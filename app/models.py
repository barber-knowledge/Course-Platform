"""
SQLAlchemy ORM models for the Modular Course Platform
"""
from datetime import datetime, timedelta, timezone
import secrets
from flask_login import UserMixin
# Commenting out the import of hashing functions for development
# from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from slugify import slugify

# Helper function for SQLAlchemy model defaults to replace utcnow
def get_utc_now():
    """Return current UTC datetime - replacement for datetime.utcnow"""
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    reset_password_token = db.Column(db.String(100), nullable=True)
    reset_token_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    last_login = db.Column(db.DateTime)
    bio = db.Column(db.Text, nullable=True)
    
    # Relationships
    enrolled_courses = db.relationship('UserCourse', back_populates='user', lazy='dynamic')
    quiz_attempts = db.relationship('QuizAttempt', back_populates='user', lazy='dynamic')
    video_progress = db.relationship('VideoProgress', back_populates='user', lazy='dynamic')
    certificates = db.relationship('Certificate', back_populates='user', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='user', lazy='dynamic')
    
    def set_password(self, password):
        # No hashing for development - store plain text password
        self.password_hash = password
        
    def check_password(self, password):
        # Simple plain text comparison for development
        return self.password_hash == password
    
    def generate_reset_token(self):
        """Generate a password reset token that expires in 24 hours"""
        token = secrets.token_urlsafe(32)
        self.reset_password_token = token
        self.reset_token_expires_at = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        return token
    
    def verify_reset_token(self, token):
        """Verify if the reset token is valid and not expired"""
        if self.reset_password_token != token:
            return False
        
        if self.reset_token_expires_at < datetime.utcnow():
            return False
            
        return True
    
    def clear_reset_token(self):
        """Clear reset token after use"""
        self.reset_password_token = None
        self.reset_token_expires_at = None
        db.session.commit()
    
    @staticmethod
    def get_user_by_reset_token(token):
        """Get user by reset token"""
        if not token:
            return None
        return User.query.filter_by(reset_password_token=token).first()
    
    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Course(db.Model):
    """Course model for course management"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    is_active = db.Column(db.Boolean, default=True, index=True)
    has_certificate = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(255), nullable=True)
    certificate_template_id = db.Column(db.Integer, db.ForeignKey('certificate_templates.id'), nullable=True)
    
    # Landing page fields
    slug = db.Column(db.String(255), unique=True, index=True)
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    benefits = db.Column(db.Text)  # JSON-formatted list of benefits
    faq = db.Column(db.Text)  # JSON-formatted FAQs
    banner_text = db.Column(db.Text)
    banner_image = db.Column(db.String(255))
    detailed_description = db.Column(db.Text)
    promo_video_url = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    videos = db.relationship('Video', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    quiz = db.relationship('Quiz', back_populates='course', uselist=False, cascade='all, delete-orphan')
    enrollments = db.relationship('UserCourse', back_populates='course', lazy='dynamic')
    certificates = db.relationship('Certificate', back_populates='course', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='course', lazy='dynamic')
    pdfs = db.relationship('CoursePDF', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.title}>'
        
    def generate_slug(self):
        """Generate a slug from the title"""
        if not self.slug:
            self.slug = slugify(self.title)
            
    @property
    def is_free(self):
        """Check if the course is free"""
        return float(self.price) == 0.0

class Video(db.Model):
    """Video model for course videos"""
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    # Store the relative path within static/uploads/videos
    video_path = db.Column(db.String(255), nullable=False) 
    sequence_order = db.Column(db.Integer, nullable=False)
    duration_seconds = db.Column(db.Integer, default=0) # Changed from duration
    is_free = db.Column(db.Boolean, default=False) # Added is_free field
    popup_id = db.Column(db.Integer, db.ForeignKey('popups.id'), nullable=True) # Added popup relationship
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    course = db.relationship('Course', back_populates='videos')
    progress_records = db.relationship('VideoProgress', back_populates='video', lazy='dynamic', cascade='all, delete-orphan')
    popup = db.relationship('Popup', back_populates='videos')
    
    __table_args__ = (
        db.UniqueConstraint('course_id', 'sequence_order', name='_course_sequence_uc'),
    )
    
    def __repr__(self):
        return f'<Video {self.title} ({self.course_id})>'

class Quiz(db.Model):
    """Quiz model for course quizzes"""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    passing_percentage = db.Column(db.Integer, default=70)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    course = db.relationship('Course', back_populates='quiz')
    questions = db.relationship('QuizQuestion', back_populates='quiz', lazy='dynamic', cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', back_populates='quiz', lazy='dynamic')
    
    def __repr__(self):
        return f'<Quiz {self.title} ({self.course_id})>'

class QuizQuestion(db.Model):
    """Quiz Question model"""
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='multiple_choice')
    points = db.Column(db.Integer, default=1)
    sequence_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    quiz = db.relationship('Quiz', back_populates='questions')
    answers = db.relationship('QuizAnswer', back_populates='question', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('quiz_id', 'sequence_order', name='_quiz_sequence_uc'),
    )
    
    def __repr__(self):
        return f'<QuizQuestion {self.id} ({self.quiz_id})>'

class QuizAnswer(db.Model):
    """Quiz Answer model for multiple choice and single choice questions"""
    __tablename__ = 'quiz_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_questions.id', ondelete='CASCADE'), nullable=False, index=True)
    answer_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    question = db.relationship('QuizQuestion', back_populates='answers')
    
    def __repr__(self):
        return f'<QuizAnswer {self.id} ({self.question_id})>'

class QuizAttempt(db.Model):
    """Quiz Attempt model to track student quiz submissions"""
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    passed = db.Column(db.Boolean, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    user = db.relationship('User', back_populates='quiz_attempts')
    quiz = db.relationship('Quiz', back_populates='attempts')
    
    def __repr__(self):
        return f'<QuizAttempt {self.id} - User: {self.user_id}, Quiz: {self.quiz_id}>'

class Certificate(db.Model):
    """Certificate model for course completion certificates"""
    __tablename__ = 'certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    certificate_id = db.Column(db.String(50), nullable=False, unique=True, index=True)
    file_path = db.Column(db.String(255), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    user = db.relationship('User', back_populates='certificates')
    course = db.relationship('Course', back_populates='certificates')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='_user_course_cert_uc'),
    )
    
    def __repr__(self):
        return f'<Certificate {self.certificate_id} - User: {self.user_id}, Course: {self.course_id}>'

class Payment(db.Model):
    """Payment model for course payments"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    stripe_payment_id = db.Column(db.String(100), nullable=False, unique=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False, index=True)
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    user = db.relationship('User', back_populates='payments')
    course = db.relationship('Course', back_populates='payments')
    
    def __repr__(self):
        return f'<Payment {self.id} - {self.stripe_payment_id}>'

