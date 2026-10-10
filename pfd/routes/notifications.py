from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from extensions import db
from models import Notification

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications")
@login_required
def index():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template("notifications.html", items=items)


@notifications_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def mark_read(notif_id):
    n = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    n.is_read = True
    db.session.commit()
    return redirect(url_for("notifications.index"))


@notifications_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return redirect(url_for("notifications.index"))
