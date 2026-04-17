# HeartGuard AI - Intelligent Cardiac Risk Assessment System

## Overview

HeartGuard AI is an advanced machine learning-powered web application designed for cardiac risk assessment and patient-doctor collaboration. It combines cutting-edge ML models with a secure, user-friendly interface for cardiologists and patients.

## Key Features

### 🏥 Patient Features
- **Heart Disease Risk Assessment** - AI-powered prediction using 6-model ensemble
- **Medical Reports** - View and manage all cardiac assessment reports
- **Medical File Upload** - Share medical documents with doctors (PDF, images, documents)
- **Patient QR Code** - Unique QR code with patient ID for instant doctor access
- **Doctor Discovery** - Browse and connect with specialist cardiologists
- **Account Management** - Update profile, view QR code, change password

### 👨‍⚕️ Doctor Features
- **QR Code Scanner** - Live webcam scanning or manual patient ID entry
- **Patient History Access** - View complete medical records via QR scan
- **Report Verification** - Review and verify patient assessment reports
- **Patient Dashboard** - Pending reports queue and statistics
- **Patient Files** - Access uploaded medical documents from patients
- **Specialty Registration** - Register by cardiology specialty type

### 🔒 Security & Privacy
- Role-based access control (Patient/Doctor)
- Secure login with password hashing
- Google OAuth2 integration
- Doctor-only access to patient QR scanning
- Permission checks for file downloads

### 🎯 Medical Intelligence
- **6-Model ML Ensemble** - Multiple algorithms for cardiac risk prediction
- **1,302+ Training Records** - Diverse cardiac dataset
- **Real-time Risk Scoring** - Instant probability calculation
- **Medical Report Generation** - PDF reports with detailed analysis

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- Windows/Mac/Linux
- 500MB disk space
- Modern web browser (Chrome, Firefox, Edge)

### Step 1: Install Dependencies

```bash
cd heartguard_new
pip install -r requirements.txt
```

### Step 2: Initialize Database

The database is automatically initialized on first run.

### Step 3: Run the Application

```bash
python run.py
```

The server will start on:
```
http://127.0.0.1:5000
```

---

## Usage Guide

### For Patients

#### 1. Register Account
1. Go to http://127.0.0.1:5000
2. Click **"Get Started"** → **"Sign Up"**
3. Choose **"Patient"** role
4. Enter name, email, password, phone number
5. Click **"Create Patient Account"**

#### 2. Get Your QR Code
1. Log in to patient account
2. Click **"Account"** in navigation
3. Scroll to **"Patient QR Code"** section
4. See your unique **Patient ID** and **QR code image**
5. Share this QR code with your doctors

#### 3. Run Heart Assessment
1. Log in as patient
2. Click **"Assessment"** in navigation
3. Fill in your health metrics (age, blood pressure, cholesterol, etc.)
4. Click **"Analyze My Heart Health"**
5. Get instant AI risk prediction (Low Risk / High Risk)
6. View detailed report with probability score

#### 4. Share Medical Documents
1. Log in as patient
2. Click **"Medical Files"** in navigation
3. Click the dropzone or select file
4. Choose document type (Lab Report, CT/MRI Scan, X-Ray, ECG, etc.)
5. Add description (optional)
6. Click **"Upload"**
7. Doctors can now download these files when reviewing your record

#### 5. Find & Contact Doctors
1. Log in as patient
2. Click **"Find Doctors"** in navigation
3. Browse cardiologists by specialty:
   - Interventional Cardiologist
   - Electrophysiologist
   - Clinical Cardiologist
   - Pediatric Cardiologist
   - Cardiothoracic Surgeon
4. View doctor contact information

---

### For Doctors

#### 1. Register Account
1. Go to http://127.0.0.1:5000
2. Click **"Get Started"** → **"Sign Up"**
3. Choose **"Doctor"** role
4. Enter name, email, password, specialty
5. Click **"Create Doctor Account"**

#### 2. Scan Patient QR Code
1. Log in to doctor account
2. Click **"QR Scanner"** in navigation
3. **Option A (Camera):**
   - Click **"Start Camera"**
   - Point webcam at patient's QR code
   - System extracts patient ID automatically
4. **Option B (Manual):**
   - Click **"Access Patient Record"** without camera
   - Manually enter patient ID (e.g., 5)
   - Click **"Access Patient Record"**

#### 3. View Patient Medical History
After scanning/entering patient ID, you'll see:
- **Patient Information** (name, email, contact)
- **Patient ID & QR Code** (for reference)
- **All Medical Reports** (past and current)
- **Uploaded Medical Documents** (PDF, images, etc.)
- **Risk Scores & Probabilities**
- **Vital Signs** (age, BP, heart rate, cholesterol)

#### 4. Download Patient Files
1. Scroll to **"Uploaded Medical Documents"** section
2. Click **"Download File"** button on any document
3. File downloads to your computer
4. Review alongside patient's health assessment

#### 5. Verify & Analyze Reports
1. Log in to doctor account
2. Click **"Dashboard"** in navigation
3. See **"Pending Verification"** queue
4. Click **"Review Patient Record"** on any pending report
5. View patient's assessment and medical files
6. Click **"Verify & Complete"** to mark report as verified

---

## Application Structure