class UserCourse(db.Model):
    """Many-to-many relationship between users and courses"""
    __tablename__ = 'user_courses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    enrollment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    user = db.relationship('User', back_populates='enrolled_courses')
    course = db.relationship('Course', back_populates='enrollments')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='_user_course_uc'),
    )
    
    def __repr__(self):
        return f'<UserCourse - User: {self.user_id}, Course: {self.course_id}>'

class VideoProgress(db.Model):
    """Tracks user progress in watching videos"""
    __tablename__ = 'video_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False, index=True)
    seconds_watched = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    last_watched_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    user = db.relationship('User', back_populates='video_progress')
    video = db.relationship('Video', back_populates='progress_records')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'video_id', name='_user_video_uc'),
    )
    
    def __repr__(self):
        return f'<VideoProgress - User: {self.user_id}, Video: {self.video_id}>'

class CoursePDF(db.Model):
    """PDF document model for course materials"""
    __tablename__ = 'course_pdfs'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    pdf_path = db.Column(db.String(255), nullable=False)
    sequence_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    course = db.relationship('Course', back_populates='pdfs')
    
    __table_args__ = (
        db.UniqueConstraint('course_id', 'sequence_order', name='_course_pdf_sequence_uc'),
    )
    
    def __repr__(self):
        return f'<CoursePDF {self.title} ({self.course_id})>'

