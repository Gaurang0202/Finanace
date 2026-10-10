"""
models/category.py
-------------------
Categories are shared lookup values used by both Income and Expense records.
`type` distinguishes an income category ("income") from an expense
category ("expense"). Admins manage the global list; icons/colors drive
the dashboard's charts and badges.
"""

from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' | 'expense'
    icon = db.Column(db.String(50), default="fa-tag")
    color = db.Column(db.String(20), default="#6c5ce7")

    __table_args__ = (
        db.UniqueConstraint("name", "type", name="uq_category_name_type"),
    )

    def __repr__(self):
        return f"<Category {self.name} ({self.type})>"


DEFAULT_INCOME_CATEGORIES = [
    ("Salary", "fa-money-check-dollar", "#2ecc71"),
    ("Freelancing", "fa-laptop-code", "#00b894"),
    ("Business", "fa-briefcase", "#0984e3"),
    ("Investment", "fa-chart-line", "#6c5ce7"),
    ("Bonus", "fa-gift", "#fdcb6e"),
    ("Others", "fa-circle-plus", "#636e72"),
]

DEFAULT_EXPENSE_CATEGORIES = [
    ("Food", "fa-utensils", "#e17055"),
    ("Transport", "fa-car", "#0984e3"),
    ("Shopping", "fa-bag-shopping", "#e84393"),
    ("Entertainment", "fa-film", "#a29bfe"),
    ("Healthcare", "fa-briefcase-medical", "#d63031"),
    ("Education", "fa-graduation-cap", "#00cec9"),
    ("Bills", "fa-file-invoice-dollar", "#fdcb6e"),
    ("Travel", "fa-plane", "#0abde3"),
    ("Others", "fa-circle-minus", "#636e72"),
]
