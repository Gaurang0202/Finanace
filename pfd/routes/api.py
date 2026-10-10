"""
routes/api.py
--------------
Lightweight JSON endpoints consumed by Chart.js on the frontend. Keeping
these separate from the page routes means the same data can be re-used by
the dashboard, the analytics page, or a future mobile client.
"""

from datetime import date
from collections import OrderedDict, defaultdict

from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract

from extensions import db
from models import Income, Expense

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/charts/income-vs-expense")
@login_required
def income_vs_expense():
    """Last 6 months of income vs expense totals, for a grouped bar/line chart."""
    uid = current_user.id
    today = date.today()

    months = []
    y, m = today.year, today.month
    for _ in range(6):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months.reverse()

    inc_rows = db.session.query(
        extract("year", Income.date), extract("month", Income.date), func.sum(Income.amount)
    ).filter(Income.user_id == uid).group_by(extract("year", Income.date), extract("month", Income.date)).all()
    exp_rows = db.session.query(
        extract("year", Expense.date), extract("month", Expense.date), func.sum(Expense.amount)
    ).filter(Expense.user_id == uid).group_by(extract("year", Expense.date), extract("month", Expense.date)).all()

    inc_map = {(int(y_), int(m_)): float(t) for y_, m_, t in inc_rows}
    exp_map = {(int(y_), int(m_)): float(t) for y_, m_, t in exp_rows}

    labels = [date(y_, m_, 1).strftime("%b %Y") for y_, m_ in months]
    income_series = [inc_map.get((y_, m_), 0) for y_, m_ in months]
    expense_series = [exp_map.get((y_, m_), 0) for y_, m_ in months]

    return jsonify({"labels": labels, "income": income_series, "expense": expense_series})


@api_bp.route("/charts/spending-by-category")
@login_required
def spending_by_category():
    uid = current_user.id
    rows = db.session.query(Expense).filter_by(user_id=uid).all()
    totals = defaultdict(float)
    for e in rows:
        totals[e.category.name if e.category else "Others"] += float(e.amount)

    ordered = OrderedDict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))
    return jsonify({"labels": list(ordered.keys()), "values": list(ordered.values())})


@api_bp.route("/charts/savings-trend")
@login_required
def savings_trend():
    uid = current_user.id
    today = date.today()

    months = []
    y, m = today.year, today.month
    for _ in range(12):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months.reverse()

    inc_rows = db.session.query(
        extract("year", Income.date), extract("month", Income.date), func.sum(Income.amount)
    ).filter(Income.user_id == uid).group_by(extract("year", Income.date), extract("month", Income.date)).all()
    exp_rows = db.session.query(
        extract("year", Expense.date), extract("month", Expense.date), func.sum(Expense.amount)
    ).filter(Expense.user_id == uid).group_by(extract("year", Expense.date), extract("month", Expense.date)).all()

    inc_map = {(int(y_), int(m_)): float(t) for y_, m_, t in inc_rows}
    exp_map = {(int(y_), int(m_)): float(t) for y_, m_, t in exp_rows}

    labels = [date(y_, m_, 1).strftime("%b %Y") for y_, m_ in months]
    savings_series = [round(inc_map.get((y_, m_), 0) - exp_map.get((y_, m_), 0), 2) for y_, m_ in months]

    return jsonify({"labels": labels, "savings": savings_series})


@api_bp.route("/charts/yearly-comparison")
@login_required
def yearly_comparison():
    uid = current_user.id
    inc_rows = db.session.query(extract("year", Income.date), func.sum(Income.amount)).filter(
        Income.user_id == uid
    ).group_by(extract("year", Income.date)).all()
    exp_rows = db.session.query(extract("year", Expense.date), func.sum(Expense.amount)).filter(
        Expense.user_id == uid
    ).group_by(extract("year", Expense.date)).all()

    years = sorted(set([int(y) for y, _ in inc_rows] + [int(y) for y, _ in exp_rows]))
    inc_map = {int(y): float(t) for y, t in inc_rows}
    exp_map = {int(y): float(t) for y, t in exp_rows}

    return jsonify({
        "labels": [str(y) for y in years],
        "income": [inc_map.get(y, 0) for y in years],
        "expense": [exp_map.get(y, 0) for y in years],
    })
