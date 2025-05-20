"""
Certificates blueprint routes
"""
from flask import Blueprint, render_template, send_file, abort, current_app, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Certificate, Course, User
from app.utils.certificate import get_user_certificates, verify_certificate
import os
from datetime import datetime

bp = Blueprint('certificates', __name__, url_prefix='/certificates')

@bp.route('/')
@login_required
def index():
    """
    View all user certificates
    """
    # Get all certificates for the current user
    certificates = get_user_certificates(current_user.id)
    
    return render_template('certificates/index.html', 
                          title='My Certificates',
                          certificates=certificates)

@bp.route('/<int:course_id>')
@login_required
def view(course_id):
    """
    View a specific certificate
    """
    # Get the certificate for this course and user
    certificate = Certificate.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first_or_404()
    
    # Load related course and user data
    certificate.course = Course.query.get(certificate.course_id)
    certificate.user = User.query.get(certificate.user_id)
    
    return render_template('certificates/certificate.html', 
                          title=f'Certificate for {certificate.course.title}', 
                          certificate=certificate)

@bp.route('/<int:course_id>/download')
@login_required
def download(course_id):
    """
    Download a certificate
    """
    # Get the certificate for this course and user
    certificate = Certificate.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first_or_404()
    
    try:
        # For now, just serve an HTML version since actual PDF generation is not implemented
        # In a real implementation, you would serve the PDF file from certificate.file_path
        
        # Check if the certificate file exists
        certificate_path = os.path.join(current_app.root_path, 'static', certificate.file_path)
        if os.path.exists(certificate_path):
            return send_file(certificate_path, as_attachment=True, 
                            download_name=f'certificate_{certificate.course.title}_{datetime.now().strftime("%Y%m%d")}.pdf')
        else:
            # If no physical file exists, redirect to the HTML view
            flash('PDF certificate is not available. Please view the online certificate.', 'info')
            return redirect(url_for('certificates.view', course_id=course_id))
    except Exception as e:
        current_app.logger.error(f"Error downloading certificate: {str(e)}")
        flash('There was an error downloading your certificate. Please try again later.', 'danger')
        return redirect(url_for('certificates.view', course_id=course_id))

@bp.route('/verify/<certificate_id>')
def verify(certificate_id):
    """
    Verify a certificate's authenticity
    """
    # Get the certificate by its unique ID
    certificate = verify_certificate(certificate_id)
    
    if certificate:
        # Certificate is valid, load related data
        certificate.course = Course.query.get(certificate.course_id)
        certificate.user = User.query.get(certificate.user_id)
        
        return render_template('certificates/verify.html', 
                              title='Certificate Verification', 
                              certificate=certificate,
                              is_valid=True)
    else:
        # Certificate is not valid
        return render_template('certificates/verify.html', 
                              title='Certificate Verification', 
                              certificate_id=certificate_id,
                              is_valid=False)

@bp.route('/api/verify/<certificate_id>')
def api_verify(certificate_id):
    """
    API endpoint to verify a certificate's authenticity
    """
    # Get the certificate by its unique ID
    certificate = verify_certificate(certificate_id)
    
    if certificate:
        # Certificate is valid
        return jsonify({
            'valid': True,
            'certificate_id': certificate.certificate_id,
            'course_title': Course.query.get(certificate.course_id).title,
            'user_name': User.query.get(certificate.user_id).name,
            'issue_date': certificate.issue_date.strftime('%Y-%m-%d')
        }), 200
    else:
        # Certificate is not valid
        return jsonify({
            'valid': False,
            'message': 'Certificate not found or invalid'
        }), 404