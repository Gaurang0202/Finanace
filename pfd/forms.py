"""
forms.py
--------
Flask-WTF forms. Using WTForms gives us CSRF protection automatically
(via Flask-WTF) plus server-side validation, so every POST route is
protected against forged submissions and malformed input.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, DecimalField, SelectField, DateField,
    TextAreaField, BooleanField, IntegerField
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional


class RegisterForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=180)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, message="Use at least 8 characters.")])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )


class TransactionForm(FlaskForm):
    """Used for both Income and Expense entries; the route decides which model to save to."""
    amount = DecimalField("Amount", validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    description = StringField("Description", validators=[Optional(), Length(max=255)])
    date = DateField("Date", validators=[DataRequired()])
    payment_method = SelectField(
        "Payment Method",
        choices=[("Cash", "Cash"), ("Card", "Card"), ("UPI", "UPI"), ("Bank Transfer", "Bank Transfer"), ("Other", "Other")],
        validators=[Optional()]
    )


class BudgetForm(FlaskForm):
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    amount = DecimalField("Budget Amount", validators=[DataRequired(), NumberRange(min=1)], places=2)
    month = SelectField("Month", coerce=int, validators=[DataRequired()], choices=[(i, i) for i in range(1, 13)])
    year = IntegerField("Year", validators=[DataRequired(), NumberRange(min=2000, max=2100)])


class SavingsGoalForm(FlaskForm):
    title = StringField("Goal Title", validators=[DataRequired(), Length(max=120)])
    icon = SelectField(
        "Icon",
        choices=[
            ("fa-piggy-bank", "Piggy Bank"), ("fa-laptop", "Laptop"), ("fa-plane", "Vacation"),
            ("fa-car", "Car"), ("fa-house", "House"), ("fa-shield-heart", "Emergency Fund"),
        ]
    )
    target_amount = DecimalField("Target Amount", validators=[DataRequired(), NumberRange(min=1)], places=2)
    saved_amount = DecimalField("Already Saved", validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    target_date = DateField("Target Date", validators=[Optional()])


class ProfileForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    occupation = StringField("Occupation", validators=[Optional(), Length(max=120)])
    phone = StringField("Phone Number", validators=[Optional(), Length(max=30)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    currency = SelectField("Currency", choices=[("INR", "INR (₹)"), ("USD", "USD ($)"), ("EUR", "EUR (€)"), ("GBP", "GBP (£)")])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField("New Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirm New Password", validators=[DataRequired(), EqualTo("new_password")])


class CategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[DataRequired(), Length(max=80)])
    type = SelectField("Type", choices=[("income", "Income"), ("expense", "Expense")])
    icon = StringField("Icon (Font Awesome class)", default="fa-tag")
    color = StringField("Color (hex)", default="#6c5ce7")
