"""
Products blueprint routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Product, Popup, Video, ProductPurchase
from app.utils.email import EmailService
from werkzeug.utils import secure_filename
import os
import uuid
import stripe
import json
import re
from . import bp

# Helper function for file uploads
def allowed_file(filename, allowed_extensions):
    """Check if file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Helper function to generate slugs from titles
def slugify(text):
    """
    Convert spaces to hyphens, remove special chars, and convert to lowercase
    to create a URL-friendly slug from any text.
    """
    # Replace spaces with hyphens
    text = text.replace(' ', '-')
    # Remove special characters
    text = re.sub(r'[^\w\-]', '', text)
    # Convert to lowercase
    return text.lower()

# Public-facing routes
@bp.route('/', methods=['GET'])
def index():
    """Public products page with e-commerce UI"""
    products = Product.query.all()
    return render_template('products/index.html', products=products)

@bp.route('/<int:product_id>', methods=['GET'])
def view(product_id):
    """View a specific product details"""
    # Get the product or return 404 if not found
    product = Product.query.get_or_404(product_id)
    
    # Check if user has already purchased this product
    is_purchased = False
    if current_user.is_authenticated:
        purchase = ProductPurchase.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
            status='completed'
        ).first()
        is_purchased = purchase is not None
    
    return render_template('products/view.html', 
                          product=product,
                          is_purchased=is_purchased)

@bp.route('/landing/<slug>', methods=['GET'])
def landing_page(slug):
    """Product landing/marketing page"""
    product = Product.query.filter_by(slug=slug).first_or_404()
    
    # Parse JSON fields for the landing page
    benefits = []
    if product.benefits:
        try:
            benefits = json.loads(product.benefits)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Error parsing benefits JSON: {e}")
            
    faq = []
    if product.faq:
        try:
            faq = json.loads(product.faq)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Error parsing FAQ JSON: {e}")
    
    # Process technical specs if present
    specs = []
    if product.technical_specs:
        try:
            specs = json.loads(product.technical_specs)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Error parsing technical specs JSON: {e}")
    
    # Process features if present
    features = []
    if product.features:
        try:
            features = json.loads(product.features)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Error parsing features JSON: {e}")
    
    # Process testimonials if present
    testimonials = []
    if product.testimonials:
        try:
            testimonials = json.loads(product.testimonials)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Error parsing testimonials JSON: {e}")
            
    return render_template('products/landing/index.html', 
                          product=product, 
                          benefits=benefits,
                          faq=faq,
                          features=features,
                          specs=specs,
                          testimonials=testimonials,
                          meta_title=product.meta_title,
                          meta_description=product.meta_description)

# Ensure only admin users can access admin-related routes
@bp.before_request
def check_admin_for_admin_routes():
    """Check if user is admin for routes that require admin privileges"""
    admin_endpoints = ['admin_products', 'new_product', 'edit_product', 'delete_product', 
                      'admin_popups', 'new_popup', 'edit_popup', 'delete_popup']
    
    if request.endpoint and request.endpoint.split('.')[-1] in admin_endpoints:
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this area.', 'danger')
            return redirect(url_for('main.index'))

# Admin routes for product management
@bp.route('/admin', methods=['GET'])
@login_required
def admin_products():
    """Admin view of all products"""
    products = Product.query.all()
    return render_template('products/admin/index.html', products=products)

