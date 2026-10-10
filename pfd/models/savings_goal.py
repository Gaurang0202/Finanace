from datetime import datetime
from extensions import db


class SavingsGoal(db.Model):
    __tablename__ = "savings_goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    icon = db.Column(db.String(50), default="fa-piggy-bank")
    target_amount = db.Column(db.Numeric(12, 2), nullable=False)
    saved_amount = db.Column(db.Numeric(12, 2), default=0)
    target_date = db.Column(db.Date, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def remaining_amount(self):
        return max(float(self.target_amount) - float(self.saved_amount), 0)

    @property
    def progress_percent(self):
        if not self.target_amount or float(self.target_amount) == 0:
            return 0
        pct = (float(self.saved_amount) / float(self.target_amount)) * 100
        return round(min(pct, 100), 1)

    def __repr__(self):
        return f"<SavingsGoal {self.title}>"
