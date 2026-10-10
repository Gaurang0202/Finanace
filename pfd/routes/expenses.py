"""
routes/expenses.py
-------------------
CRUD for expense entries, plus search/filter/sort/pagination. After every
add/edit, we re-check the relevant budget and drop a Notification if the
user has crossed the 80%/100% thresholds (see services usage below).
"""

from datetime import date
from calendar import monthrange

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models import Expense, Category, Budget, Notification
from forms import TransactionForm

expenses_bp = Blueprint("expenses", __name__)


def _populate_category_choices(form):
    cats = Category.query.filter_by(type="expense").order_by(Category.name).all()
    form.category_id.choices = [(c.id, c.name) for c in cats]


def _check_budget_alert(user_id: int, category_id: int, txn_date: date):
    """Fire an in-app notification if this category just crossed 80% or 100% of budget."""
    budget = Budget.query.filter_by(user_id=user_id, category_id=category_id, month=txn_date.month, year=txn_date.year).first()
    if not budget:
        return

    month_start = date(txn_date.year, txn_date.month, 1)
    month_end = date(txn_date.year, txn_date.month, monthrange(txn_date.year, txn_date.month)[1])
    spent = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.user_id == user_id, Expense.category_id == category_id,
        Expense.date.between(month_start, month_end),
    ).scalar()

    pct = (float(spent) / float(budget.amount)) * 100 if budget.amount else 0
    cat_name = budget.category.name if budget.category else "this category"

    if pct >= 100:
        db.session.add(Notification(
            user_id=user_id, title="Budget exceeded",
            message=f"You've exceeded your {cat_name} budget for {txn_date.strftime('%B %Y')}.",
            category="danger",
        ))
    elif pct >= 80:
        db.session.add(Notification(
            user_id=user_id, title="Budget warning",
            message=f"You've used {pct:.0f}% of your {cat_name} budget for {txn_date.strftime('%B %Y')}.",
            category="warning",
        ))


@expenses_bp.route("/expenses")
@login_required
def list_expenses():
    q = Expense.query.filter_by(user_id=current_user.id)

    search = request.args.get("search", "").strip()
    category_id = request.args.get("category", type=int)
    sort = request.args.get("sort", "date_desc")
    page = request.args.get("page", 1, type=int)

    if search:
        q = q.filter(Expense.description.ilike(f"%{search}%"))
    if category_id:
        q = q.filter(Expense.category_id == category_id)

    sort_map = {
        "date_desc": Expense.date.desc(),
        "date_asc": Expense.date.asc(),
        "amount_desc": Expense.amount.desc(),
        "amount_asc": Expense.amount.asc(),
    }
    q = q.order_by(sort_map.get(sort, Expense.date.desc()))

    pagination = q.paginate(page=page, per_page=10, error_out=False)
    categories = Category.query.filter_by(type="expense").order_by(Category.name).all()

    return render_template(
        "expenses.html", pagination=pagination, items=pagination.items,
        categories=categories, search=search, category_id=category_id, sort=sort
    )


@expenses_bp.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    form = TransactionForm()
    _populate_category_choices(form)

    if form.validate_on_submit():
        entry = Expense(
            user_id=current_user.id, category_id=form.category_id.data,
            amount=form.amount.data, description=form.description.data,
            date=form.date.data, payment_method=form.payment_method.data,
        )
        db.session.add(entry)
        db.session.flush()
        _check_budget_alert(current_user.id, entry.category_id, entry.date)

        if float(entry.amount) >= 10000:
            db.session.add(Notification(
                user_id=current_user.id, title="Large expense detected",
                message=f"A large expense of ₹{float(entry.amount):,.0f} was recorded in '{entry.category.name}'.",
                category="warning",
            ))

        db.session.commit()
        flash("Expense added successfully.", "success")
        return redirect(url_for("expenses.list_expenses"))

    return render_template("expense_form.html", form=form, mode="add")


@expenses_bp.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    entry = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    form = TransactionForm(obj=entry)
    _populate_category_choices(form)

    if form.validate_on_submit():
        entry.category_id = form.category_id.data
        entry.amount = form.amount.data
        entry.description = form.description.data
        entry.date = form.date.data
        entry.payment_method = form.payment_method.data
        db.session.commit()
        _check_budget_alert(current_user.id, entry.category_id, entry.date)
        db.session.commit()
        flash("Expense updated.", "success")
        return redirect(url_for("expenses.list_expenses"))

    return render_template("expense_form.html", form=form, mode="edit", entry=entry)


@expenses_bp.route("/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    entry = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash("Expense entry deleted.", "info")
    return redirect(url_for("expenses.list_expenses"))
