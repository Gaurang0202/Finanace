from datetime import datetime, date
from extensions import db


class Income(db.Model):
    __tablename__ = "income"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    description = db.Column(db.String(255))
    date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")

    def __repr__(self):
        return f"<Income {self.amount} on {self.date}>"
