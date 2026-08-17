"""
MedTrack — Doctor Blueprint
All routes require the doctor role.
Doctors can only access records of their own patients.
"""
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, abort,
)
from app.decorators import doctor_required
from app.models import appointment as appt_model
from app.models import diagnosis as diag_model
from app.models import patient as patient_model
from app.models import doctor as doctor_model
from app.notifications import send_diagnosis_notification

doctors_bp = Blueprint("doctors", __name__, url_prefix="/doctor")


@doctors_bp.route("/dashboard")
@doctor_required
def dashboard():
    doctor_id = session["user_id"]
    appointments = appt_model.get_appointments_by_doctor(doctor_id)

    # Enrich with patient names
    patient_cache = {}
    for appt in appointments:
        pid = appt.get("PatientID", "")
        if pid not in patient_cache:
            pat = patient_model.get_patient(pid)
            patient_cache[pid] = pat["Name"] if pat else "Unknown"
        appt["PatientName"] = patient_cache[pid]

    return render_template("doctor/dashboard.html", appointments=appointments)


@doctors_bp.route("/patient/<patient_id>/history")
@doctor_required
def patient_history(patient_id: str):
    """
    A doctor can only view a patient's history if they have at least
    one appointment with that patient.
    """
    doctor_id = session["user_id"]
    doctor_appointments = appt_model.get_appointments_by_doctor(doctor_id)
    patient_ids = {a["PatientID"] for a in doctor_appointments}

    if patient_id not in patient_ids:
        abort(403)  # Doctor has no appointments with this patient

    patient = patient_model.get_patient(patient_id)
    if not patient:
        abort(404)

    reports = diag_model.get_reports_by_patient(patient_id)

    # Enrich with appointment date
    patient_appointments = appt_model.get_appointments_by_patient(patient_id)
    appt_lookup = {a["AppointmentID"]: a for a in patient_appointments}
    for report in reports:
        appt = appt_lookup.get(report.get("AppointmentID", ""), {})
        report["AppointmentDate"] = appt.get("Date", "—")

    return render_template(
        "doctor/patient_history.html",
        patient=patient,
        reports=reports,
    )


@doctors_bp.route("/diagnosis/<appointment_id>", methods=["GET", "POST"])
@doctor_required
def submit_diagnosis(appointment_id: str):
    """Submit a diagnosis report for an appointment."""
    doctor_id = session["user_id"]

    # Verify ownership
    if not appt_model.appointment_belongs_to_doctor(appointment_id, doctor_id):
        abort(403)

    appointment = appt_model.get_appointment(appointment_id)
    patient = patient_model.get_patient(appointment["PatientID"])
    doctor = doctor_model.get_doctor(doctor_id)

    if request.method == "POST":
        diagnosis = request.form.get("diagnosis", "").strip()
        prescription = request.form.get("prescription", "").strip()
        notes = request.form.get("notes", "").strip()

        if not diagnosis:
            flash("Diagnosis is required.", "danger")
            return render_template(
                "doctor/diagnosis_form.html",
                appointment=appointment,
                patient=patient,
            )

        diag_model.create_report(
            appointment_id=appointment_id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes,
            doctor_id=doctor_id,
            patient_id=appointment["PatientID"],
        )

        # Update appointment status to Completed
        appt_model.update_appointment_status(appointment_id, "Completed")

        # Send SNS notification (non-fatal)
        send_diagnosis_notification(
            patient_name=patient["Name"] if patient else "Patient",
            doctor_name=doctor["Name"] if doctor else "Doctor",
            appointment_id=appointment_id,
        )

        flash("Diagnosis report submitted successfully.", "success")
        return redirect(url_for("doctors.dashboard"))

    return render_template(
        "doctor/diagnosis_form.html",
        appointment=appointment,
        patient=patient,
    )


@doctors_bp.route("/appointment/<appointment_id>/status", methods=["POST"])
@doctor_required
def update_status(appointment_id: str):
    """Allow doctor to update an appointment status."""
    doctor_id = session["user_id"]
    if not appt_model.appointment_belongs_to_doctor(appointment_id, doctor_id):
        abort(403)

    new_status = request.form.get("status", "").strip()
    valid_statuses = {"Pending", "Confirmed", "Completed", "Cancelled"}
    if new_status not in valid_statuses:
        flash("Invalid status.", "danger")
        return redirect(url_for("doctors.dashboard"))

    appt_model.update_appointment_status(appointment_id, new_status)
    flash(f"Appointment status updated to '{new_status}'.", "success")
    return redirect(url_for("doctors.dashboard"))
