import stripe
from flask import current_app, redirect, render_template, request, url_for, flash, session
from flask_login import current_user, login_required
from app.models import Course, UserCourse
from app import db
from app.blueprints.payments import bp
from datetime import datetime
import os

@bp.route('/checkout/<int:course_id>', methods=['GET'])
@login_required
def checkout(course_id):
    """
    Create a Stripe checkout session for a specific course
    """
    # Get the course
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing_enrollment = UserCourse.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('courses.view', course_id=course_id))
    
    # Configure Stripe API key
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    
    # Create a new checkout session
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': course.title,
                            'description': course.description[:255] if course.description else None,
                            'images': [request.url_root.rstrip('/') + course.image_url] if course.image_url else None,
                        },
                        'unit_amount': int(course.price * 100),  # Convert to cents
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=request.url_root.rstrip('/') + url_for('payments.success', course_id=course_id),
            cancel_url=request.url_root.rstrip('/') + url_for('courses.view', course_id=course_id),
            client_reference_id=str(course_id),  # Store course ID for reference
            customer_email=current_user.email,
            metadata={
                'user_id': current_user.id,
                'course_id': course_id
            }
        )
        
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        current_app.logger.error(f"Error creating Stripe session: {str(e)}")
        flash('An error occurred while processing your payment. Please try again later.', 'danger')
        return redirect(url_for('courses.view', course_id=course_id))

@bp.route('/success/<int:course_id>')
@login_required
def success(course_id):
    """
    Handle successful payment and course enrollment
    """
    course = Course.query.get_or_404(course_id)
    
    # Check if already enrolled
    existing_enrollment = UserCourse.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if not existing_enrollment:
        # Create enrollment record
        enrollment = UserCourse(
            user_id=current_user.id,
            course_id=course_id,
            enrollment_date=datetime.utcnow(),
            completed=False
        )
        
        db.session.add(enrollment)
        db.session.commit()
        
    flash(f'Thank you for your payment! You are now enrolled in {course.title}.', 'success')
    return redirect(url_for('courses.view', course_id=course_id))

@bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle Stripe webhooks for payment confirmation
    """
    import json  # Adding json import at the top of the function
    
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # For testing without webhook signing
            data = json.loads(payload)
            event = stripe.Event.construct_from(data, stripe.api_key)
            
        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Get metadata
            metadata = session.get('metadata', {})
            user_id = int(metadata.get('user_id', 0))
            course_id = int(metadata.get('course_id', 0))
            
            if user_id and course_id:
                # Check if already enrolled
                existing_enrollment = UserCourse.query.filter_by(
                    user_id=user_id,
                    course_id=course_id
                ).first()
                
                if not existing_enrollment:
                    # Create enrollment record
                    enrollment = UserCourse(
                        user_id=user_id,
                        course_id=course_id,
                        enrollment_date=datetime.utcnow(),
                        completed=False
                    )
                    
                    db.session.add(enrollment)
                    db.session.commit()
                    
            return {'success': True}, 200
            
    except Exception as e:
        current_app.logger.error(f"Webhook error: {str(e)}")
        return {'error': str(e)}, 400
    
    return {'success': True}, 200