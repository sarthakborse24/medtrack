"""
DiagnosisReport model — DynamoDB access functions for the DiagnosisReports table.
PK: ReportID  |  Attribute: AppointmentID
"""
import uuid
from boto3.dynamodb.conditions import Attr
from app.models.db import get_table


def _table():
    return get_table("DIAGNOSIS_REPORTS_TABLE")


def create_report(
    appointment_id: str,
    diagnosis: str,
    prescription: str = "",
    notes: str = "",
    doctor_id: str = "",
    patient_id: str = "",
) -> dict:
    """Create and persist a diagnosis report tied to an appointment."""
    report_id = str(uuid.uuid4())
    item = {
        "ReportID": report_id,
        "AppointmentID": appointment_id,
        "DoctorID": doctor_id,
        "PatientID": patient_id,
        "Diagnosis": diagnosis,
        "Prescription": prescription,
        "Notes": notes,
    }
    _table().put_item(Item=item)
    return item


def get_report(report_id: str) -> dict | None:
    """Fetch a diagnosis report by ReportID."""
    response = _table().get_item(Key={"ReportID": report_id})
    return response.get("Item")


def get_reports_by_appointment(appointment_id: str) -> list:
    """Return all diagnosis reports for a specific appointment."""
    response = _table().scan(
        FilterExpression=Attr("AppointmentID").eq(appointment_id)
    )
    return response.get("Items", [])


def get_reports_by_patient(patient_id: str) -> list:
    """Return all diagnosis reports for a specific patient (for medical history)."""
    response = _table().scan(
        FilterExpression=Attr("PatientID").eq(patient_id)
    )
    return response.get("Items", [])


def get_reports_by_doctor(doctor_id: str) -> list:
    """Return all diagnosis reports submitted by a specific doctor."""
    response = _table().scan(
        FilterExpression=Attr("DoctorID").eq(doctor_id)
    )
    return response.get("Items", [])
