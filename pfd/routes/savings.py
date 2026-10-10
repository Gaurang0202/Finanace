"""
routes/savings.py
------------------
Savings goal CRUD, plus a quick "add contribution" action that updates
saved_amount and flags the goal complete (with a notification) once it's
fully funded.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import SavingsGoal, Notification
from forms import SavingsGoalForm

savings_bp = Blueprint("savings", __name__)


@savings_bp.route("/savings")
@login_required
def list_goals():
    goals = SavingsGoal.query.filter_by(user_id=current_user.id).order_by(SavingsGoal.created_at.desc()).all()
    return render_template("savings.html", goals=goals)


@savings_bp.route("/savings/add", methods=["GET", "POST"])
@login_required
def add_goal():
    form = SavingsGoalForm()
    if form.validate_on_submit():
        goal = SavingsGoal(
            user_id=current_user.id, title=form.title.data, icon=form.icon.data,
            target_amount=form.target_amount.data, saved_amount=form.saved_amount.data or 0,
            target_date=form.target_date.data,
        )
        if goal.saved_amount and float(goal.saved_amount) >= float(goal.target_amount):
            goal.is_completed = True
        db.session.add(goal)
        db.session.commit()
        flash("Savings goal created.", "success")
        return redirect(url_for("savings.list_goals"))

    return render_template("savings_form.html", form=form, mode="add")


@savings_bp.route("/savings/<int:goal_id>/edit", methods=["GET", "POST"])
@login_required
def edit_goal(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    form = SavingsGoalForm(obj=goal)
    if form.validate_on_submit():
        goal.title = form.title.data
        goal.icon = form.icon.data
        goal.target_amount = form.target_amount.data
        goal.saved_amount = form.saved_amount.data or 0
        goal.target_date = form.target_date.data
        goal.is_completed = float(goal.saved_amount) >= float(goal.target_amount)
        db.session.commit()
        flash("Savings goal updated.", "success")
        return redirect(url_for("savings.list_goals"))

    return render_template("savings_form.html", form=form, mode="edit", goal=goal)


@savings_bp.route("/savings/<int:goal_id>/contribute", methods=["POST"])
@login_required
def contribute(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    amount = request.form.get("amount", type=float)
    if amount and amount > 0:
        goal.saved_amount = float(goal.saved_amount) + amount
        was_completed = goal.is_completed
        if float(goal.saved_amount) >= float(goal.target_amount):
            goal.saved_amount = goal.target_amount
            goal.is_completed = True
            if not was_completed:
                db.session.add(Notification(
                    user_id=current_user.id, title="Goal achieved! \U0001F389",
                    message=f"You reached your '{goal.title}' savings goal.",
                    category="success",
                ))
        db.session.commit()
        flash("Contribution added.", "success")
    return redirect(url_for("savings.list_goals"))


@savings_bp.route("/savings/<int:goal_id>/delete", methods=["POST"])
@login_required
def delete_goal(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash("Savings goal deleted.", "info")
    return redirect(url_for("savings.list_goals"))
