"""
routes/admin.py
----------------
Admin-only views: user directory, global category management, and a
lightweight application log viewer. Every route is guarded by
@admin_required (see utils/decorators.py) on top of @login_required.
"""

import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models import User, Category, Income, Expense
from forms import CategoryForm
from utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def index():
    total_users = User.query.count()
    total_income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).scalar()
    total_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).scalar()
    return render_template(
        "admin/dashboard.html", total_users=total_users,
        total_income=float(total_income), total_expense=float(total_expense),
    )


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
    else:
        user.is_active_account = not user.is_active_account
        db.session.commit()
        flash(f"{user.email} is now {'active' if user.is_active_account else 'inactive'}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        existing = Category.query.filter_by(name=form.name.data.strip(), type=form.type.data).first()
        if existing:
            flash("That category already exists.", "danger")
        else:
            db.session.add(Category(
                name=form.name.data.strip(), type=form.type.data,
                icon=form.icon.data or "fa-tag", color=form.color.data or "#6c5ce7",
            ))
            db.session.commit()
            flash("Category added.", "success")
        return redirect(url_for("admin.categories"))

    income_cats = Category.query.filter_by(type="income").order_by(Category.name).all()
    expense_cats = Category.query.filter_by(type="expense").order_by(Category.name).all()
    return render_template("admin/categories.html", form=form, income_cats=income_cats, expense_cats=expense_cats)


@admin_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_category(category_id):
    cat = Category.query.get_or_404(category_id)
    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/logs")
@login_required
@admin_required
def logs():
    log_path = os.path.join(current_app.root_path, "database", "app.log")
    lines = []
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-200:]
    return render_template("admin/logs.html", lines=lines)