class PlatformConfig(db.Model):
    """Platform configuration settings"""
    __tablename__ = 'platform_config'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_name = db.Column(db.String(255), default="Modular Course Platform")
    primary_color = db.Column(db.String(20), default="#4a6cf7")
    secondary_color = db.Column(db.String(20), default="#6c757d")
    logo_path = db.Column(db.String(255), nullable=True)
    welcome_message = db.Column(db.Text, nullable=True)
    setup_complete = db.Column(db.Boolean, default=False)
    stripe_secret_key = db.Column(db.String(255), nullable=True)
    stripe_publishable_key = db.Column(db.String(255), nullable=True)
    stripe_enabled = db.Column(db.Boolean, default=False)
    
    # Email configuration settings
    smtp_server = db.Column(db.String(255), nullable=True)
    smtp_port = db.Column(db.Integer, nullable=True)
    smtp_username = db.Column(db.String(255), nullable=True)
    smtp_password = db.Column(db.String(255), nullable=True)
    smtp_use_tls = db.Column(db.Boolean, default=True)
    smtp_use_ssl = db.Column(db.Boolean, default=False)
    smtp_default_sender = db.Column(db.String(255), nullable=True)
    smtp_enabled = db.Column(db.Boolean, default=False)
    
    # RabbitMQ configuration settings
    rabbitmq_host = db.Column(db.String(255), default='localhost')
    rabbitmq_port = db.Column(db.Integer, default=5672)
    rabbitmq_username = db.Column(db.String(255), default='guest')
    rabbitmq_password = db.Column(db.String(255), default='guest')
    rabbitmq_vhost = db.Column(db.String(255), default='/')
    rabbitmq_enabled = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    def __repr__(self):
        return f'<PlatformConfig {self.platform_name}>'
    
    @classmethod
    def get_config(cls):
        """Get the current platform configuration or create default if not exists"""
        config = cls.query.first()
        if not config:
            config = cls()
            db.session.add(config)
            db.session.commit()
        return config

