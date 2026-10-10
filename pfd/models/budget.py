from datetime import datetime
from extensions import db


class Budget(db.Model):
    """A monthly spending limit set by the user for one category."""

    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    month = db.Column(db.Integer, nullable=False)   # 1-12
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")

    __table_args__ = (
        db.UniqueConstraint("user_id", "category_id", "month", "year", name="uq_budget_user_cat_month_year"),
    )

    def __repr__(self):
        return f"<Budget {self.category.name if self.category else ''} {self.month}/{self.year}>"
