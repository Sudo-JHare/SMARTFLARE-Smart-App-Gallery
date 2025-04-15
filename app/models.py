#app/models.py
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255))
    oauth_provider = db.Column(db.String(50))
    oauth_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class ApplicationType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class OSSupport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class FHIRSupport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Speciality(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class PricingLicense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class DesignedFor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class EHRSupport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class SmartApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    developer = db.Column(db.String(100), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    logo_url = db.Column(db.String(200))
    launch_url = db.Column(db.String(200), nullable=False)
    client_id = db.Column(db.String(100), nullable=False)
    scopes = db.Column(db.Text)
    website = db.Column(db.String(200))
    designed_for_id = db.Column(db.Integer, db.ForeignKey('designed_for.id'))
    application_type_id = db.Column(db.Integer, db.ForeignKey('application_type.id'))
    fhir_compatibility_id = db.Column(db.Integer, db.ForeignKey('fhir_support.id'))
    categories = db.Column(db.Text)  # Comma-separated Category IDs
    specialties = db.Column(db.Text)  # Comma-separated Speciality IDs
    licensing_pricing_id = db.Column(db.Integer, db.ForeignKey('pricing_license.id'))
    os_support = db.Column(db.Text)  # Comma-separated OSSupport IDs
    app_images = db.Column(db.Text)
    ehr_support = db.Column(db.Text)  # Comma-separated EHRSupport IDs
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)