@bp.route('/admin/new', methods=['GET', 'POST'])
@login_required
def new_product():
    """Create a new product"""
    if request.method == 'POST':
        # Basic fields
        title = request.form.get('title')
        description = request.form.get('description')
        price = float(request.form.get('price', 0))
        external_url = request.form.get('external_url')
        is_featured = 'is_featured' in request.form
        
        # Landing page fields
        slug = request.form.get('slug') or slugify(title)
        meta_title = request.form.get('meta_title')
        meta_description = request.form.get('meta_description')
        banner_text = request.form.get('banner_text')
        detailed_description = request.form.get('detailed_description')
        promo_video_url = request.form.get('promo_video_url')
        
        # Marketing fields - Check for both possible field names
        benefits = request.form.get('benefits_list') or request.form.get('benefits')
        faq = request.form.get('faq_items') or request.form.get('faq')
        testimonials = request.form.get('testimonials')
        features = request.form.get('features')
        technical_specs = request.form.get('technical_specs')
        gallery_images = request.form.get('gallery_images')
        related_products = request.form.get('related_products')
        download_link = request.form.get('download_link')
        pricing_tiers = request.form.get('pricing_tiers')
        cta_primary_text = request.form.get('cta_primary_text')
        cta_secondary_text = request.form.get('cta_secondary_text')
        seo_keywords = request.form.get('seo_keywords')
        
        # Extended marketing fields
        usp = request.form.get('usp')
        customer_avatars = request.form.get('customer_avatars')
        before_after = request.form.get('before_after')
        guarantee_text = request.form.get('guarantee_text')
        product_comparison = request.form.get('product_comparison')
        limited_offer = request.form.get('limited_offer')
        social_proof = request.form.get('social_proof')
        author_bio = request.form.get('author_bio')
        
        # Handle image upload
        image_path = None
        if 'product_image' in request.files and request.files['product_image'].filename:
            image_file = request.files['product_image']
            if image_file and allowed_file(image_file.filename, ['jpg', 'jpeg', 'png']):
                filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                # Store relative path with forward slashes for web compatibility
                image_path = 'uploads/products/' + filename
                # Full path for saving the file
                full_path = os.path.join(current_app.static_folder, 'uploads', 'products', filename)
                image_file.save(full_path)
        
        # Handle banner image upload
        banner_image = None
        if 'banner_image' in request.files and request.files['banner_image'].filename:
            banner_file = request.files['banner_image']
            if banner_file and allowed_file(banner_file.filename, ['jpg', 'jpeg', 'png']):
                filename = secure_filename(f"banner_{uuid.uuid4()}_{banner_file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                # Store relative path with forward slashes for web compatibility
                banner_image = 'uploads/products/' + filename
                # Full path for saving the file
                full_path = os.path.join(current_app.static_folder, 'uploads', 'products', filename)
                banner_file.save(full_path)
        
        product = Product(
            title=title,
            description=description,
            price=price,
            external_url=external_url,
            image_path=image_path,
            is_featured=is_featured,
            slug=slug,
            meta_title=meta_title,
            meta_description=meta_description,
            banner_text=banner_text,
            banner_image=banner_image,
            detailed_description=detailed_description,
            promo_video_url=promo_video_url,
            benefits=benefits,
            faq=faq,
            testimonials=testimonials,
            features=features,
            technical_specs=technical_specs,
            gallery_images=gallery_images,
            related_products=related_products,
            download_link=download_link,
            pricing_tiers=pricing_tiers,
            cta_primary_text=cta_primary_text,
            cta_secondary_text=cta_secondary_text,
            seo_keywords=seo_keywords,
            usp=usp,
            customer_avatars=customer_avatars,
            before_after=before_after,
            guarantee_text=guarantee_text,
            product_comparison=product_comparison,
            limited_offer=limited_offer,
            social_proof=social_proof,
            author_bio=author_bio
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product created successfully!', 'success')
        return redirect(url_for('products.admin_products'))
    
    return render_template('products/admin/form.html', product=None)

@bp.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit an existing product"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            # Basic fields
            product.title = request.form.get('title')
            product.description = request.form.get('description')
            product.price = float(request.form.get('price', 0))
            product.external_url = request.form.get('external_url')
            product.is_featured = 'is_featured' in request.form
            
            # Landing page fields
            product.slug = request.form.get('slug') or slugify(product.title)
            product.meta_title = request.form.get('meta_title')
            product.meta_description = request.form.get('meta_description')
            product.banner_text = request.form.get('banner_text')
            product.detailed_description = request.form.get('detailed_description')
            product.promo_video_url = request.form.get('promo_video_url')
            
            # Marketing fields - Check for both possible field names/formats
            product.benefits = request.form.get('benefits')
            product.faq = request.form.get('faq')
            product.testimonials = request.form.get('testimonials')
            product.features = request.form.get('features')
            product.technical_specs = request.form.get('technical_specs')
            product.gallery_images = request.form.get('gallery_images')
            product.related_products = request.form.get('related_products')
            product.download_link = request.form.get('download_link')
            product.pricing_tiers = request.form.get('pricing_tiers')
            product.cta_primary_text = request.form.get('cta_primary_text')
            product.cta_secondary_text = request.form.get('cta_secondary_text')
            product.seo_keywords = request.form.get('seo_keywords')
            
            # Extended marketing fields
            product.usp = request.form.get('usp')
            product.customer_avatars = request.form.get('customer_avatars')
            product.before_after = request.form.get('before_after')
            product.guarantee_text = request.form.get('guarantee_text')
            product.product_comparison = request.form.get('product_comparison')
            product.limited_offer = request.form.get('limited_offer')
            product.social_proof = request.form.get('social_proof')
            product.author_bio = request.form.get('author_bio')
            
            # Handle product image upload
            if 'product_image' in request.files and request.files['product_image'].filename:
                image_file = request.files['product_image']
                if image_file and allowed_file(image_file.filename, ['jpg', 'jpeg', 'png']):
                    filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
                    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    # Store relative path with forward slashes for web compatibility
                    product.image_path = 'uploads/products/' + filename
                    # Full path for saving the file
                    full_path = os.path.join(current_app.static_folder, 'uploads', 'products', filename)
                    image_file.save(full_path)
                    current_app.logger.debug(f"Saved product image to {full_path}")
            
            # Handle banner image upload
            if 'banner_image' in request.files and request.files['banner_image'].filename:
                banner_file = request.files['banner_image']
                if banner_file and allowed_file(banner_file.filename, ['jpg', 'jpeg', 'png']):
                    filename = secure_filename(f"banner_{uuid.uuid4()}_{banner_file.filename}")
                    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products')
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    # Store relative path with forward slashes for web compatibility
                    product.banner_image = 'uploads/products/' + filename
                    # Full path for saving the file
                    full_path = os.path.join(current_app.static_folder, 'uploads', 'products', filename)
                    banner_file.save(full_path)
                    current_app.logger.debug(f"Saved banner image to {full_path}")
            
            # Debug logging before commit
            current_app.logger.info(f"About to save product {product_id} with title {product.title}")
            
            # Commit changes to database
            db.session.commit()
            
            # Verify changes were saved
            db.session.refresh(product)
            current_app.logger.info(f"Product {product_id} updated successfully - title: {product.title}")
            
            flash('Product updated successfully!', 'success')
            return redirect(url_for('products.admin_products'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving product: {str(e)}")
            current_app.logger.exception(e)  # Log the full exception with traceback
            flash(f'Error saving product: {str(e)}', 'danger')
            return render_template('products/admin/form.html', product=product)
    
    # GET request - show the edit form
    current_app.logger.info(f"Showing edit form for product {product_id}")
    return render_template('products/admin/form.html', product=product)

@bp.route('/admin/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete a product"""
    product = Product.query.get_or_404(product_id)
    
    # Delete the product image if it exists
    if product.image_path:
        try:
            image_path = os.path.join(current_app.static_folder, product.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting product image: {str(e)}")
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products.admin_products'))

# Admin routes for popup management
@bp.route('/admin/popups', methods=['GET'])
@login_required
def admin_popups():
    """Admin view of all popups"""
    popups = Popup.query.all()
    return render_template('products/admin/popups/index.html', popups=popups)

@bp.route('/admin/popups/new', methods=['GET', 'POST'])
@login_required
def new_popup():
    """Create a new popup"""
    products = Product.query.all()
    
    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        popup_text = request.form.get('popup_text')
        popup_button_label = request.form.get('popup_button_label') or "Learn More"
        popup_trigger_seconds = int(request.form.get('popup_trigger_seconds', 0))
        
        # Handle popup image upload
        popup_image_path = None
        if 'popup_image' in request.files and request.files['popup_image'].filename:
            image_file = request.files['popup_image']
            if image_file and allowed_file(image_file.filename, ['jpg', 'jpeg', 'png']):
                filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'popups')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                # Store relative path with forward slashes for web compatibility
                popup_image_path = 'uploads/popups/' + filename
                # Full path for saving the file
                full_path = os.path.join(current_app.static_folder, 'uploads', 'popups', filename)
                image_file.save(full_path)
        
        popup = Popup(
            product_id=product_id,
            popup_text=popup_text,
            popup_image=popup_image_path,
            popup_button_label=popup_button_label,
            popup_trigger_seconds=popup_trigger_seconds
        )
        
        db.session.add(popup)
        db.session.commit()
        
        flash('Popup created successfully!', 'success')
        return redirect(url_for('products.admin_popups'))
    
    return render_template('products/admin/popups/form.html', popup=None, products=products)

@bp.route('/admin/popups/<int:popup_id>', methods=['GET', 'POST'])
@login_required
def edit_popup(popup_id):
    """Edit an existing popup"""
    popup = Popup.query.get_or_404(popup_id)
    products = Product.query.all()
    
    if request.method == 'POST':
        popup.product_id = request.form.get('product_id', type=int)
        popup.popup_text = request.form.get('popup_text')
        popup.popup_button_label = request.form.get('popup_button_label') or "Learn More"
        popup.popup_trigger_seconds = int(request.form.get('popup_trigger_seconds', 0))
        
        # Handle popup image upload
        if 'popup_image' in request.files and request.files['popup_image'].filename:
            image_file = request.files['popup_image']
            if image_file and allowed_file(image_file.filename, ['jpg', 'jpeg', 'png']):
                # Delete old image if it exists
                if popup.popup_image:
                    try:
                        old_image_path = os.path.join(current_app.static_folder, popup.popup_image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        current_app.logger.error(f"Error deleting old popup image: {str(e)}")
                
                # Save new image
                filename = secure_filename(f"{uuid.uuid4()}_{image_file.filename}")
                upload_folder = os.path.join(current_app.static_folder, 'uploads', 'popups')
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                # Store relative path with forward slashes for web compatibility
                popup.popup_image = 'uploads/popups/' + filename
                # Full path for saving the file
                full_path = os.path.join(current_app.static_folder, 'uploads', 'popups', filename)
                image_file.save(full_path)
        
        db.session.commit()
        flash('Popup updated successfully!', 'success')
        return redirect(url_for('products.admin_popups'))
    
    return render_template('products/admin/popups/form.html', popup=popup, products=products)

@bp.route('/admin/popups/<int:popup_id>/delete', methods=['POST'])
@login_required
def delete_popup(popup_id):
    """Delete a popup"""
    popup = Popup.query.get_or_404(popup_id)
    
    # Delete the popup image if it exists
    if popup.popup_image:
        try:
            image_path = os.path.join(current_app.static_folder, popup.popup_image)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting popup image: {str(e)}")
    
    db.session.delete(popup)
    db.session.commit()
    
    flash('Popup deleted successfully!', 'success')
    return redirect(url_for('products.admin_popups'))

# Routes for associating popups with videos
@bp.route('/admin/videos', methods=['GET'])
@login_required
def admin_videos_with_popups():
    """Admin view of videos with popup associations"""
    videos = Video.query.all()
    popups = Popup.query.all()
    return render_template('products/admin/videos/index.html', videos=videos, popups=popups)

@bp.route('/admin/videos/<int:video_id>/popup', methods=['POST'])
@login_required
def set_video_popup(video_id):
    """Associate a popup with a video or remove association"""
    video = Video.query.get_or_404(video_id)
    popup_id = request.form.get('popup_id', type=int)
    
    # If popup_id is 0 or None, remove popup association
    if not popup_id:
        video.popup_id = None
        db.session.commit()
        flash('Popup removed from video successfully!', 'success')
    else:
        # Verify popup exists
        popup = Popup.query.get_or_404(popup_id)
        video.popup_id = popup_id
        db.session.commit()
        flash('Popup associated with video successfully!', 'success')
    
    return redirect(url_for('products.admin_videos_with_popups'))

# API endpoint to get popup info for video
@bp.route('/api/video/<int:video_id>/popup', methods=['GET'])
@login_required
def get_video_popup(video_id):
    """Get popup info for a video if associated"""
    video = Video.query.get_or_404(video_id)
    
    if not video.popup_id:
        return jsonify({"has_popup": False})
    
    popup = Popup.query.get(video.popup_id)
    if not popup:
        return jsonify({"has_popup": False})
    
    product = Product.query.get(popup.product_id)
    if not product:
        return jsonify({"has_popup": False})
    
    # Ensure popup_trigger_seconds is greater than zero to prevent immediate popups
    if not popup.popup_trigger_seconds or popup.popup_trigger_seconds <= 0:
        current_app.logger.warning(f"Popup {popup.id} has invalid trigger time: {popup.popup_trigger_seconds}")
        # Set a default of 45 seconds if not properly configured
        popup_trigger_seconds = 45
    else:
        popup_trigger_seconds = popup.popup_trigger_seconds
    
    # Log the popup timing for debugging
    current_app.logger.info(f"Video {video_id} popup will trigger at {popup_trigger_seconds} seconds")
    
    popup_data = {
        "has_popup": True,
        "popup_id": popup.id,
        "popup_trigger_seconds": popup_trigger_seconds,
        "popup_text": popup.popup_text,
        "popup_button_label": popup.popup_button_label,
        "popup_image": popup.popup_image,
        "product": {
            "id": product.id,
            "title": product.title,
            "price": float(product.price),
            "is_free": product.price == 0,  # Determine if free based on price
            "has_external_url": bool(product.external_url),  # Check if external URL exists
            "external_url": product.external_url
        }
    }
    
    return jsonify(popup_data)

# Stripe checkout integration
@bp.route('/checkout/<int:product_id>', methods=['GET'])
@login_required
def checkout(product_id):
    """Create a Stripe checkout session for a product"""
    product = Product.query.get_or_404(product_id)
    
    # If product is free or has external URL, redirect directly
    if product.is_free and product.has_external_url:
        return redirect(product.external_url)
    
    # Configure Stripe API key - Use app config directly like in courses
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    
    # Create Stripe Checkout Session
    try:
        # Prepare product image URL - ensure forward slashes for URLs
        image_url = None
        if product.image_path:
            # Replace backslashes with forward slashes & ensure proper URL formatting
            normalized_path = product.image_path.replace('\\', '/')
            image_url = f"{request.url_root.rstrip('/')}/static/{normalized_path}"
        
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': product.title,
                            'description': product.description[:255] if product.description else None,
                            'images': [image_url] if image_url else None
                        },
                        'unit_amount': int(product.price * 100),  # Price in cents
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            success_url=request.url_root.rstrip('/') + url_for('products.checkout_success', product_id=product.id),
            cancel_url=request.url_root.rstrip('/') + url_for('products.checkout_cancel'),
            metadata={
                'product_id': product.id,
                'user_id': current_user.id
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        current_app.logger.error(f"Stripe checkout error: {str(e)}")
        flash("An error occurred while processing your payment. Please try again.", "danger")
        return redirect(url_for('main.index'))

@bp.route('/checkout/success/<int:product_id>', methods=['GET'])
@login_required
def checkout_success(product_id):
    """Handle successful Stripe checkout"""
    product = Product.query.get_or_404(product_id)
    
    # Record the product purchase in the database
    from app.models import ProductPurchase
    
    # Check if the user has already purchased this product
    existing_purchase = ProductPurchase.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if not existing_purchase:
        # Create a new purchase record
        purchase = ProductPurchase(
            user_id=current_user.id,
            product_id=product_id,
            amount=product.price,
            status='completed'
        )
        
        # If this is coming from a Stripe checkout, we'll set the payment ID later
        # via the webhook, but for now we just create the purchase record
        
        db.session.add(purchase)
        db.session.commit()
    
    flash(f"Thank you for your purchase of {product.title}!", "success")
    return redirect(url_for('main.dashboard'))

@bp.route('/checkout/cancel', methods=['GET'])
@login_required
def checkout_cancel():
    """Handle canceled Stripe checkout"""
    flash("Your purchase was canceled. Feel free to continue browsing our courses.", "info")
    return redirect(url_for('courses.index'))