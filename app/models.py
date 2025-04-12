"""
SQLAlchemy ORM models for the Modular Course Platform
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrolled_courses = db.relationship('UserCourse', back_populates='user', lazy='dynamic')
    quiz_attempts = db.relationship('QuizAttempt', back_populates='user', lazy='dynamic')
    video_progress = db.relationship('VideoProgress', back_populates='user', lazy='dynamic')
    certificates = db.relationship('Certificate', back_populates='user', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    videos = db.relationship('Video', back_populates='course', lazy='dynamic', cascade='all, delete-orphan')
    quiz = db.relationship('Quiz', back_populates='course', uselist=False, cascade='all, delete-orphan')
    enrollments = db.relationship('UserCourse', back_populates='course', lazy='dynamic')
    certificates = db.relationship('Certificate', back_populates='course', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='course', lazy='dynamic')
    
    def __repr__(self):
        return f'<Course {self.title}>'

class Video(db.Model):
    """Video model for course videos"""
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    video_path = db.Column(db.String(255), nullable=False)
    sequence_order = db.Column(db.Integer, nullable=False)
    duration_seconds = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = db.relationship('Course', back_populates='videos')
    progress_records = db.relationship('VideoProgress', back_populates='video', lazy='dynamic', cascade='all, delete-orphan')
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=True)
    option_d = db.Column(db.Text, nullable=True)
    correct_option = db.Column(db.Enum('A', 'B', 'C', 'D', name='correct_option_enum'), nullable=False)
    sequence_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quiz = db.relationship('Quiz', back_populates='questions')
    
    __table_args__ = (
        db.UniqueConstraint('quiz_id', 'sequence_order', name='_quiz_sequence_uc'),
    )
    
    def __repr__(self):
        return f'<QuizQuestion {self.id} ({self.quiz_id})>'

class QuizAttempt(db.Model):
    """Quiz Attempt model to track student quiz submissions"""
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    passed = db.Column(db.Boolean, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='video_progress')
    video = db.relationship('Video', back_populates='progress_records')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'video_id', name='_user_video_uc'),
    )
    
    def __repr__(self):
        return f'<VideoProgress - User: {self.user_id}, Video: {self.video_id}>'

class PlatformConfig(db.Model):
    """Platform configuration settings"""
    __tablename__ = 'platform_config'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_name = db.Column(db.String(100), nullable=False, default='Modular Course Platform')
    primary_color = db.Column(db.String(7), nullable=False, default='#0d6efd')  # Bootstrap primary blue
    secondary_color = db.Column(db.String(7), nullable=False, default='#6c757d')  # Bootstrap secondary
    logo_path = db.Column(db.String(255), nullable=True)
    welcome_message = db.Column(db.Text, nullable=True)
    setup_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Stripe configuration
    stripe_secret_key = db.Column(db.String(255), nullable=True)
    stripe_publishable_key = db.Column(db.String(255), nullable=True)
    stripe_enabled = db.Column(db.Boolean, default=False)
    
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