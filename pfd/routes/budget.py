"""
routes/budget.py
-----------------
Monthly budget planner: create a spending limit per category per month,
and see live spent/remaining/progress figures.
"""

from datetime import date
from calendar import monthrange

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models import Budget, Category, Expense
from forms import BudgetForm

budget_bp = Blueprint("budget", __name__)


@budget_bp.route("/budget", methods=["GET", "POST"])
@login_required
def index():
    today = date.today()
    form = BudgetForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(type="expense").order_by(Category.name).all()]
    if request.method == "GET":
        form.month.data = today.month
        form.year.data = today.year

    if form.validate_on_submit():
        existing = Budget.query.filter_by(
            user_id=current_user.id, category_id=form.category_id.data,
            month=form.month.data, year=form.year.data,
        ).first()
        if existing:
            existing.amount = form.amount.data
            flash("Budget updated for that category/month.", "success")
        else:
            db.session.add(Budget(
                user_id=current_user.id, category_id=form.category_id.data,
                amount=form.amount.data, month=form.month.data, year=form.year.data,
            ))
            flash("Budget created.", "success")
        db.session.commit()
        return redirect(url_for("budget.index", month=form.month.data, year=form.year.data))

    view_month = request.args.get("month", today.month, type=int)
    view_year = request.args.get("year", today.year, type=int)
    month_start = date(view_year, view_month, 1)
    month_end = date(view_year, view_month, monthrange(view_year, view_month)[1])

    budgets = Budget.query.filter_by(user_id=current_user.id, month=view_month, year=view_year).all()
    rows = []
    for b in budgets:
        spent = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == current_user.id, Expense.category_id == b.category_id,
            Expense.date.between(month_start, month_end),
        ).scalar()
        spent = float(spent)
        amount = float(b.amount)
        pct = round(min((spent / amount) * 100, 100), 1) if amount else 0
        rows.append({
            "id": b.id, "category": b.category.name if b.category else "Others",
            "icon": b.category.icon if b.category else "fa-tag",
            "budget": amount, "spent": spent, "remaining": max(amount - spent, 0),
            "percent": pct, "status": "danger" if pct >= 100 else ("warning" if pct >= 80 else "success"),
        })

    return render_template("budget.html", form=form, rows=rows, view_month=view_month, view_year=view_year)


@budget_bp.route("/budget/<int:budget_id>/delete", methods=["POST"])
@login_required
def delete_budget(budget_id):
    b = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first_or_404()
    db.session.delete(b)
    db.session.commit()
    flash("Budget removed.", "info")
    return redirect(url_for("budget.index"))
