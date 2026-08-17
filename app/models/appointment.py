"""
Appointment model — DynamoDB access functions for the Appointments table.
PK: AppointmentID  |  Attributes: PatientID, DoctorID
"""
import uuid
from boto3.dynamodb.conditions import Attr
from app.models.db import get_table


def _table():
    return get_table("APPOINTMENTS_TABLE")


def create_appointment(
    patient_id: str,
    doctor_id: str,
    date: str,
    time: str,
    reason: str = "",
) -> dict:
    """Create and persist a new appointment. Returns the created item."""
    appointment_id = str(uuid.uuid4())
    item = {
        "AppointmentID": appointment_id,
        "PatientID": patient_id,
        "DoctorID": doctor_id,
        "Date": date,
        "Time": time,
        "Reason": reason,
        "Status": "Pending",
    }
    _table().put_item(Item=item)
    return item


def get_appointment(appointment_id: str) -> dict | None:
    """Fetch an appointment by AppointmentID."""
    response = _table().get_item(Key={"AppointmentID": appointment_id})
    return response.get("Item")


def get_appointments_by_patient(patient_id: str) -> list:
    """Return all appointments for a specific patient."""
    response = _table().scan(
        FilterExpression=Attr("PatientID").eq(patient_id)
    )
    items = response.get("Items", [])
    return sorted(items, key=lambda x: (x.get("Date", ""), x.get("Time", "")), reverse=True)


def get_appointments_by_doctor(doctor_id: str) -> list:
    """Return all appointments for a specific doctor."""
    response = _table().scan(
        FilterExpression=Attr("DoctorID").eq(doctor_id)
    )
    items = response.get("Items", [])
    return sorted(items, key=lambda x: (x.get("Date", ""), x.get("Time", "")), reverse=True)


def update_appointment_status(appointment_id: str, status: str) -> None:
    """Update the status of an appointment ('Pending', 'Confirmed', 'Completed', 'Cancelled')."""
    _table().update_item(
        Key={"AppointmentID": appointment_id},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "Status"},
        ExpressionAttributeValues={":s": status},
    )


def appointment_belongs_to_doctor(appointment_id: str, doctor_id: str) -> bool:
    """Verify that the appointment belongs to the given doctor."""
    appt = get_appointment(appointment_id)
    return appt is not None and appt.get("DoctorID") == doctor_id


def appointment_belongs_to_patient(appointment_id: str, patient_id: str) -> bool:
    """Verify that the appointment belongs to the given patient."""
    appt = get_appointment(appointment_id)
    return appt is not None and appt.get("PatientID") == patient_id
