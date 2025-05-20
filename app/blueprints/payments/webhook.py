"""
Stripe webhook handler for processing payments
"""
import stripe
from flask import Blueprint, request, current_app, jsonify
from app import db
from app.models import Payment, UserCourse, Course, ProductPurchase, Product, PlatformConfig

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    # Get the webhook payload
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    # Get Stripe webhook secret from config
    config = PlatformConfig.query.first()
    endpoint_secret = config.stripe_webhook_secret if config else None
    
    try:
        if not endpoint_secret:
            # Use more permissive event parsing if no webhook secret is set
            event = stripe.Event.construct_from(
                request.get_json(), stripe.api_key
            )
        else:
            # Verify the signature with the webhook secret
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
    except ValueError as e:
        # Invalid payload
        current_app.logger.error(f"Invalid Stripe payload: {str(e)}")
        return jsonify(success=False, error="Invalid payload"), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        current_app.logger.error(f"Invalid Stripe signature: {str(e)}")
        return jsonify(success=False, error="Invalid signature"), 400
    
    # Handle the event
    if event.type == 'checkout.session.completed':
        # Get the session data
        session = event.data.object
        
        # Check if it's a course or product purchase
        metadata = session.get('metadata', {})
        course_id = metadata.get('course_id')
        product_id = metadata.get('product_id')
        user_id = metadata.get('user_id')
        
        if not user_id:
            current_app.logger.error("Missing user_id in Stripe metadata")
            return jsonify(success=False, error="Missing user_id"), 400
        
        # Process course purchase
        if course_id:
            try:
                course_id = int(course_id)
                user_id = int(user_id)
                
                # Create payment record
                payment = Payment(
                    user_id=user_id,
                    course_id=course_id,
                    stripe_payment_id=session.id,
                    amount=session.amount_total / 100,  # Convert cents to dollars
                    status='completed'
                )
                db.session.add(payment)
                
                # Enroll user in course if not already enrolled
                existing_enrollment = UserCourse.query.filter_by(
                    user_id=user_id,
                    course_id=course_id
                ).first()
                
                if not existing_enrollment:
                    enrollment = UserCourse(
                        user_id=user_id,
                        course_id=course_id
                    )
                    db.session.add(enrollment)
                
                db.session.commit()
                current_app.logger.info(f"Course purchase processed: User {user_id}, Course {course_id}")
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error processing course payment: {str(e)}")
                return jsonify(success=False, error="Error processing payment"), 500
        
        # Process product purchase
        elif product_id:
            try:
                product_id = int(product_id)
                user_id = int(user_id)
                
                # Find any existing purchase
                existing_purchase = ProductPurchase.query.filter_by(
                    user_id=user_id,
                    product_id=product_id
                ).first()
                
                if existing_purchase:
                    # Update existing purchase with Stripe payment ID
                    existing_purchase.stripe_payment_id = session.id
                    existing_purchase.amount = session.amount_total / 100
                    existing_purchase.status = 'completed'
                else:
                    # Create new purchase record
                    purchase = ProductPurchase(
                        user_id=user_id,
                        product_id=product_id,
                        stripe_payment_id=session.id,
                        amount=session.amount_total / 100,  # Convert cents to dollars
                        status='completed'
                    )
                    db.session.add(purchase)
                
                db.session.commit()
                current_app.logger.info(f"Product purchase processed: User {user_id}, Product {product_id}")
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error processing product payment: {str(e)}")
                return jsonify(success=False, error="Error processing payment"), 500
        
        else:
            current_app.logger.warning("Unknown Stripe purchase type, missing course_id or product_id")
    
    # Return a 200 response to acknowledge receipt of the event
    return jsonify(success=True)