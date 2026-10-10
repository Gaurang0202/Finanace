from extensions import db, login_manager

from models.user import User
from models.category import Category
from models.income import Income
from models.expense import Expense
from models.budget import Budget
from models.savings_goal import SavingsGoal
from models.notification import Notification
from models.settings import Settings

__all__ = [
    "db",
    "User",
    "Category",
    "Income",
    "Expense",
    "Budget",
    "SavingsGoal",
    "Notification",
    "Settings",
]


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login calls this on every request to re-hydrate the logged-in user."""
    return User.query.get(int(user_id))
