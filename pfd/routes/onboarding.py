"""
routes/onboarding.py
---------------------
Two tiny endpoints backing the interactive product tour (see
static/js/onboarding.js). Completion state is persisted on the User model
itself (not localStorage) so it follows the account across devices, per the
"use the existing user system" requirement.
"""

from flask import Blueprint, jsonify, redirect, url_for
from flask_login import login_required, current_user

from extensions import db

onboarding_bp = Blueprint("onboarding", __name__, url_prefix="/onboarding")


@onboarding_bp.route("/complete", methods=["POST"])
@login_required
def complete():
    current_user.onboarding_completed = True
    db.session.commit()
    return jsonify({"status": "ok"})


@onboarding_bp.route("/replay", methods=["POST"])
@login_required
def replay():
    """Used by the 'Replay Product Tour' link in Profile/Settings."""
    current_user.onboarding_completed = False
    db.session.commit()
    return redirect(url_for("dashboard.index"))