class Product(db.Model):
    """Product model for products to be sold or promoted"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    image_path = db.Column(db.String(255))
    external_url = db.Column(db.String(255))
    
    # Landing page fields
    slug = db.Column(db.String(255), unique=True, index=True)
    meta_title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    benefits = db.Column(db.Text)  # JSON-formatted list of benefits
    faq = db.Column(db.Text)  # JSON-formatted FAQs
    banner_text = db.Column(db.Text)
    banner_image = db.Column(db.String(255))
    detailed_description = db.Column(db.Text)
    promo_video_url = db.Column(db.String(255))
    
    # Additional marketing fields
    testimonials = db.Column(db.Text)  # JSON-formatted testimonials
    features = db.Column(db.Text)  # JSON-formatted features list
    technical_specs = db.Column(db.Text)  # JSON-formatted technical specifications
    is_featured = db.Column(db.Boolean, default=False)
    gallery_images = db.Column(db.Text)  # JSON-formatted list of image paths
    related_products = db.Column(db.Text)  # JSON-formatted list of related product IDs
    download_link = db.Column(db.Text)  # For digital products
    pricing_tiers = db.Column(db.Text)  # JSON-formatted pricing options
    cta_primary_text = db.Column(db.String(100), default="Buy Now")
    cta_secondary_text = db.Column(db.String(100), default="Learn More")
    seo_keywords = db.Column(db.Text)  # Comma-separated SEO keywords
    
    # Extended marketing fields
    usp = db.Column(db.Text)  # Unique Selling Proposition
    customer_avatars = db.Column(db.Text)  # JSON-formatted target customer profiles
    before_after = db.Column(db.Text)  # JSON-formatted customer transformation stories
    guarantee_text = db.Column(db.Text)  # Product guarantee or warranty information
    product_comparison = db.Column(db.Text)  # JSON-formatted comparison with other products
    limited_offer = db.Column(db.Text)  # JSON-formatted limited time offer details
    social_proof = db.Column(db.Text)  # JSON-formatted social proof metrics and testimonials
    author_bio = db.Column(db.Text)  # Product creator or author biography
    
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    popups = db.relationship('Popup', back_populates='product', lazy='dynamic', cascade='all, delete-orphan')
    
    def generate_slug(self):
        """Generate a slug from the title"""
        if not self.slug:
            self.slug = slugify(self.title)
    
    @property
    def is_free(self):
        """Check if the product is free"""
        return float(self.price) == 0.0
    
    @property
    def has_external_url(self):
        """Check if the product has an external URL"""
        return bool(self.external_url)
    
    def __repr__(self):
        return f'<Product {self.title}>'

class Popup(db.Model):
    """Popup model for in-video product promotions"""
    __tablename__ = 'popups'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    popup_image = db.Column(db.String(255))
    popup_text = db.Column(db.Text)
    popup_button_label = db.Column(db.String(100), default="Learn More")
    popup_trigger_seconds = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    product = db.relationship('Product', back_populates='popups')
    videos = db.relationship('Video', back_populates='popup', lazy='dynamic')
    
    def __repr__(self):
        return f'<Popup for Product {self.product_id}>'

class ProductPurchase(db.Model):
    """Tracks product purchases by users"""
    __tablename__ = 'product_purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    stripe_payment_id = db.Column(db.String(100), nullable=True, unique=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='completed', index=True)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('product_purchases', lazy='dynamic'))
    product = db.relationship('Product', backref=db.backref('purchases', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='_user_product_purchase_uc'),
    )
    
    def __repr__(self):
        return f'<ProductPurchase - User: {self.user_id}, Product: {self.product_id}>'

class EmailTemplate(db.Model):
    """Email template model for system emails"""
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    body_text = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    template_key = db.Column(db.String(100), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'
    
    @classmethod
    def get_template(cls, template_key):
        """Get an email template by its key"""
        return cls.query.filter_by(template_key=template_key, is_active=True).first()
    
    @classmethod
    def init_default_templates(cls):
        """Initialize default email templates if they don't exist"""
        default_templates = [
            {
                'name': 'User Registration Welcome',
                'subject': 'Welcome to {{ config.platform_name }}',
                'body_html': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Welcome to {{ config.platform_name }}, {{ user.name }}!</h1>
                    <p>Thank you for registering with us. We're excited to have you on board.</p>
                    <p>Your account has been created and you can now access all our features.</p>
                    <p><a href="{{ login_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Login to your account</a></p>
                    <p>If you have any questions, please don't hesitate to contact us.</p>
                    <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                </div>
                ''',
                'body_text': '''
                Welcome to {{ config.platform_name }}, {{ user.name }}!
                
                Thank you for registering with us. We're excited to have you on board.
                Your account has been created and you can now access all our features.
                
                You can login to your account here: {{ login_url }}
                
                If you have any questions, please don't hesitate to contact us.
                
                Best regards,
                The {{ config.platform_name }} Team
                ''',
                'description': 'Email sent to users when they register for an account',
                'template_key': 'user_registration'
            },
            {
                'name': 'Course Enrollment Confirmation',
                'subject': 'You are now enrolled in {{ course.title }}',
                'body_html': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>You're now enrolled in {{ course.title }}!</h1>
                    <p>Hello {{ user.name }},</p>
                    <p>We're excited to confirm your enrollment in <strong>{{ course.title }}</strong>.</p>
                    {% if course.is_free %}
                    <p>This is a free course, and you have full access to all materials.</p>
                    {% else %}
                    <p>Your payment of ${{ course.price }} has been successfully processed.</p>
                    {% endif %}
                    <p><a href="{{ course_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Start Learning Now</a></p>
                    <p>We hope you enjoy the course and learn a lot!</p>
                    <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                </div>
                ''',
                'body_text': '''
                You're now enrolled in {{ course.title }}!
                
                Hello {{ user.name }},
                
                We're excited to confirm your enrollment in {{ course.title }}.
                
                {% if course.is_free %}
                This is a free course, and you have full access to all materials.
                {% else %}
                Your payment of ${{ course.price }} has been successfully processed.
                {% endif %}
                
                You can start learning now at: {{ course_url }}
                
                We hope you enjoy the course and learn a lot!
                
                Best regards,
                The {{ config.platform_name }} Team
                ''',
                'description': 'Email sent to users when they enroll in a course',
                'template_key': 'course_enrollment'
            },
            {
                'name': 'Course Completion Congratulations',
                'subject': 'Congratulations on completing {{ course.title }}!',
                'body_html': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Congratulations, {{ user.name }}!</h1>
                    <p>You have successfully completed <strong>{{ course.title }}</strong>. This is a significant achievement that demonstrates your dedication to learning.</p>
                    {% if course.has_certificate %}
                    <p>Your certificate of completion is ready to download.</p>
                    <p><a href="{{ certificate_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Your Certificate</a></p>
                    {% endif %}
                    <p>We hope you found the course valuable and enriching. Keep up the great work!</p>
                    <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                </div>
                ''',
                'body_text': '''
                Congratulations, {{ user.name }}!
                
                You have successfully completed {{ course.title }}. This is a significant achievement that demonstrates your dedication to learning.
                
                {% if course.has_certificate %}
                Your certificate of completion is ready to download.
                
                Download your certificate here: {{ certificate_url }}
                {% endif %}
                
                We hope you found the course valuable and enriching. Keep up the great work!
                
                Best regards,
                The {{ config.platform_name }} Team
                ''',
                'description': 'Email sent to users when they complete a course',
                'template_key': 'course_completion'
            },
            {
                'name': 'Product Purchase Confirmation',
                'subject': 'Your purchase of {{ product.title }} - Order Confirmation',
                'body_html': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Thank you for your purchase!</h1>
                    <p>Hello {{ user.name }},</p>
                    <p>Your purchase of <strong>{{ product.title }}</strong> has been successfully processed.</p>
                    <div style="border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0;">Order Details</h3>
                        <p><strong>Product:</strong> {{ product.title }}</p>
                        <p><strong>Price:</strong> ${{ product.price }}</p>
                        <p><strong>Order Date:</strong> {{ purchase.purchase_date|date }}</p>
                        <p><strong>Order ID:</strong> {{ purchase.id }}</p>
                    </div>
                    {% if product.download_link %}
                    <p>You can download your purchase using the link below:</p>
                    <p><a href="{{ download_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Your Product</a></p>
                    {% endif %}
                    {% if product.external_url %}
                    <p>You can access your product here:</p>
                    <p><a href="{{ product.external_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Access Your Product</a></p>
                    {% endif %}
                    <p>If you have any questions or need assistance, please don't hesitate to contact us.</p>
                    <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                </div>
                ''',
                'body_text': '''
                Thank you for your purchase!
                
                Hello {{ user.name }},
                
                Your purchase of {{ product.title }} has been successfully processed.
                
                Order Details:
                Product: {{ product.title }}
                Price: ${{ product.price }}
                Order Date: {{ purchase.purchase_date|date }}
                Order ID: {{ purchase.id }}
                
                {% if product.download_link %}
                You can download your purchase using this link: {{ download_url }}
                {% endif %}
                
                {% if product.external_url %}
                You can access your product here: {{ product.external_url }}
                {% endif %}
                
                If you have any questions or need assistance, please don't hesitate to contact us.
                
                Best regards,
                The {{ config.platform_name }} Team
                ''',
                'description': 'Email sent to users when they purchase a product',
                'template_key': 'product_purchase'
            },
            {
                'name': 'Quiz Completion Results',
                'subject': 'Your quiz results for {{ quiz.title }}',
                'body_html': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Your Quiz Results</h1>
                    <p>Hello {{ user.name }},</p>
                    <p>You have completed the quiz for <strong>{{ quiz.title }}</strong>.</p>
                    <div style="border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; text-align: center;">
                        <h2 style="margin-top: 0;">Your Score: {{ quiz_attempt.score }}%</h2>
                        <p style="font-size: 18px; margin-bottom: 0;">
                            {% if quiz_attempt.passed %}
                            <span style="color: green;">✓ Passed</span>
                            {% else %}
                            <span style="color: red;">✗ Not Passed</span>
                            {% endif %}
                        </p>
                    </div>
                    <p>
                        {% if quiz_attempt.passed %}
                        Congratulations on passing the quiz! You can now continue with the rest of the course.
                        {% else %}
                        Don't worry if you didn't pass this time. You can review the material and try again.
                        {% endif %}
                    </p>
                    <p><a href="{{ quiz_results_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Detailed Results</a></p>
                    <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                </div>
                ''',
                'body_text': '''
                Your Quiz Results
                
                Hello {{ user.name }},
                
                You have completed the quiz for {{ quiz.title }}.
                
                Your Score: {{ quiz_attempt.score }}%
                
                {% if quiz_attempt.passed %}
                Congratulations on passing the quiz! You can now continue with the rest of the course.
                {% else %}
                Don't worry if you didn't pass this time. You can review the material and try again.
                {% endif %}
                
                View detailed results here: {{ quiz_results_url }}
                
                Best regards,
                The {{ config.platform_name }} Team
                ''',
                'description': 'Email sent to users with their quiz results',
                'template_key': 'quiz_completion'
            },
            {
                'name': 'Password Reset',
                'subject': 'Reset Your {{ config.platform_name }} Password',
                'body_html': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Password Reset Request</h1>
                    <p>Hello {{ user.name }},</p>
                    <p>We received a request to reset your password for your {{ config.platform_name }} account.</p>
                    <p>To reset your password, click the button below:</p>
                    <p><a href="{{ reset_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Your Password</a></p>
                    <p>If you did not request a password reset, please ignore this email or contact us if you have concerns.</p>
                    <p>This password reset link will expire in 24 hours.</p>
                    <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                </div>
                ''',
                'body_text': '''
                Password Reset Request
                
                Hello {{ user.name }},
                
                We received a request to reset your password for your {{ config.platform_name }} account.
                
                To reset your password, please visit the following link:
                {{ reset_url }}
                
                If you did not request a password reset, please ignore this email or contact us if you have concerns.
                
                This password reset link will expire in 24 hours.
                
                Best regards,
                The {{ config.platform_name }} Team
                ''',
                'description': 'Email sent to users when they request a password reset',
                'template_key': 'password_reset'
            },
            {
                'name': 'Certificate Issued Notification',
                'subject': 'Your Certificate for {{ course.title }} is Ready',
                'body_html': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1>Your Certificate is Ready!</h1>
                    <p>Hello {{ user.name }},</p>
                    <p>Congratulations on completing <strong>{{ course.title }}</strong>! Your certificate of completion is now ready.</p>
                    <p>You can view and download your certificate using the links below:</p>
                    <p>
                        <a href="{{ certificate_view_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">View Certificate</a>
                        <a href="{{ certificate_download_url }}" style="display: inline-block; background-color: {{ config.primary_color }}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Certificate</a>
                    </p>
                    <p>Your certificate has also been attached to this email for your convenience.</p>
                    <p>Congratulations again on your achievement!</p>
                    <p>Best regards,<br>The {{ config.platform_name }} Team</p>
                </div>
                ''',
                'body_text': '''
                Your Certificate is Ready!
                
                Hello {{ user.name }},
                
                Congratulations on completing {{ course.title }}! Your certificate of completion is now ready.
                
                You can view your certificate at: {{ certificate_view_url }}
                You can download your certificate at: {{ certificate_download_url }}
                
                Your certificate has also been attached to this email for your convenience.
                
                Congratulations again on your achievement!
                
                Best regards,
                The {{ config.platform_name }} Team
                ''',
                'description': 'Email sent to users when their course certificate is generated',
                'template_key': 'certificate_issued'
            }
        ]
        
        for template_data in default_templates:
            # Check if template exists already
            existing = cls.query.filter_by(template_key=template_data['template_key']).first()
            if not existing:
                template = cls(**template_data)
                db.session.add(template)
        
        db.session.commit()

class CertificateSettings(db.Model):
    """Settings for certificate generation and appearance"""
    __tablename__ = 'certificate_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    background_color = db.Column(db.String(20), default="#FFFFFF")
    border_color = db.Column(db.String(20), default="#294767")
    text_color = db.Column(db.String(20), default="#000000")
    signature_image = db.Column(db.String(255), nullable=True)
    logo_image = db.Column(db.String(255), nullable=True)
    certificate_title = db.Column(db.String(255), default="CERTIFICATE OF COMPLETION")
    certificate_text = db.Column(db.Text, default="has successfully completed the course")
    certificate_text_template = db.Column(db.Text, nullable=True)
    footer_text = db.Column(db.Text, default="")
    instructor_name = db.Column(db.String(100), default="Course Instructor")
    font = db.Column(db.String(100), default="Arial, sans-serif")
    auto_issue = db.Column(db.Boolean, default=True)
    send_email = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    @classmethod
    def get_settings(cls):
        """Get certificate settings, create default if none exist"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

class CertificateTemplate(db.Model):
    """Model for storing multiple certificate template designs"""
    __tablename__ = 'certificate_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    background_color = db.Column(db.String(20), default="#FFFFFF")
    border_color = db.Column(db.String(20), default="#294767")
    text_color = db.Column(db.String(20), default="#000000")
    signature_path = db.Column(db.String(255), nullable=True)
    logo_path = db.Column(db.String(255), nullable=True)
    certificate_title = db.Column(db.String(255), default="CERTIFICATE OF COMPLETION")
    certificate_text = db.Column(db.Text, default="has successfully completed the course")
    footer_text = db.Column(db.Text, default="")
    instructor_name = db.Column(db.String(100), default="Course Instructor")
    font = db.Column(db.String(100), default="Arial, sans-serif")
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)
    updated_at = db.Column(db.DateTime, default=get_utc_now, onupdate=get_utc_now)
    
    # Courses using this template
    courses = db.relationship('Course', backref='certificate_template', lazy=True)
    
    @classmethod
    def get_default_template(cls):
        """Get the default certificate template"""
        template = cls.query.filter_by(is_default=True).first()
        if not template:
            # Create a default template if none exists
            template = cls(
                name="Default Certificate",
                description="Default certificate template",
                is_default=True
            )
            db.session.add(template)
            db.session.commit()
        return template
