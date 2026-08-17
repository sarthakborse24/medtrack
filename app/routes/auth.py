"""
MedTrack — Auth Blueprint
Handles patient registration, patient login, doctor login, doctor registration, and logout.
"""
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import patient as patient_model
from app.models import doctor as doctor_model

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


# ──────────────────────────────
# Home / Landing
# ──────────────────────────────

@auth_bp.route("/")
def home():
    return render_template("home.html")


# ──────────────────────────────
# Patient Registration
# ──────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("patients.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not name:
            errors.append("Full name is required.")
        if not _validate_email(email):
            errors.append("Please enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/register.html", name=name, email=email, phone=phone)

        if patient_model.email_exists(email):
            flash("An account with that email already exists.", "danger")
            return render_template("auth/register.html", name=name, email=email, phone=phone)

        password_hash = generate_password_hash(password)
        patient_model.create_patient(name=name, email=email, password_hash=password_hash, phone=phone)
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# ──────────────────────────────
# Patient Login
# ──────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session and session.get("role") == "patient":
        return redirect(url_for("patients.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("auth/login.html", email=email)

        user = patient_model.get_patient_by_email(email)
        if not user or not check_password_hash(user["PasswordHash"], password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", email=email)

        session.clear()
        session["user_id"] = user["PatientID"]
        session["role"] = "patient"
        session["name"] = user["Name"]
        flash(f"Welcome back, {user['Name']}!", "success")
        return redirect(url_for("patients.dashboard"))

    return render_template("auth/login.html")


# ──────────────────────────────
# Doctor Login
# ──────────────────────────────

@auth_bp.route("/doctor/login", methods=["GET", "POST"])
def doctor_login():
    if "user_id" in session and session.get("role") == "doctor":
        return redirect(url_for("doctors.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("auth/doctor_login.html", email=email)

        doctor = doctor_model.get_doctor_by_email(email)
        if not doctor or not check_password_hash(doctor["PasswordHash"], password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/doctor_login.html", email=email)

        session.clear()
        session["user_id"] = doctor["DoctorID"]
        session["role"] = "doctor"
        session["name"] = doctor["Name"]
        flash(f"Welcome, Dr. {doctor['Name']}!", "success")
        return redirect(url_for("doctors.dashboard"))

    return render_template("auth/doctor_login.html")


# ──────────────────────────────
# Doctor Registration (admin-gated)
# ──────────────────────────────

@auth_bp.route("/doctor/register", methods=["GET", "POST"])
def doctor_register():
    """
    Doctor self-registration protected by an ADMIN_SECRET code.
    Only someone who knows the secret (set in .env) can create a doctor account.
    """
    if "user_id" in session and session.get("role") == "doctor":
        return redirect(url_for("doctors.dashboard"))

    if request.method == "POST":
        admin_secret = request.form.get("admin_secret", "").strip()
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        specialization = request.form.get("specialization", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Validate admin secret first
        expected_secret = current_app.config.get("ADMIN_SECRET", "")
        if not expected_secret or admin_secret != expected_secret:
            flash("Invalid admin secret. Contact your administrator.", "danger")
            return render_template("auth/doctor_register.html", name=name, email=email,
                                   specialization=specialization, phone=phone)

        errors = []
        if not name:
            errors.append("Full name is required.")
        if not _validate_email(email):
            errors.append("Please enter a valid email address.")
        if not specialization:
            errors.append("Specialization is required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/doctor_register.html", name=name, email=email,
                                   specialization=specialization, phone=phone)

        if doctor_model.email_exists(email):
            flash("A doctor account with that email already exists.", "danger")
            return render_template("auth/doctor_register.html", name=name, email=email,
                                   specialization=specialization, phone=phone)

        password_hash = generate_password_hash(password)
        doctor_model.create_doctor(
            name=name,
            email=email,
            password_hash=password_hash,
            specialization=specialization,
            phone=phone,
        )
        flash(f"Doctor account created for Dr. {name}! Please log in.", "success")
        return redirect(url_for("auth.doctor_login"))

    return render_template("auth/doctor_register.html")


# ──────────────────────────────
# Logout
# ──────────────────────────────

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.home"))
