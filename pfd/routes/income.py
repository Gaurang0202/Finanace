"""
routes/income.py
-----------------
CRUD for income entries, plus search/filter/sort/pagination on the listing
page (mirrors the requirements' Transactions feature, scoped to income).
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import Income, Category
from forms import TransactionForm

income_bp = Blueprint("income", __name__)


def _populate_category_choices(form):
    cats = Category.query.filter_by(type="income").order_by(Category.name).all()
    form.category_id.choices = [(c.id, c.name) for c in cats]


@income_bp.route("/income")
@login_required
def list_income():
    q = Income.query.filter_by(user_id=current_user.id)

    search = request.args.get("search", "").strip()
    category_id = request.args.get("category", type=int)
    sort = request.args.get("sort", "date_desc")
    page = request.args.get("page", 1, type=int)

    if search:
        q = q.filter(Income.description.ilike(f"%{search}%"))
    if category_id:
        q = q.filter(Income.category_id == category_id)

    sort_map = {
        "date_desc": Income.date.desc(),
        "date_asc": Income.date.asc(),
        "amount_desc": Income.amount.desc(),
        "amount_asc": Income.amount.asc(),
    }
    q = q.order_by(sort_map.get(sort, Income.date.desc()))

    pagination = q.paginate(page=page, per_page=10, error_out=False)
    categories = Category.query.filter_by(type="income").order_by(Category.name).all()

    return render_template(
        "income.html", pagination=pagination, items=pagination.items,
        categories=categories, search=search, category_id=category_id, sort=sort
    )


@income_bp.route("/income/add", methods=["GET", "POST"])
@login_required
def add_income():
    form = TransactionForm()
    _populate_category_choices(form)
    del form.payment_method  # not relevant for income

    if form.validate_on_submit():
        entry = Income(
            user_id=current_user.id, category_id=form.category_id.data,
            amount=form.amount.data, description=form.description.data, date=form.date.data,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Income added successfully.", "success")
        return redirect(url_for("income.list_income"))

    return render_template("income_form.html", form=form, mode="add")


@income_bp.route("/income/<int:income_id>/edit", methods=["GET", "POST"])
@login_required
def edit_income(income_id):
    entry = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    form = TransactionForm(obj=entry)
    _populate_category_choices(form)
    del form.payment_method

    if form.validate_on_submit():
        entry.category_id = form.category_id.data
        entry.amount = form.amount.data
        entry.description = form.description.data
        entry.date = form.date.data
        db.session.commit()
        flash("Income updated.", "success")
        return redirect(url_for("income.list_income"))

    return render_template("income_form.html", form=form, mode="edit", entry=entry)


@income_bp.route("/income/<int:income_id>/delete", methods=["POST"])
@login_required
def delete_income(income_id):
    entry = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash("Income entry deleted.", "info")
    return redirect(url_for("income.list_income"))