```
heartguard_new/
├── backend/
│   ├── app.py                 # Flask application & routes
│   ├── models.py              # SQLAlchemy database models
│   ├── ml_core.py             # Machine learning ensemble
│   ├── pdf_generator.py       # Report generation
│   └── notifications.py       # Email notifications
├── frontend/
│   ├── templates/
│   │   ├── base.html          # Navigation & layout
│   │   ├── home.html          # Landing page
│   │   ├── login.html         # Login page
│   │   ├── register.html      # Registration page
│   │   ├── patient_dashboard.html      # Patient home
│   │   ├── doctor_dashboard.html       # Doctor home
│   │   ├── predict.html       # Assessment form
│   │   ├── patient_record.html         # Patient history (doctor view)
│   │   ├── qr_scanner.html    # QR scanner page
│   │   ├── doctor_directory.html       # Doctor listing
│   │   ├── medical_files.html          # File upload page
│   │   └── account.html       # Account settings
│   └── static/
│       ├── css/style.css
│       ├── js/main.js
│       └── qrcodes/           # Patient QR code images
├── datasets/                  # Training data
├── instance/                  # Database & uploaded files
│   ├── database.db
│   └── medical_files/
├── run.py                     # Application entry point
├── init_db.py                 # Database initialization
└── requirements.txt           # Python dependencies
```

---

## Database Schema

### User Table
- `id` - Primary key
- `name` - Full name
- `email` - Unique email
- `password_hash` - Encrypted password
- `role` - 'patient' or 'doctor'
- `patient_uuid` - UUID for public access
- `id` - **Patient ID** (used in QR code)
- `phone_number` - Contact number
- `specialty` - Doctor's specialty

### Report Table
- `id` - Primary key
- `patient_id` - Foreign key to User
- `doctor_id` - Foreign key to User (doctor reviewing)
- `prediction_result` - 0 (Low Risk) or 1 (High Risk)
- `probability` - Risk score 0-1
- `status` - 'Pending' or 'Verified'
- `created_at` - Timestamp

### PatientFile Table
- `id` - Primary key
- `patient_id` - Foreign key to User
- `filename` - Stored filename
- `original_filename` - Original upload name
- `document_type` - Type of document
- `description` - User notes
- `file_path` - Storage location
- `file_size` - Size in bytes
- `created_at` - Upload timestamp

---

## QR Code System

### How It Works
1. **Generation**: Patient QR code created at registration
2. **Storage**: Saved as `patient_{id}.png` in `frontend/static/qrcodes/`
3. **Encoding**: Contains URL to secure `/scan_patient_qr/<patient_id>` route
4. **Access**: Only authenticated doctors can scan/access
5. **Display**: 
   - Patients see it on Account page
   - Doctors see it when viewing patient record

### Scanner Features
- **Live Camera Scanning** - Use webcam with jsQR library
- **Fallback Mode** - Manual patient ID entry if camera unavailable
- **Auto-Detection** - Extracts patient ID from QR automatically
- **Error Handling** - Clear status messages and visual feedback

---

## Machine Learning Details

### Model Ensemble
The system uses 6 sub-models for cardiac risk prediction:
- Logistic Regression
- Random Forest
- Gradient Boosting
- Support Vector Machine
- Neural Network
- K-Nearest Neighbors

### Input Features
- Age, Sex, Chest pain type
- Resting blood pressure
- Serum cholesterol
- Fasting blood sugar
- Resting ECG results
- Max heart rate achieved
- Exercise induced angina
- ST depression
- ST slope
- Major vessels count
- Thalassemia type

### Output
- **Risk Category**: Low Risk (0) or High Risk (1)
- **Probability Score**: 0-100% confidence

---

## Contact & Support

**Support Email:** arjunahlawat83@gmail.com / anujpatwa30@gmail.com  
**Emergency Hotline:** 8708405576 / 7081792624

---

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite
- **ML**: scikit-learn, pandas, numpy
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: Flask-Login, Google OAuth2
- **QR Codes**: qrcode, jsQR
- **PDF Generation**: ReportLab
- **File Upload**: Werkzeug

---

## System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.8 or higher |
| RAM | 2GB minimum |
| Disk Space | 500MB |
| Browser | Chrome, Firefox, Edge (Modern) |
| Internet | For Google Login only |

---

## Troubleshooting

### App won't start
```bash
# Make sure you're in the correct directory
cd heartguard_new

# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Run the app
python run.py
```

### QR Code not displaying
- Patient ID might be missing in database
- Refresh browser (Ctrl+F5)
- Check `frontend/static/qrcodes/` folder permissions

### Cannot access patient record
- Ensure you're logged in as a **doctor**
- Patient ID must be a valid number
- Check that patient exists in database

### Camera not working in QR Scanner
- Browser needs permission to access webcam
- Allow camera access when prompted
- Check HTTPS (camera requires secure context in production)
- Use manual patient ID entry as fallback

---

## Future Enhancements

- [ ] WhatsApp/SMS notifications for file uploads
- [ ] Appointment scheduling system
- [ ] Mobile app for patients
- [ ] Advanced analytics dashboard
- [ ] Integration with hospital EMR systems
- [ ] Telemedicine video consultation
- [ ] Multi-language support
- [ ] Blockchain for report verification

---

## License

Proprietary - HeartGuard AI Medical Systems (2026)

---

## Version

**v3.2** - QR Code Patient Access System  
**Release Date:** April 10, 2026  
**Last Updated:** April 10, 2026
