#app/forms.py

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, PasswordField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
import re
from app.models import ApplicationType, Category, OSSupport, FHIRSupport, Speciality, PricingLicense, DesignedFor, EHRSupport
from app import db

def validate_url_or_path(form, field):
    if not field.data:
        return
    # Validate file paths like /static/uploads/<uuid>_<filename>.jpg|png
    if field.data.startswith('/app/uploads/'):
        # Allow UUIDs (hex with hyphens), underscores, mixed-case filenames
        path_pattern = r'^/app/uploads/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_[\w\-\.]+\.(jpg|png)$'
        if re.match(path_pattern, field.data, re.I):
            return
    # Validate URLs
    url_pattern = r'^(https?:\/\/)?([\w\-]+\.)+[\w\-]+(\/[\w\-\.]*)*\/?(\?[^\s]*)?(#[^\s]*)?$'
    if not re.match(url_pattern, field.data):
        raise ValidationError('Invalid URL or file path.')

class SmartAppForm(FlaskForm):
    name = StringField('App Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=500)])
    developer = StringField('Developer/Organization', validators=[DataRequired(), Length(min=3, max=100)])
    contact_email = StringField('Contact Email', validators=[DataRequired(), Email()])
    logo_url = StringField('Logo URL', validators=[Optional(), validate_url_or_path], render_kw={"placeholder": "https://example.com/logo.png or leave blank to upload"})
    logo_upload = FileField('Upload Logo', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    launch_url = StringField('Launch URL', validators=[DataRequired(), Length(max=200)])
    client_id = StringField('Client ID', validators=[DataRequired(), Length(min=3, max=100)])
    scopes = TextAreaField('Scopes (comma-separated)', validators=[DataRequired(), Length(max=500)], render_kw={"placeholder": "patient/Patient.read,launch/patient"})
    website = StringField('Company Website', validators=[Optional(), Length(max=200)], render_kw={"placeholder": "https://example.com"})
    designed_for = SelectField('Designed For', coerce=int, validators=[DataRequired()])
    designed_for_new = StringField('Add New Designed For', validators=[Optional(), Length(max=100)])
    application_type = SelectField('Application Type', coerce=int, validators=[DataRequired()])
    application_type_new = StringField('Add New Application Type', validators=[Optional(), Length(max=100)])
    fhir_compatibility = SelectField('FHIR Compatibility', coerce=int, validators=[DataRequired()])
    fhir_compatibility_new = StringField('Add New FHIR Compatibility', validators=[Optional(), Length(max=100)])
    categories = SelectMultipleField('Categories', coerce=int, validators=[DataRequired()])
    categories_new = StringField('Add New Category', validators=[Optional(), Length(max=100)])
    specialties = SelectMultipleField('Specialties', coerce=int, validators=[DataRequired()])
    specialties_new = StringField('Add New Speciality', validators=[Optional(), Length(max=100)])
    licensing_pricing = SelectField('Licensing & Pricing', coerce=int, validators=[DataRequired()])
    licensing_pricing_new = StringField('Add New Licensing/Pricing', validators=[Optional(), Length(max=100)])
    os_support = SelectMultipleField('OS Support', coerce=int, validators=[DataRequired()])
    os_support_new = StringField('Add New OS Support', validators=[Optional(), Length(max=100)])
    app_image_urls = TextAreaField('App Image URLs (one per line)', validators=[Optional(), Length(max=1000)], render_kw={"placeholder": "e.g., https://example.com/image1.png"})
    app_image_uploads = FileField('Upload App Images', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    ehr_support = SelectMultipleField('EHR Support', coerce=int, validators=[DataRequired()])
    ehr_support_new = StringField('Add New EHR Support', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Register App')

    def __init__(self, *args, **kwargs):
        super(SmartAppForm, self).__init__(*args, **kwargs)
        self.application_type.choices = [(t.id, t.name) for t in ApplicationType.query.all()]
        self.categories.choices = [(c.id, c.name) for c in Category.query.all()]
        self.os_support.choices = [(o.id, o.name) for o in OSSupport.query.all()]
        self.fhir_compatibility.choices = [(f.id, f.name) for f in FHIRSupport.query.all()]
        self.specialties.choices = [(s.id, s.name) for s in Speciality.query.all()]
        self.licensing_pricing.choices = [(p.id, p.name) for p in PricingLicense.query.all()]
        self.designed_for.choices = [(d.id, d.name) for d in DesignedFor.query.all()]
        self.ehr_support.choices = [(e.id, e.name) for e in EHRSupport.query.all()]

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class GalleryFilterForm(FlaskForm):
    categories = StringField('Categories', validators=[Length(max=500)], render_kw={"placeholder": "e.g., Clinical, Billing"})
    fhir_compatibility = StringField('FHIR Compatibility', validators=[Length(max=200)], render_kw={"placeholder": "e.g., R4, US Core"})
    submit = SubmitField('Filter')