from extensions import db


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    theme = db.Column(db.String(10), default="light")  # 'light' | 'dark'
    email_monthly_report = db.Column(db.Boolean, default=False)
    budget_alerts = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Settings user={self.user_id} theme={self.theme}>"
