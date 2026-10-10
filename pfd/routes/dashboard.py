"""
routes/dashboard.py
--------------------
The main landing page after login: balance, income/expense totals,
budget status, recent transactions, goals and AI insights all in one view.
"""

from datetime import date
from calendar import monthrange

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models import Income, Expense, Budget, SavingsGoal, Notification
from services.insights import generate_insights

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month, monthrange(today.year, today.month)[1])

    uid = current_user.id

    total_income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(
        Income.user_id == uid, Income.date.between(month_start, month_end)
    ).scalar()

    total_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == uid, Expense.date.between(month_start, month_end)
    ).scalar()

    all_time_income = db.session.query(func.coalesce(func.sum(Income.amount), 0)).filter(Income.user_id == uid).scalar()
    all_time_expense = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.user_id == uid).scalar()
    total_balance = float(all_time_income) - float(all_time_expense)

    savings_this_month = float(total_income) - float(total_expense)
    savings_rate = round((savings_this_month / float(total_income)) * 100, 1) if float(total_income) > 0 else 0

    # --- Budget status for the current month --------------------------
    budgets = Budget.query.filter_by(user_id=uid, month=today.month, year=today.year).all()
    budget_rows = []
    for b in budgets:
        spent = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == uid,
            Expense.category_id == b.category_id,
            Expense.date.between(month_start, month_end),
        ).scalar()
        spent = float(spent)
        amount = float(b.amount)
        pct = round(min((spent / amount) * 100, 100), 1) if amount else 0
        budget_rows.append({
            "category": b.category.name if b.category else "Others",
            "budget": amount,
            "spent": spent,
            "remaining": max(amount - spent, 0),
            "percent": pct,
            "status": "danger" if pct >= 100 else ("warning" if pct >= 80 else "success"),
        })

    # --- Recent transactions (combined) -----------------------------
    recent_income = Income.query.filter_by(user_id=uid).order_by(Income.date.desc(), Income.id.desc()).limit(5).all()
    recent_expense = Expense.query.filter_by(user_id=uid).order_by(Expense.date.desc(), Expense.id.desc()).limit(5).all()
    recent = sorted(
        [{"type": "income", "obj": i} for i in recent_income] + [{"type": "expense", "obj": e} for e in recent_expense],
        key=lambda r: (r["obj"].date, r["obj"].id), reverse=True
    )[:8]

    goals = SavingsGoal.query.filter_by(user_id=uid).order_by(SavingsGoal.created_at.desc()).limit(4).all()
    notifications = Notification.query.filter_by(user_id=uid, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    insights = generate_insights(uid)[:4]

    return render_template(
        "dashboard.html",
        total_balance=total_balance,
        total_income=float(total_income),
        total_expense=float(total_expense),
        savings_this_month=savings_this_month,
        savings_rate=savings_rate,
        budget_rows=budget_rows,
        recent=recent,
        goals=goals,
        notifications=notifications,
        insights=insights,
        month_label=today.strftime("%B %Y"),
    )
