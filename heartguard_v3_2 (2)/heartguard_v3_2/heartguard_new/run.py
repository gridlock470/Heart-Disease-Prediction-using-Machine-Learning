"""
HeartGuard AI — Application Entry Point
========================================
Run this file to start the Flask server:
    python run.py
"""
import os
import sys

# Add backend directory to Python path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_DIR, 'backend'))

from app import app
from models import db

if __name__ == '__main__':
    # Ensure instance directory exists
    os.makedirs(os.path.join(PROJECT_DIR, 'instance'), exist_ok=True)

    # Create database tables
    with app.app_context():
        db.create_all()
        print("[OK] Database tables ready.")

    print("\n" + "=" * 50)
    print("  HeartGuard AI — Server Starting")
    print("  http://127.0.0.1:5000")
    print("=" * 50 + "\n")

    app.run(debug=True)
