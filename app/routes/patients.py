"""
MedTrack — Patient Blueprint
All routes require the patient role.
"""
from flask import Blueprint, render_template, session, abort
from app.decorators import patient_required
from app.models import appointment as appt_model
from app.models import diagnosis as diag_model
from app.models import doctor as doctor_model

patients_bp = Blueprint("patients", __name__, url_prefix="/patient")


@patients_bp.route("/dashboard")
@patient_required
def dashboard():
    patient_id = session["user_id"]
    appointments = appt_model.get_appointments_by_patient(patient_id)

    # Enrich with doctor names
    doctor_cache = {}
    for appt in appointments:
        did = appt.get("DoctorID", "")
        if did not in doctor_cache:
            doctor = doctor_model.get_doctor(did)
            doctor_cache[did] = doctor["Name"] if doctor else "Unknown"
        appt["DoctorName"] = doctor_cache[did]

    return render_template("patient/dashboard.html", appointments=appointments)


@patients_bp.route("/appointment/<appointment_id>")
@patient_required
def appointment_detail(appointment_id: str):
    """Show full detail of a single appointment including any diagnosis reports."""
    patient_id = session["user_id"]

    appt = appt_model.get_appointment(appointment_id)

    # Security: appointment must belong to this patient
    if not appt or appt.get("PatientID") != patient_id:
        abort(403)

    # Fetch doctor info
    doctor = doctor_model.get_doctor(appt.get("DoctorID", ""))
    appt["DoctorName"] = doctor["Name"] if doctor else "Unknown"
    appt["DoctorSpecialization"] = doctor.get("Specialization", "") if doctor else ""

    # Fetch diagnosis reports for this appointment
    reports = diag_model.get_reports_by_appointment(appointment_id)

    return render_template(
        "patient/appointment_detail.html",
        appt=appt,
        reports=reports,
        doctor=doctor,
    )


@patients_bp.route("/history")
@patient_required
def history():
    patient_id = session["user_id"]
    reports = diag_model.get_reports_by_patient(patient_id)
    appointments = appt_model.get_appointments_by_patient(patient_id)

    # Build appointment lookup for context
    appt_lookup = {a["AppointmentID"]: a for a in appointments}

    # Enrich reports with doctor names and appointment date
    doctor_cache = {}
    for report in reports:
        did = report.get("DoctorID", "")
        if did not in doctor_cache:
            doctor = doctor_model.get_doctor(did)
            doctor_cache[did] = doctor["Name"] if doctor else "Unknown"
        report["DoctorName"] = doctor_cache[did]

        appt = appt_lookup.get(report.get("AppointmentID", ""), {})
        report["AppointmentDate"] = appt.get("Date", "—")

    return render_template("patient/history.html", reports=reports)
