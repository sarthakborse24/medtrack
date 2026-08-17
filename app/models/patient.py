"""
Patient model — DynamoDB access functions for the Patients table.
PK: PatientID
"""
import uuid
from boto3.dynamodb.conditions import Attr
from app.models.db import get_table


def _table():
    return get_table("PATIENTS_TABLE")


def create_patient(name: str, email: str, password_hash: str, phone: str = "") -> dict:
    """Create and persist a new patient record. Returns the created item."""
    patient_id = str(uuid.uuid4())
    item = {
        "PatientID": patient_id,
        "Name": name,
        "Email": email.lower().strip(),
        "PasswordHash": password_hash,
        "Phone": phone,
    }
    _table().put_item(Item=item)
    return item


def get_patient(patient_id: str) -> dict | None:
    """Fetch a patient by their PatientID."""
    response = _table().get_item(Key={"PatientID": patient_id})
    return response.get("Item")


def get_patient_by_email(email: str) -> dict | None:
    """Scan for a patient by email (used during login)."""
    response = _table().scan(
        FilterExpression=Attr("Email").eq(email.lower().strip())
    )
    items = response.get("Items", [])
    return items[0] if items else None


def email_exists(email: str) -> bool:
    """Check whether an email is already registered."""
    return get_patient_by_email(email) is not None
