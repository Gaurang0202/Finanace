"""
services/insights.py
---------------------
Generates plain-English "AI-style" financial insights for a user by
analyzing their income/expense history with pandas. This is a transparent,
rule-based engine (mean/std anomaly detection, category ranking, trend
comparison) rather than a black-box model, which keeps it explainable,
free to run, and fast -- while still reading like personalized guidance.
"""

from datetime import date
from calendar import month_name
import pandas as pd

from models import Income, Expense


def _to_frame(records, extra_cols=None):
    rows = []
    for r in records:
        row = {
            "amount": float(r.amount),
            "date": r.date,
            "category": r.category.name if r.category else "Others",
        }
        if extra_cols:
            for c in extra_cols:
                row[c] = getattr(r, c, None)
        rows.append(row)
    return pd.DataFrame(rows)


def generate_insights(user_id: int) -> list[dict]:
    """
    Returns a list of insight dicts: {"type": "success|warning|info|danger", "icon": ..., "text": ...}
    """
    insights = []
    today = date.today()

    expenses = Expense.query.filter_by(user_id=user_id).all()
    incomes = Income.query.filter_by(user_id=user_id).all()

    if not expenses and not incomes:
        insights.append({
            "type": "info", "icon": "fa-circle-info",
            "text": "Add a few income and expense entries to unlock personalized insights."
        })
        return insights

    exp_df = _to_frame(expenses)
    inc_df = _to_frame(incomes)

    # --- Highest spending category (all-time) ---------------------------
    if not exp_df.empty:
        by_cat = exp_df.groupby("category")["amount"].sum().sort_values(ascending=False)
        top_cat, top_amt = by_cat.index[0], by_cat.iloc[0]
        share = top_amt / exp_df["amount"].sum() * 100
        insights.append({
            "type": "info", "icon": "fa-chart-pie",
            "text": f"'{top_cat}' is your biggest spending category, making up {share:.1f}% of total expenses (₹{top_amt:,.0f})."
        })

    # --- This month vs last month expense trend --------------------------
    if not exp_df.empty:
        exp_df["ym"] = exp_df["date"].apply(lambda d: (d.year, d.month))
        this_ym = (today.year, today.month)
        last_month_date = date(today.year - 1, 12, 1) if today.month == 1 else date(today.year, today.month - 1, 1)
        last_ym = (last_month_date.year, last_month_date.month)

        this_month_total = exp_df[exp_df["ym"] == this_ym]["amount"].sum()
        last_month_total = exp_df[exp_df["ym"] == last_ym]["amount"].sum()

        if last_month_total > 0:
            change = (this_month_total - last_month_total) / last_month_total * 100
            if change > 10:
                insights.append({
                    "type": "warning", "icon": "fa-arrow-trend-up",
                    "text": f"Spending is up {change:.1f}% compared to {month_name[last_month_date.month]}. Consider reviewing discretionary categories."
                })
            elif change < -10:
                insights.append({
                    "type": "success", "icon": "fa-arrow-trend-down",
                    "text": f"Great job! Spending dropped {abs(change):.1f}% compared to {month_name[last_month_date.month]}."
                })

    # --- Monthly savings rate --------------------------------------------
    if not inc_df.empty:
        inc_df["ym"] = inc_df["date"].apply(lambda d: (d.year, d.month))
        this_ym = (today.year, today.month)
        month_income = inc_df[inc_df["ym"] == this_ym]["amount"].sum()
        month_expense = exp_df[exp_df["ym"] == this_ym]["amount"].sum() if not exp_df.empty else 0

        if month_income > 0:
            savings_rate = (month_income - month_expense) / month_income * 100
            if savings_rate >= 20:
                insights.append({
                    "type": "success", "icon": "fa-piggy-bank",
                    "text": f"Your savings rate this month is {savings_rate:.1f}% -- healthy! Financial experts generally recommend 20%+."
                })
            elif savings_rate >= 0:
                insights.append({
                    "type": "warning", "icon": "fa-scale-balanced",
                    "text": f"Your savings rate this month is {savings_rate:.1f}%. Try trimming non-essential spending to push it above 20%."
                })
            else:
                insights.append({
                    "type": "danger", "icon": "fa-triangle-exclamation",
                    "text": f"You're spending {abs(savings_rate):.1f}% more than you earned this month. Review your budgets to get back on track."
                })

    # --- Expense anomaly detection (z-score) ------------------------------
    if len(exp_df) >= 5:
        mean, std = exp_df["amount"].mean(), exp_df["amount"].std()
        if std and std > 0:
            exp_df["z"] = (exp_df["amount"] - mean) / std
            anomalies = exp_df[exp_df["z"] > 2.5]
            if not anomalies.empty:
                biggest = anomalies.sort_values("z", ascending=False).iloc[0]
                insights.append({
                    "type": "warning", "icon": "fa-magnifying-glass-dollar",
                    "text": f"Unusually large expense detected: ₹{biggest['amount']:,.0f} in '{biggest['category']}' on {biggest['date']}."
                })

    # --- Suggested budget adjustment ----------------------------------
    if not exp_df.empty:
        by_cat = exp_df.groupby("category")["amount"].mean().sort_values(ascending=False)
        if len(by_cat) > 0:
            cat, avg = by_cat.index[0], by_cat.iloc[0]
            insights.append({
                "type": "info", "icon": "fa-lightbulb",
                "text": f"Consider setting a monthly budget of about ₹{avg * 1.1:,.0f} for '{cat}' based on your historical average."
            })

    return insights
