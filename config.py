"""
MedTrack Configuration
All settings are loaded from environment variables.
Never hardcode secrets here.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-CHANGE-IN-PROD")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    # AWS
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

    # DynamoDB Table Names
    PATIENTS_TABLE = os.environ.get("PATIENTS_TABLE", "MedTrack_Patients")
    DOCTORS_TABLE = os.environ.get("DOCTORS_TABLE", "MedTrack_Doctors")
    APPOINTMENTS_TABLE = os.environ.get("APPOINTMENTS_TABLE", "MedTrack_Appointments")
    DIAGNOSIS_REPORTS_TABLE = os.environ.get(
        "DIAGNOSIS_REPORTS_TABLE", "MedTrack_DiagnosisReports"
    )

    # SNS
    SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")

    # Admin secret for doctor registration
    ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")
