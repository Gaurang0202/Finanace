"""
routes/profile.py
------------------
Profile page: personal info, financial summary, account settings
(password change, avatar upload, theme + notification preferences).
"""

import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import func

from extensions import db
from models import Income, Expense, Settings
from forms import ProfileForm, ChangePasswordForm

profile_bp = Blueprint("profile", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def index():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.currency = form.currency.data
        current_user.occupation = (form.occupation.data or "").strip() or None
        current_user.phone = (form.phone.data or "").strip() or None
        current_user.address = (form.address.data or "").strip() or None
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile.index"))

    total_income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(Income.user_id == current_user.id).scalar()
    total_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.user_id == current_user.id).scalar()

    if not current_user.settings:
        db.session.add(Settings(user_id=current_user.id))
        db.session.commit()

    return render_template(
        "profile.html", form=form, password_form=ChangePasswordForm(),
        total_income=float(total_income), total_expense=float(total_expense),
        total_savings=float(total_income) - float(total_expense),
    )


@profile_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password changed successfully.", "success")
    else:
        flash("Please correct the errors and try again.", "danger")
    return redirect(url_for("profile.index"))


@profile_bp.route("/profile/upload-picture", methods=["POST"])
@login_required
def upload_picture():
    file = request.files.get("profile_picture")
    if file and file.filename and _allowed_file(file.filename):
        os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = secure_filename(f"user_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}")
        file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
        current_user.profile_picture = filename
        db.session.commit()
        flash("Profile picture updated.", "success")
    else:
        flash("Please upload a valid image file (png, jpg, jpeg, gif, webp).", "danger")
    return redirect(url_for("profile.index"))


@profile_bp.route("/profile/toggle-theme", methods=["POST"])
@login_required
def toggle_theme():
    if not current_user.settings:
        db.session.add(Settings(user_id=current_user.id))
        db.session.flush()
    current_user.settings.theme = "dark" if current_user.settings.theme == "light" else "light"
    db.session.commit()
    return redirect(request.referrer or url_for("dashboard.index"))
