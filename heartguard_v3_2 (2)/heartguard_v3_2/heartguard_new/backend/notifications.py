import os
import smtplib
from email.message import EmailMessage
import mimetypes
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# ==========================================
# SETUP INSTRUCTIONS FOR THE USER
# ==========================================
# 1. Create a .env file in the 'ml project' folder.
# 2. Add the following variables to it:
#    EMAIL_USER=your_email@gmail.com
#    EMAIL_PASS=your_gmail_app_password
#    TWILIO_SID=your_twilio_account_sid
#    TWILIO_TOKEN=your_twilio_auth_token
#    TWILIO_WHATSAPP_NUMBER=+14155238886 (Twilio Sandbox Number)
# ==========================================

# Email Config
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')

# Twilio WhatsApp Config
TWILIO_SID = os.environ.get('TWILIO_SID')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')

# List of known placeholder values that should be treated as "not configured"
_PLACEHOLDERS = {
    'your_email@gmail.com', 'your_gmail_app_password_here',
    'your_twilio_account_sid_here', 'your_twilio_auth_token_here',
}

def _is_configured(value):
    """Check if a config value is set and not a placeholder."""
    return bool(value and value.strip() and value.strip() not in _PLACEHOLDERS)


def _normalize_whatsapp_number(phone_number):
    if not phone_number:
        return None
    normalized = ''.join(ch for ch in phone_number if ch.isdigit() or ch == '+')
    if normalized.startswith('00'):
        normalized = '+' + normalized[2:]
    if not normalized.startswith('+'):
        normalized = '+' + normalized
    return normalized


def generate_whatsapp_text(report, patient_name, doctor_name):
    risk_level = "HIGH RISK" if report.prediction_result == 1 else "LOW RISK"
    date_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    body = f"""*HEARTGUARD MEDICAL REPORT* 🩺
Hello {patient_name},

Your clinical assessment has been verified by *Dr. {doctor_name}*.

*REPORT DETAILS:*
• ID: #{report.id}
• Verified: {date_str}
• AI Assessment: *{risk_level}* 🚨
• Confidence: {round(report.probability * 100, 1)}%

*VITALS:*
• BP: {report.trestbps} mmHg
• Chol: {report.chol} mg/dl
• HR: {report.thalach} bpm

*ACTION:*
{"🚨 *URGENT*: Please schedule a follow-up appointment." if report.prediction_result == 1 else "✅ Continue maintaining a healthy lifestyle."}

_Your full detailed PDF report is attached below._"""
    return body

def send_email_notification(patient_email, subject, body, pdf_path=None):
    """Sends an email using Gmail SMTP."""
    if not _is_configured(EMAIL_USER) or not _is_configured(EMAIL_PASS):
        print("[EMAIL SKIP] Gmail not configured. Update .env with real credentials.")
        print(f"  To configure: Set EMAIL_USER and EMAIL_PASS in .env")
        print(f"  Guide: myaccount.google.com > Security > App Passwords")
        return False
        
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = patient_email

        if pdf_path and os.path.exists(pdf_path):
            ctype, encoding = mimetypes.guess_type(pdf_path)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            
            with open(pdf_path, 'rb') as fp:
                msg.add_attachment(fp.read(),
                                   maintype=maintype,
                                   subtype=subtype,
                                   filename=os.path.basename(pdf_path))

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {patient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_whatsapp_notification(patient_phone, body, media_url=None):
    """Sends a WhatsApp message using Twilio API."""
    if not _is_configured(TWILIO_SID) or not _is_configured(TWILIO_TOKEN) or not _is_configured(TWILIO_WHATSAPP_NUMBER):
        reason = "Twilio or WhatsApp sender number is not configured."
        print(f"[WHATSAPP SKIP] {reason} Update .env with real credentials.")
        return False, reason
    if not patient_phone:
        reason = "Patient phone number is not set on user profile."
        print(f"[WHATSAPP SKIP] {reason}")
        return False, reason
        
    try:
        normalized_phone = _normalize_whatsapp_number(patient_phone)
        if not normalized_phone:
            reason = f"Unable to normalize patient phone number: {patient_phone}"
            print(f"[WHATSAPP SKIP] {reason}")
            return False, reason

        client = Client(TWILIO_SID, TWILIO_TOKEN)
        # Twilio requires WhatsApp numbers to be prefixed with 'whatsapp:'
        to_number = f"whatsapp:{normalized_phone}"
        from_number = TWILIO_WHATSAPP_NUMBER
        if not from_number.startswith('whatsapp:'):
            from_number = f"whatsapp:{from_number}"
        
        msg_kwargs = {
            'body': body,
            'from_': from_number,
            'to': to_number
        }
        
        # Add media URL if provided (MUST BE PUBLICLY ACCESSIBLE URL)
        if media_url:
            msg_kwargs['media_url'] = [media_url]
            
        message = client.messages.create(**msg_kwargs)
        print(f"WhatsApp sent successfully: SID {message.sid}")
        return True, None
    except Exception as e:
        reason = str(e)
        print(f"Failed to send WhatsApp: {reason}")
        return False, reason

def dispatch_report_notifications(report, doctor, pdf_filepath=None, base_url=None, pdf_filename=None):
    """Main function called by app.py when a report is verified."""
    patient = report.patient
    body = generate_whatsapp_text(report, patient.name, doctor.name)
    subject = f"HeartGuard Assessment Verified - ID #{report.id}"
    
    # 1. Send Email with Attached PDF
    email_sent = send_email_notification(patient.email, subject, body, pdf_path=pdf_filepath)
    
    # 2. Send WhatsApp
    whatsapp_sent = False
    whatsapp_reason = None
    if patient.phone_number:
        # Fix: Prevent Twilio from trying to access local files when running on localhost
        if base_url and ("127.0.0.1" in base_url or "localhost" in base_url):
            print("[WHATSAPP] Running locally. Sending text only (Twilio cannot fetch local PDFs).")
            media_url = None
        else:
            media_url = f"{base_url}static/reports/{pdf_filename}" if base_url and pdf_filename else None
            
        print(f"Attempting WhatsApp with PDF Media URL: {media_url}")
        whatsapp_sent, whatsapp_reason = send_whatsapp_notification(patient.phone_number, body, media_url=media_url)
    else:
        whatsapp_reason = "Patient phone number is not set on the user profile."
        print(f"[WHATSAPP SKIP] {whatsapp_reason}")
        whatsapp_sent = False
        
    return email_sent, whatsapp_sent, whatsapp_reason