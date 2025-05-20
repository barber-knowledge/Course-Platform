from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

class CertificateSettingsForm(FlaskForm):
    certificate_title = StringField('Certificate Title', validators=[DataRequired()])
    certificate_text = TextAreaField('Certificate Text', validators=[Optional()])
    certificate_text_template = TextAreaField('Certificate Text Template', validators=[Optional()])
    footer_text = TextAreaField('Footer Text', validators=[Optional()])
    instructor_name = StringField('Instructor Name', validators=[Optional()])
    
    certificate_border_color = StringField('Border Color', validators=[Optional()])
    certificate_text_color = StringField('Text Color', validators=[Optional()])
    background_color = StringField('Background Color', validators=[Optional()])
    
    certificate_font = SelectField('Font', choices=[
        ('Arial, sans-serif', 'Arial'),
        ('Times New Roman, serif', 'Times New Roman'),
        ('Courier New, monospace', 'Courier New'),
        ('Georgia, serif', 'Georgia'),
        ('Verdana, sans-serif', 'Verdana')
    ])
    
    certificate_logo = FileField('Certificate Logo', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    
    certificate_signature = FileField('Certificate Signature', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    
    auto_issue_certificates = BooleanField('Auto-issue Certificates')
    send_certificate_email = BooleanField('Send Email Notification')
    
    submit = SubmitField('Save Settings')

class CertificateTemplateForm(FlaskForm):
    """Form for certificate template management"""
    name = StringField('Template Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    certificate_title = StringField('Certificate Title', validators=[DataRequired()])
    certificate_text = TextAreaField('Certificate Text', default='has successfully completed the course')
    footer_text = TextAreaField('Footer Text')
    instructor_name = StringField('Instructor Name', default='Course Instructor')
    border_color = StringField('Border Color', default='#294767')
    text_color = StringField('Text Color', default='#000000')
    background_color = StringField('Background Color', default='#FFFFFF')
    font = SelectField('Font', choices=[
        ('Arial, sans-serif', 'Arial (Sans-serif)'),
        ('Times New Roman, serif', 'Times New Roman (Serif)'),
        ('Courier New, monospace', 'Courier New (Monospace)'),
        ('Georgia, serif', 'Georgia (Serif)'),
        ('Verdana, sans-serif', 'Verdana (Sans-serif)'),
        ('Trebuchet MS, sans-serif', 'Trebuchet MS (Sans-serif)')
    ])
    logo = FileField('Logo Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    signature = FileField('Signature Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    is_default = BooleanField('Set as Default Template')
    submit = SubmitField('Save Template')