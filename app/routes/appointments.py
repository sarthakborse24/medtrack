"""
MedTrack — Appointments Blueprint
"""
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session,
)
from app.decorators import patient_required
from app.models import doctor as doctor_model
from app.models import appointment as appt_model
from app.models import patient as patient_model
from app.notifications import send_appointment_notification

appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")


@appointments_bp.route("/book", methods=["GET", "POST"])
@patient_required
def book():
    doctors = doctor_model.get_all_doctors()

    if request.method == "POST":
        doctor_id = request.form.get("doctor_id", "").strip()
        date = request.form.get("date", "").strip()
        time = request.form.get("time", "").strip()
        reason = request.form.get("reason", "").strip()

        errors = []
        if not doctor_id:
            errors.append("Please select a doctor.")
        if not date:
            errors.append("Please select a date.")
        if not time:
            errors.append("Please select a time.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "appointments/book.html",
                doctors=doctors,
                selected_doctor=doctor_id,
                selected_date=date,
                selected_time=time,
                reason=reason,
            )

        # Verify doctor exists
        doctor = doctor_model.get_doctor(doctor_id)
        if not doctor:
            flash("Selected doctor not found.", "danger")
            return render_template("appointments/book.html", doctors=doctors)

        patient_id = session["user_id"]
        patient = patient_model.get_patient(patient_id)

        appt = appt_model.create_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=date,
            time=time,
            reason=reason,
        )

        # Send SNS notification (non-fatal)
        send_appointment_notification(
            patient_name=patient["Name"] if patient else "Patient",
            doctor_name=doctor["Name"],
            date=date,
            time=time,
            appointment_id=appt["AppointmentID"],
        )

        flash("Appointment booked successfully!", "success")
        return redirect(url_for("patients.dashboard"))

    return render_template("appointments/book.html", doctors=doctors)
