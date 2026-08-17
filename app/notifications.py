"""
MedTrack — SNS Notification Module
Publishes event notifications to an SNS topic.
Topic ARN is read from the SNS_TOPIC_ARN environment variable.
Uses boto3's default credential chain — no hardcoded keys.
"""
import logging
import boto3
from botocore.exceptions import ClientError
from flask import current_app

logger = logging.getLogger(__name__)


def _sns_client():
    return boto3.client("sns", region_name=current_app.config["AWS_REGION"])


def _publish(subject: str, message: str) -> bool:
    """
    Publish a message to the configured SNS topic.
    Returns True on success, False on failure (non-fatal — app continues).
    """
    topic_arn = current_app.config.get("SNS_TOPIC_ARN", "")
    if not topic_arn:
        logger.warning("SNS_TOPIC_ARN is not configured — notification skipped.")
        print("[SNS] WARNING: SNS_TOPIC_ARN is empty — notification skipped.")
        return False

    try:
        response = _sns_client().publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message,
        )
        msg_id = response.get("MessageId", "?")
        logger.info("SNS notification sent: %s (MessageId: %s)", subject, msg_id)
        print(f"[SNS] SUCCESS: {subject} | MessageId: {msg_id}")
        return True
    except ClientError as e:
        logger.error("Failed to send SNS notification: %s", e)
        print(f"[SNS] ERROR: {e}")
        return False
    except Exception as e:
        logger.error("Unexpected error in SNS publish: %s", e)
        print(f"[SNS] UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return False


def send_appointment_notification(
    patient_name: str,
    doctor_name: str,
    date: str,
    time: str,
    appointment_id: str = "",
) -> bool:
    """Notify on a successful appointment booking."""
    subject = "MedTrack: New Appointment Booked"
    message = (
        f"A new appointment has been booked on MedTrack.\n\n"
        f"Patient : {patient_name}\n"
        f"Doctor  : {doctor_name}\n"
        f"Date    : {date}\n"
        f"Time    : {time}\n"
        f"Appt ID : {appointment_id}\n\n"
        f"Please log in to MedTrack to manage this appointment."
    )
    return _publish(subject, message)


def send_diagnosis_notification(
    patient_name: str,
    doctor_name: str,
    appointment_id: str = "",
) -> bool:
    """Notify on a new diagnosis report submission."""
    subject = "MedTrack: Diagnosis Report Submitted"
    message = (
        f"A diagnosis report has been submitted on MedTrack.\n\n"
        f"Patient : {patient_name}\n"
        f"Doctor  : {doctor_name}\n"
        f"Appt ID : {appointment_id}\n\n"
        f"Please log in to MedTrack to view your medical history."
    )
    return _publish(subject, message)
