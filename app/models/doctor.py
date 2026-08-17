"""
Doctor model — DynamoDB access functions for the Doctors table.
PK: DoctorID
"""
import uuid
from boto3.dynamodb.conditions import Attr
from app.models.db import get_table


def _table():
    return get_table("DOCTORS_TABLE")


def create_doctor(
    name: str,
    email: str,
    password_hash: str,
    specialization: str = "",
    phone: str = "",
) -> dict:
    """Create and persist a new doctor record. Returns the created item."""
    doctor_id = str(uuid.uuid4())
    item = {
        "DoctorID": doctor_id,
        "Name": name,
        "Email": email.lower().strip(),
        "PasswordHash": password_hash,
        "Specialization": specialization,
        "Phone": phone,
    }
    _table().put_item(Item=item)
    return item


def get_doctor(doctor_id: str) -> dict | None:
    """Fetch a doctor by their DoctorID."""
    response = _table().get_item(Key={"DoctorID": doctor_id})
    return response.get("Item")


def get_doctor_by_email(email: str) -> dict | None:
    """Scan for a doctor by email (used during login)."""
    response = _table().scan(
        FilterExpression=Attr("Email").eq(email.lower().strip())
    )
    items = response.get("Items", [])
    return items[0] if items else None


def get_all_doctors() -> list:
    """Return all doctors (for appointment booking dropdown)."""
    response = _table().scan()
    return response.get("Items", [])


def email_exists(email: str) -> bool:
    """Check whether a doctor email is already registered."""
    return get_doctor_by_email(email) is not None
