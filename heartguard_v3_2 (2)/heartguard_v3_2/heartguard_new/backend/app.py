"""
HeartGuard AI — Flask Backend Application
==========================================
All routes, authentication, and business logic.
Frontend templates and static files are served from ../frontend/
"""
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Ensure backend modules can import each other
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from models import db, User, Report, PatientFile
from ml_core import predict_heart_disease, model_cv_scores
from notifications import dispatch_report_notifications
from pdf_generator import generate_medical_report_pdf
import qrcode

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# ── Path Configuration ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')

# ── Flask App ──
app = Flask(
    __name__,
    template_folder=os.path.join(FRONTEND_DIR, 'templates'),
    static_folder=os.path.join(FRONTEND_DIR, 'static'),
    instance_path=INSTANCE_DIR
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'heartguard-dev-secret-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google OAuth
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ═══════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html', google_client_id=GOOGLE_CLIENT_ID)


@app.route('/auth/google', methods=['POST'])
def auth_google():
    """Handle Google Sign-In: verify ID token, create/login user."""
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        data = request.get_json()
        token = data.get('credential')

        if not token:
            return jsonify({'success': False, 'error': 'No credential provided'}), 400

        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )

        email = idinfo.get('email')
        name = idinfo.get('name', email.split('@')[0])

        if not email:
            return jsonify({'success': False, 'error': 'Email not found in Google account'}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            user = User(
                name=name,
                email=email,
                role='patient',
                patient_uuid=str(uuid.uuid4())
            )
            user.set_password(uuid.uuid4().hex)
            db.session.add(user)
            db.session.commit()

            qr_dir = os.path.join(FRONTEND_DIR, 'static', 'qrcodes')
            os.makedirs(qr_dir, exist_ok=True)
            qr_data = url_for('scan_patient_qr', patient_id=user.id, _external=True)
            qr = qrcode.make(qr_data)
            qr.save(os.path.join(qr_dir, f"patient_{user.id}.png"))

            flash(f'Welcome {name}! Account created via Google.', 'success')
        else:
            flash(f'Welcome back, {user.name}!', 'success')

        login_user(user)
        return jsonify({'success': True, 'redirect': url_for('dashboard')})

    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid Google token: {str(e)}'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        phone_number = request.form.get('phone_number')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists', 'error')
            return redirect(url_for('register'))

        new_user = User(email=email, name=name, role=role, phone_number=phone_number)

        if role == 'patient':
            new_user.patient_uuid = str(uuid.uuid4())

        new_user.set_password(password)

        if role == 'doctor':
            new_user.specialty = request.form.get('specialty', 'Cardiology')

        db.session.add(new_user)
        db.session.commit()

        subject = "Welcome to HeartGuard AI - Your Account Details"
        body = f"""Hello {name},

Welcome to HeartGuard AI! Your account has been created successfully.

Your login details:
Email: {email}
Password: {password}

Please keep this information secure.

Best regards,
HeartGuard AI Team"""

        from notifications import send_email_notification
        send_email_notification(email, subject, body)

        if role == 'patient':
            qr_dir = os.path.join(FRONTEND_DIR, 'static', 'qrcodes')
            os.makedirs(qr_dir, exist_ok=True)
            qr_data = url_for('scan_patient_qr', patient_id=new_user.id, _external=True)
            qr = qrcode.make(qr_data)
            qr.save(os.path.join(qr_dir, f"patient_{new_user.id}.png"))

        login_user(new_user)
        flash('Registration successful! Check your email for your account details.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            import random
            reset_code = ''.join(random.choices('0123456789', k=6))
            user.reset_token = reset_code
            user.reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            db.session.commit()

            subject = "HeartGuard AI - Password Reset Code"
            body = f"""Hello {user.name},

Your reset code is: {reset_code}

This code will expire in 1 hour.

Best regards,
HeartGuard AI Team"""

            from notifications import send_email_notification
            send_email_notification(email, subject, body)

            flash('Reset code sent to your email.', 'success')
            return redirect(url_for('reset_password'))
        else:
            flash('Email not found.', 'error')

    return render_template('forgot_password.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        code = request.form.get('code')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('reset_password'))

        user = User.query.filter_by(email=email).first()

        if user and user.reset_token == code and user.reset_expires > datetime.now(timezone.utc):
            user.set_password(password)
            user.reset_token = None
            user.reset_expires = None
            db.session.commit()

            flash('Password reset successful. You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired reset code.', 'error')

    return render_template('reset_password.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'patient':
        reports = Report.query.filter_by(patient_id=current_user.id).order_by(Report.created_at.desc()).all()
        return render_template('patient_dashboard.html', reports=reports)
    elif current_user.role == 'doctor':
        pending_reports = Report.query.filter_by(status='Pending').order_by(Report.created_at.desc()).all()
        verified_reports = Report.query.filter_by(doctor_id=current_user.id, status='Verified').order_by(Report.created_at.desc()).all()
        
        # Get all patients with pending or verified reports
        patient_ids = set(r.patient_id for r in pending_reports + verified_reports)
        patients = User.query.filter(User.id.in_(patient_ids), User.role=='patient').all() if patient_ids else []
        
        pending_count = len(pending_reports)
        verified_count = len(verified_reports)
        high_risk_count = len([r for r in verified_reports if r.prediction_result == 1])
        
        return render_template('doctor_dashboard.html', 
                             pending_reports=pending_reports, 
                             patients=patients,
                             pending_count=pending_count,
                             verified_count=verified_count,
                             high_risk_count=high_risk_count)
    return redirect(url_for('home'))


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    """User account profile page."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone_number', '').strip()
            if name:
                current_user.name = name
            current_user.phone_number = phone
            db.session.commit()
            flash('Profile updated successfully.', 'success')

        elif action == 'change_password':
            current_pw = request.form.get('current_password')
            new_pw = request.form.get('new_password')
            confirm_pw = request.form.get('confirm_password')

            if not current_user.check_password(current_pw):
                flash('Current password is incorrect.', 'error')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'error')
            elif len(new_pw) < 6:
                flash('Password must be at least 6 characters.', 'error')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash('Password changed successfully.', 'success')

        return redirect(url_for('account'))

    reports_count = 0
    if current_user.role == 'patient':
        reports_count = Report.query.filter_by(patient_id=current_user.id).count()
    elif current_user.role == 'doctor':
        reports_count = Report.query.filter_by(doctor_id=current_user.id).count()

    return render_template('account.html', reports_count=reports_count)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if name and email and message:
            # Send to admin
            from notifications import send_email_notification
            admin_email = os.environ.get('MAIL_USERNAME', '')
            if admin_email:
                send_email_notification(
                    admin_email,
                    f"HeartGuard Contact: {subject}",
                    f"From: {name} <{email}>\n\n{message}"
                )
            flash('Your message has been sent! We will get back to you soon.', 'success')
        else:
            flash('Please fill in all required fields.', 'error')

        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/help')
def help_page():
    """Help & FAQ page."""
    return render_template('help.html')


@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if current_user.role != 'patient':
        flash('Only patients can take medical assessments.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            data = {
                'age': int(request.form.get('age')),
                'sex': int(request.form.get('sex')),
                'cp': int(request.form.get('cp')),
                'trestbps': int(request.form.get('trestbps')),
                'chol': int(request.form.get('chol')),
                'fbs': int(request.form.get('fbs')),
                'restecg': int(request.form.get('restecg')),
                'thalach': int(request.form.get('thalach')),
                'exang': int(request.form.get('exang')),
                'oldpeak': float(request.form.get('oldpeak')),
                'slope': int(request.form.get('slope')),
                'ca': int(request.form.get('ca')),
                'thal': int(request.form.get('thal'))
            }

            ml_result = predict_heart_disease(data)

            new_report = Report(
                patient_id=current_user.id,
                **data,
                prediction_result=ml_result['prediction'],
                probability=ml_result['probability'],
                status='Pending'
            )
            db.session.add(new_report)
            db.session.commit()

            flash('Assessment complete! Your report is pending doctor verification.', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')

    return render_template('predict.html')


@app.route('/patient_record/<patient_uuid>')
def patient_record(patient_uuid):
    user = User.query.filter_by(patient_uuid=patient_uuid, role='patient').first_or_404()
    reports = Report.query.filter_by(patient_id=user.id, status='Verified').order_by(Report.created_at.desc()).all()
    medical_files = PatientFile.query.filter_by(patient_id=user.id).order_by(PatientFile.created_at.desc()).all()
    return render_template('patient_record.html', patient=user, reports=reports, medical_files=medical_files, view_as_doctor=False)


@app.route('/review_report/<int:report_id>')
@login_required
def review_report(report_id):
    if current_user.role != 'doctor':
        flash('Only doctors can review reports.', 'error')
        return redirect(url_for('dashboard'))

    report = Report.query.get_or_404(report_id)
    past_reports = Report.query.filter_by(patient_id=report.patient_id, status='Verified').order_by(Report.created_at.desc()).all()

    return render_template('review_report.html', report=report, past_reports=past_reports)


@app.route('/verify_report/<int:report_id>')
@login_required
def verify_report(report_id):
    if current_user.role != 'doctor':
        flash('Only doctors can verify reports.', 'error')
        return redirect(url_for('dashboard'))

    report = Report.query.get_or_404(report_id)
    report.status = 'Verified'
    report.doctor_id = current_user.id
    report.verified_at = datetime.now(timezone.utc)
    db.session.commit()

    reports_dir = os.path.join(FRONTEND_DIR, 'static', 'reports')
    pdf_filename, pdf_filepath = generate_medical_report_pdf(report, report.patient, current_user, reports_dir)
    base_url = request.host_url

    email_sent, whatsapp_sent, whatsapp_reason = dispatch_report_notifications(
        report, current_user,
        pdf_filepath=pdf_filepath,
        base_url=base_url,
        pdf_filename=pdf_filename
    )

    msg = f'Report #{report.id} verified!'
    if email_sent and whatsapp_sent:
        msg += ' Sent to patient via Email & WhatsApp.'
    elif email_sent:
        msg += ' Sent to patient via Email.'
    elif whatsapp_sent:
        msg += ' Sent to patient via WhatsApp.'
    else:
        msg += ' (Notifications skipped - configure .env with real credentials)'

    category = 'success' if (email_sent or whatsapp_sent) else 'warning'
    flash(msg, category)
    return redirect(url_for('dashboard'))


@app.route('/api/model_info')
def model_info():
    return jsonify({
        'models': model_cv_scores,
        'total_models': 6,
        'ensemble_type': 'Soft Voting',
        'features': 13,
        'datasets': 5,
        'records': '1,302+'
    })


# ═══════════════════════════════════════════════════════════════
#  NEW FEATURES: Doctor Directory, Medical Files, QR Scanning
# ═══════════════════════════════════════════════════════════════

@app.route('/doctor_directory')
def doctor_directory():
    """Display all registered cardiologists."""
    doctors = User.query.filter_by(role='doctor').all()
    return render_template('doctor_directory.html', doctors=doctors)


@app.route('/qr_scanner', methods=['GET', 'POST'])
@login_required
def qr_scanner():
    """Doctor QR scanner page for scanning patient QR codes."""
    if current_user.role != 'doctor':
        flash('Only doctors can access the QR scanner.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip()
        if not patient_id:
            flash('Please enter a patient ID or scan the QR code.', 'error')
            return redirect(url_for('qr_scanner'))
        return redirect(url_for('scan_patient_qr', patient_id=patient_id))

    return render_template('qr_scanner.html')


@app.route('/medical_files')
@login_required
def medical_files():
    """Patient's medical file upload and management page."""
    if current_user.role != 'patient':
        flash('Only patients can upload medical files.', 'error')
        return redirect(url_for('dashboard'))
    
    patient_files = PatientFile.query.filter_by(patient_id=current_user.id).order_by(PatientFile.created_at.desc()).all()
    return render_template('medical_files.html', patient_files=patient_files)


@app.route('/upload_medical_file', methods=['POST'])
@login_required
def upload_medical_file():
    """Handle medical file uploads from patients."""
    if current_user.role != 'patient':
        flash('Only patients can upload medical files.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        from werkzeug.utils import secure_filename
        
        if 'file' not in request.files:
            flash('No file provided.', 'error')
            return redirect(url_for('medical_files'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(url_for('medical_files'))
        
        allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            flash('File type not allowed. Use: PDF, JPG, PNG, DOC, DOCX', 'error')
            return redirect(url_for('medical_files'))
        
        # Create medical files directory
        medical_dir = os.path.join(INSTANCE_DIR, 'medical_files', str(current_user.id))
        os.makedirs(medical_dir, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"patient_{current_user.id}_{uuid.uuid4().hex[:8]}.{file_ext}"
        file_path = os.path.join(medical_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Create database record
        patient_file = PatientFile(
            patient_id=current_user.id,
            filename=unique_filename,
            original_filename=secure_filename(file.filename),
            document_type=request.form.get('document_type', 'Medical Document'),
            description=request.form.get('description', ''),
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            uploaded_by=current_user.name
        )
        
        db.session.add(patient_file)
        db.session.commit()
        
        flash(f'File "{file.filename}" uploaded successfully!', 'success')
        return redirect(url_for('medical_files'))
        
    except Exception as e:
        flash(f'Error uploading file: {str(e)}', 'error')
        return redirect(url_for('medical_files'))


@app.route('/download_medical_file/<int:file_id>')
@login_required
def download_file(file_id):
    """Download a medical file."""
    patient_file = PatientFile.query.get_or_404(file_id)
    
    # Check permission - only patient who uploaded or doctors reviewing can download
    if current_user.id != patient_file.patient_id and current_user.role != 'doctor':
        flash('You do not have permission to download this file.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        return send_file(patient_file.file_path, as_attachment=True, download_name=patient_file.original_filename)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('medical_files'))


@app.route('/delete_medical_file/<int:file_id>')
@login_required
def delete_medical_file(file_id):
    """Delete a medical file."""
    patient_file = PatientFile.query.get_or_404(file_id)
    
    # Check permission
    if current_user.id != patient_file.patient_id:
        flash('You can only delete your own files.', 'error')
        return redirect(url_for('medical_files'))
    
    try:
        # Delete physical file
        if os.path.exists(patient_file.file_path):
            os.remove(patient_file.file_path)
        
        # Delete database record
        db.session.delete(patient_file)
        db.session.commit()
        
        flash('File deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('medical_files'))


@app.route('/doctor_dashboard_enhanced')
@login_required
def doctor_dashboard_enhanced():
    """Enhanced doctor dashboard with patient records."""
    if current_user.role != 'doctor':
        flash('Only doctors can access this page.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all patients (all reports for this doctor or pending)
    pending_reports = Report.query.filter_by(status='Pending').order_by(Report.created_at.desc()).all()
    
    # Get all unique patients from pending reports
    patient_ids = set(report.patient_id for report in pending_reports)
    patients = User.query.filter(User.id.in_(patient_ids), User.role=='patient').all() if patient_ids else []
    
    pending_count = len(pending_reports)
    verified_count = Report.query.filter_by(doctor_id=current_user.id, status='Verified').count()
    high_risk_count = Report.query.filter(Report.status=='Verified', Report.prediction_result==1).count()
    
    return render_template('doctor_dashboard.html', 
                         pending_reports=pending_reports,
                         patients=patients,
                         pending_count=pending_count,
                         verified_count=verified_count,
                         high_risk_count=high_risk_count)


@app.route('/scan_patient_qr/<int:patient_id>')
@login_required
def scan_patient_qr(patient_id):
    """View patient's medical history when doctor scans QR code."""
    if current_user.role != 'doctor':
        flash('Only doctors can view patient records.', 'error')
        return redirect(url_for('dashboard'))
    
    patient = User.query.filter_by(id=patient_id, role='patient').first_or_404()
    reports = Report.query.filter_by(patient_id=patient.id).order_by(Report.created_at.desc()).all()
    medical_files = PatientFile.query.filter_by(patient_id=patient.id).order_by(PatientFile.created_at.desc()).all()
    
    return render_template('patient_record.html', 
                         patient=patient, 
                         reports=reports, 
                         medical_files=medical_files,
                         view_as_doctor=True)


if __name__ == '__main__':
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
