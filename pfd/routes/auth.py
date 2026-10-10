"""
routes/auth.py
---------------
Registration, login, logout and a simple forgot-password flow.
Passwords are hashed via User.set_password (bcrypt); sessions are handled
by Flask-Login (login_user / logout_user / login_required).
"""

from datetime import datetime, timedelta
import secrets

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db, mail
from models import User, Settings
from forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from services.demo_seed import PRESENTATION_EMAIL

auth_bp = Blueprint("auth", __name__)

# In-memory reset-token store (fine for a project of this scope).
# For real production use, persist tokens in the DB with an expiry column.
_reset_tokens: dict[str, tuple[int, datetime]] = {}


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        submitted_email = form.email.data.lower().strip()

        if submitted_email == PRESENTATION_EMAIL:
            flash("This email address is reserved and cannot be used to register.", "danger")
            return render_template("register.html", form=form)

        existing = User.query.filter_by(email=submitted_email).first()
        if existing:
            flash("An account with that email already exists.", "danger")
            return render_template("register.html", form=form)

        user = User(name=form.name.data.strip(), email=form.email.data.lower().strip())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # get user.id before commit
        db.session.add(Settings(user_id=user.id))
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data) and user.is_active_account:
            login_user(user, remember=form.remember.data)
            flash(f"Welcome back, {user.name.split(' ')[0]}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        # Always show the same message, whether or not the account exists,
        # so we don't leak which emails are registered.
        if user:
            token = secrets.token_urlsafe(32)
            _reset_tokens[token] = (user.id, datetime.utcnow() + timedelta(hours=1))
            reset_link = url_for("auth.reset_password", token=token, _external=True)
            try:
                from flask_mail import Message
                msg = Message(
                    subject="Reset your Personal Finance Dashboard password",
                    recipients=[user.email],
                    body=f"Click the link to reset your password (valid for 1 hour): {reset_link}",
                )
                mail.send(msg)
            except Exception:
                # Mail server may not be configured in dev; surface the link instead.
                flash(f"Email not configured. Use this reset link: {reset_link}", "warning")
        flash("If that email is registered, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    entry = _reset_tokens.get(token)
    if not entry or entry[1] < datetime.utcnow():
        flash("That reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.get(entry[0])
        if user:
            user.set_password(form.password.data)
            db.session.commit()
            _reset_tokens.pop(token, None)
            flash("Password updated. Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form)
