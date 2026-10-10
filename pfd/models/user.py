"""
models/user.py
---------------
User account model. Passwords are never stored in plain text -- they are
hashed with bcrypt before being persisted, and only the hash is stored.
"""

from datetime import datetime
import bcrypt
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255), default="default.png")
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    occupation = db.Column(db.String(120))
    onboarding_completed = db.Column(db.Boolean, default=False, nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)  # 'user' or 'admin'
    currency = db.Column(db.String(10), default="INR")
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationships (cascade delete keeps the DB consistent) -----------
    incomes = db.relationship("Income", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    budgets = db.relationship("Budget", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    savings_goals = db.relationship("SavingsGoal", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    settings = db.relationship("Settings", backref="user", uselist=False, cascade="all, delete-orphan")

    # --- Password helpers ---------------------------------------------
    def set_password(self, raw_password: str) -> None:
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        try:
            return bcrypt.checkpw(raw_password.encode("utf-8"), self.password_hash.encode("utf-8"))
        except (ValueError, TypeError):
            return False

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email}>"
