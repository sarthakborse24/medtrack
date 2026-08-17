"""
MedTrack — Auth decorators for role-based access control.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, abort


def login_required(f):
    """Require any authenticated user (patient or doctor)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def patient_required(f):
    """Require the current user to be a patient."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("role") != "patient":
            abort(403)
        return f(*args, **kwargs)
    return decorated


def doctor_required(f):
    """Require the current user to be a doctor."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in.", "warning")
            return redirect(url_for("auth.doctor_login"))
        if session.get("role") != "doctor":
            abort(403)
        return f(*args, **kwargs)
    return decorated
