from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'patient' or 'doctor'
    specialty = db.Column(db.String(50), nullable=True) # For doctors
    phone_number = db.Column(db.String(20), nullable=True) # For WhatsApp
    patient_uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=True)
    email_confirmed = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(6), nullable=True)  # 6-digit code
    reset_expires = db.Column(db.DateTime, nullable=True)

    reports = db.relationship('Report', backref='patient', lazy=True, foreign_keys='Report.patient_id')
    medical_files = db.relationship('PatientFile', backref='patient_owner', lazy=True, foreign_keys='PatientFile.patient_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Medical Features
    age = db.Column(db.Integer)
    sex = db.Column(db.Integer)
    cp = db.Column(db.Integer)
    trestbps = db.Column(db.Integer)
    chol = db.Column(db.Integer)
    fbs = db.Column(db.Integer)
    restecg = db.Column(db.Integer)
    thalach = db.Column(db.Integer)
    exang = db.Column(db.Integer)
    oldpeak = db.Column(db.Float)
    slope = db.Column(db.Integer)
    ca = db.Column(db.Integer)
    thal = db.Column(db.Integer)

    # ML Results
    prediction_result = db.Column(db.Integer) # 1 = High Risk, 0 = Low Risk
    probability = db.Column(db.Float)
    
    # Status
    status = db.Column(db.String(20), default='Pending') # Pending, Verified
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    verified_at = db.Column(db.DateTime, nullable=True)
    
    medical_files = db.relationship('PatientFile', backref='report', lazy=True, foreign_keys='PatientFile.report_id')


class PatientFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('report.id'), nullable=True)
    
    filename = db.Column(db.String(256), nullable=False)
    original_filename = db.Column(db.String(256), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # Lab Report, CT/MRI Scan, X-Ray, ECG Report, etc.
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer)  # In bytes
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    uploaded_by = db.Column(db.String(100), nullable=True)  # Can be doctor or patient name

