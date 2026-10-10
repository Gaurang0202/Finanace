"""
services/demo_seed.py
----------------------
Creates a single fully-populated "presentation" account the first time the
app starts (and never again, since it's guarded by a lookup on
PRESENTATION_EMAIL). This account exists purely so the project can be
demoed with a dashboard that looks like it's had a full year of real use --
it is NOT reachable through the public registration form (see
routes/auth.py, which blocks this email explicitly).

Amounts for the most recent month are pinned close to specific presentation
figures (income/expense/savings-rate) so the dashboard's headline numbers
look intentional; the other eleven months use a seeded random generator so
the data is varied but still reproducible if the account is ever rebuilt.
"""

import random
from calendar import monthrange
from datetime import date, timedelta, datetime

from extensions import db
from models import (
    User, Category, Income, Expense, Budget, SavingsGoal, Notification, Settings
)

PRESENTATION_EMAIL = "presentation@wealthr.com"
PRESENTATION_PASSWORD = "Presentation@123"

_RNG_SEED = 20260101  # fixed seed -> reproducible demo data if ever regenerated


def _get_or_create_category(name: str, type_: str, icon: str, color: str) -> Category:
    cat = Category.query.filter_by(name=name, type=type_).first()
    if not cat:
        cat = Category(name=name, type=type_, icon=icon, color=color)
        db.session.add(cat)
        db.session.flush()
    return cat


def _month_sequence(end_date: date, count: int = 12):
    """Return `count` (year, month) tuples ending at end_date's month, oldest first."""
    months = []
    y, m = end_date.year, end_date.month
    for _ in range(count):
        months.append((y, m))
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    months.reverse()
    return months


def seed_presentation_account(app):
    """Create + populate the demo account. Safe to call on every startup --
    it's a no-op once the account already exists."""
    with app.app_context():
        existing = User.query.filter_by(email=PRESENTATION_EMAIL).first()
        if existing:
            # Account exists: never regenerate healthy data, but repair anything
            # that would make the demo unusable (deactivated, password changed,
            # missing settings, or data wiped out).
            income_n = Income.query.filter_by(user_id=existing.id).count()
            expense_n = Expense.query.filter_by(user_id=existing.id).count()
            if income_n >= 50 and expense_n >= 350:
                changed = False
                if not existing.is_active_account:
                    existing.is_active_account = True; changed = True
                if existing.role != "user":
                    existing.role = "user"; changed = True
                if not existing.check_password(PRESENTATION_PASSWORD):
                    existing.set_password(PRESENTATION_PASSWORD); changed = True
                if not existing.settings:
                    db.session.add(Settings(user_id=existing.id, theme="dark")); changed = True
                if changed:
                    db.session.commit()
                    app.logger.info("Presentation account repaired (credentials/status).")
                return
            # Data was deleted or is incomplete -> remove the shell and rebuild below.
            app.logger.warning("Presentation account data incomplete; rebuilding.")
            db.session.delete(existing)
            db.session.commit()

        app.logger.info("Creating presentation demo account...")
        rng = random.Random(_RNG_SEED)

        # --- Account -----------------------------------------------------
        user = User(
            name="John Anderson",
            email=PRESENTATION_EMAIL,
            occupation="Senior Software Engineer",
            phone="+91 98765 43210",
            address="Koramangala, Bengaluru, Karnataka, India",
            currency="INR",
            onboarding_completed=True,  # demo account skips the first-run tour
        )
        user.set_password(PRESENTATION_PASSWORD)
        db.session.add(user)
        db.session.flush()  # need user.id below

        settings = Settings(user_id=user.id, theme="dark", email_monthly_report=True, budget_alerts=True)
        db.session.add(settings)

        # --- Categories (reuse the defaults; add a couple of income types
        #     the default seed list doesn't include) --------------------
        income_cats = {c.name: c for c in Category.query.filter_by(type="income").all()}
        for name, icon, color in [("Cashback", "fa-tags", "#00cec9"), ("Interest", "fa-percent", "#0984e3")]:
            income_cats[name] = _get_or_create_category(name, "income", icon, color)

        expense_cats = {c.name: c for c in Category.query.filter_by(type="expense").all()}
        db.session.flush()

        today = date.today()
        months = _month_sequence(today, 12)          # oldest -> newest, 12 entries
        current_ym = months[-1]

        # =================================================================
        # INCOME
        # =================================================================
        income_rows = []

        for (y, m) in months:
            income_rows.append((y, m, 1, income_cats["Salary"].id, 95000, "Monthly Salary Credit"))

        freelance_notes = ["Freelance Web Project", "UI Consulting Gig", "Freelance API Integration", "Weekend Freelance Project"]
        for _ in range(rng.randint(4, 6)):
            y, m = rng.choice(months)
            income_rows.append((y, m, rng.randint(2, 27), income_cats["Freelancing"].id, rng.randint(8000, 25000), rng.choice(freelance_notes)))

        bonus_y, bonus_m = months[rng.randint(0, 5)]
        income_rows.append((bonus_y, bonus_m, rng.randint(1, 28), income_cats["Bonus"].id, 120000, "Annual Performance Bonus"))

        for _ in range(rng.randint(5, 8)):
            y, m = rng.choice(months)
            income_rows.append((y, m, rng.randint(1, 28), income_cats["Investment"].id, rng.randint(2000, 15000), "Mutual Fund Dividend Payout"))

        cashback_notes = ["Amazon Pay Cashback", "Credit Card Cashback", "Flipkart Cashback Offer", "Google Pay Rewards"]
        for (y, m) in months:
            for _ in range(rng.randint(1, 2)):
                income_rows.append((y, m, rng.randint(1, 28), income_cats["Cashback"].id, rng.randint(100, 800), rng.choice(cashback_notes)))

        for (y, m) in months:
            income_rows.append((y, m, rng.randint(1, 5), income_cats["Interest"].id, rng.randint(500, 2000), "Savings Account Interest"))

        current_month_income_target = 112500
        current_rows = [r for r in income_rows if (r[0], r[1]) == current_ym]
        current_total = sum(r[4] for r in current_rows)
        adjustment = current_month_income_target - current_total
        if adjustment != 0:
            income_rows.append((
                current_ym[0], current_ym[1], 28, income_cats["Investment"].id,
                adjustment, "Other Income Adjustment"
            ))

        for (y, m, d, cat_id, amount, desc) in income_rows:
            db.session.add(Income(user_id=user.id, category_id=cat_id, amount=amount, description=desc, date=date(y, m, d)))

        # =================================================================
        # EXPENSES
        # =================================================================
        expense_items = {
            "Bills": [
                ("Electricity Bill - BESCOM", 1200, 3200, "monthly"),
                ("Water Bill - BWSSB", 300, 700, "monthly"),
                ("Airtel Fiber Internet", 999, 1499, "monthly"),
                ("Jio Mobile Recharge", 299, 599, "monthly"),
            ],
            "Transport": [
                ("Indian Oil Petrol", 800, 2000, "multi"),
                ("HP Petrol Pump", 800, 2000, "multi"),
                ("Uber Ride", 150, 600, "multi"),
                ("Ola Cab Booking", 150, 550, "multi"),
                ("Namma Metro Card Recharge", 100, 300, "multi"),
            ],
            "Food": [
                ("Reliance Fresh Groceries", 1500, 4000, "multi"),
                ("BigBasket Order", 1200, 3500, "multi"),
                ("Dinner at Barbeque Nation", 1200, 3500, "occasional"),
                ("Lunch at Domino's", 300, 900, "multi"),
                ("Starbucks Coffee", 150, 450, "multi"),
                ("Chaayos Coffee", 80, 250, "multi"),
                ("Swiggy Food Order", 250, 900, "multi"),
            ],
            "Shopping": [
                ("Amazon Electronics", 1500, 15000, "occasional"),
                ("Myntra Fashion Order", 800, 4000, "occasional"),
                ("Amazon Orders", 500, 3000, "multi"),
            ],
            "Entertainment": [
                ("Netflix Subscription", 499, 649, "monthly"),
                ("Spotify Premium", 119, 119, "monthly"),
                ("PVR Cinemas Movie Tickets", 400, 1200, "occasional"),
            ],
            "Healthcare": [
                ("Apollo Pharmacy", 300, 2000, "occasional"),
                ("Gold's Gym Membership", 1800, 2500, "monthly"),
                ("Doctor Consultation Fee", 500, 1500, "occasional"),
            ],
            "Travel": [
                ("Flight - Delhi to Goa (IndiGo)", 4500, 9000, "rare"),
                ("Taj Goa Hotel Booking", 6000, 15000, "rare"),
                ("MakeMyTrip Holiday Package", 3000, 12000, "rare"),
            ],
            "Education": [
                ("Udemy Online Course", 499, 1999, "occasional"),
                ("Coursera Subscription", 2500, 4000, "occasional"),
            ],
            "Others": [
                ("ATM Cash Withdrawal", 1000, 5000, "multi"),
                ("Gift for Friend", 500, 2000, "occasional"),
                ("LIC Insurance Premium", 3000, 8000, "occasional"),
            ],
        }

        payment_methods = ["Cash", "Card", "UPI", "Bank Transfer"]
        rent_month_names = ["January", "February", "March", "April", "May", "June",
                             "July", "August", "September", "October", "November", "December"]

        expense_rows = []

        for (y, m) in months:
            month_name = rent_month_names[m - 1]
            expense_rows.append((y, m, 1, expense_cats["Bills"].id, rng.randint(22000, 25000),
                                  f"{month_name} Apartment Rent", "Bank Transfer"))

            for cat_name, items in expense_items.items():
                cat_id = expense_cats[cat_name].id
                for desc, lo, hi, freq in items:
                    if freq == "monthly":
                        expense_rows.append((y, m, rng.randint(1, 10), cat_id, rng.randint(lo, hi), desc, rng.choice(payment_methods)))
                    elif freq == "multi":
                        for _ in range(rng.randint(1, 2)):
                            expense_rows.append((y, m, rng.randint(1, 28), cat_id, rng.randint(lo, hi), desc, rng.choice(payment_methods)))
                    elif freq == "occasional":
                        if rng.random() < 0.35:
                            expense_rows.append((y, m, rng.randint(1, 28), cat_id, rng.randint(lo, hi), desc, rng.choice(payment_methods)))
                    elif freq == "rare":
                        if rng.random() < 0.15:
                            expense_rows.append((y, m, rng.randint(1, 28), cat_id, rng.randint(lo, hi), desc, rng.choice(payment_methods)))

        current_month_expense_target = 68430
        current_exp_rows = [r for r in expense_rows if (r[0], r[1]) == current_ym]
        current_exp_total = sum(r[4] for r in current_exp_rows)
        exp_adjustment = current_month_expense_target - current_exp_total
        if exp_adjustment > 0:
            expense_rows.append((current_ym[0], current_ym[1], 27, expense_cats["Others"].id,
                                  exp_adjustment, "Miscellaneous Monthly Expense", "Card"))
        elif exp_adjustment < 0:
            trimmable = [i for i, r in enumerate(expense_rows) if (r[0], r[1]) == current_ym and r[3] != expense_cats["Bills"].id]
            trimmable.sort(key=lambda i: expense_rows[i][4], reverse=True)
            remaining = -exp_adjustment
            for i in trimmable:
                if remaining <= 0:
                    break
                y, m, d, cat_id, amt, desc, pm = expense_rows[i]
                cut = min(amt - 50, remaining)
                if cut > 0:
                    expense_rows[i] = (y, m, d, cat_id, amt - cut, desc, pm)
                    remaining -= cut

        for (y, m, d, cat_id, amount, desc, pm) in expense_rows:
            db.session.add(Expense(
                user_id=user.id, category_id=cat_id, amount=amount,
                description=desc, date=date(y, m, d), payment_method=pm,
            ))

        db.session.flush()

        # =================================================================
        # BUDGETS
        # =================================================================
        cur_y, cur_m = current_ym

        spent_by_cat = {}
        for cat_name, cat in expense_cats.items():
            total = sum(r[4] for r in expense_rows if (r[0], r[1]) == current_ym and r[3] == cat.id)
            spent_by_cat[cat_name] = total

        status_cycle = ["under", "under", "near", "under", "over", "near", "under", "over", "near"]
        budget_rows_created = 0
        for i, (cat_name, cat) in enumerate(expense_cats.items()):
            spent = spent_by_cat.get(cat_name, 0)
            if spent <= 0:
                spent = rng.randint(500, 2000)
            status = status_cycle[i % len(status_cycle)]
            if status == "under":
                budget_amount = round(spent / rng.uniform(0.45, 0.65), -2)
            elif status == "near":
                budget_amount = round(spent / rng.uniform(0.82, 0.95), -2)
            else:
                budget_amount = round(spent / rng.uniform(1.1, 1.3), -2)
            db.session.add(Budget(user_id=user.id, category_id=cat.id, amount=budget_amount, month=cur_m, year=cur_y))
            budget_rows_created += 1

        prev_y, prev_m = months[-2]
        for cat_name in ["Food", "Transport", "Shopping"]:
            cat = expense_cats[cat_name]
            prev_spent = sum(r[4] for r in expense_rows if (r[0], r[1]) == (prev_y, prev_m) and r[3] == cat.id) or rng.randint(2000, 5000)
            db.session.add(Budget(user_id=user.id, category_id=cat.id, amount=round(prev_spent / rng.uniform(0.7, 1.1), -2), month=prev_m, year=prev_y))
            budget_rows_created += 1

        # =================================================================
        # SAVINGS GOALS
        # =================================================================
        goal_defs = [
            ("Emergency Fund", "fa-shield-heart", 500000, 350000, 180),
            ("Europe Vacation", "fa-plane", 300000, 220000, 240),
            ("New Car", "fa-car", 1200000, 650000, 365),
            ("Home Down Payment", "fa-house", 2000000, 950000, 540),
        ]
        for title, icon, target, saved, days_out in goal_defs:
            db.session.add(SavingsGoal(
                user_id=user.id, title=title, icon=icon,
                target_amount=target, saved_amount=saved,
                target_date=today + timedelta(days=days_out),
                is_completed=False,
            ))

        # =================================================================
        # NOTIFICATIONS -- 20 realistic, timestamped across the year.
        # =================================================================
        notif_templates = [
            ("Budget warning", "You've used 85% of your Shopping budget for {month}.", "warning"),
            ("Budget exceeded", "You've exceeded your Entertainment budget for {month}.", "danger"),
            ("Large expense detected", "A large expense of ₹8,500 was recorded in 'Travel'.", "warning"),
            ("Monthly report available", "Your {month} financial summary report is ready to view.", "info"),
            ("Goal contribution added", "You added ₹15,000 to your 'Emergency Fund' goal.", "success"),
            ("Budget warning", "You've used 82% of your Food budget for {month}.", "warning"),
            ("Savings milestone", "Your 'Europe Vacation' fund just crossed 70% completion.", "success"),
            ("Large expense detected", "A large expense of ₹12,000 was recorded in 'Shopping'.", "warning"),
            ("Budget exceeded", "You've exceeded your Transport budget for {month}.", "danger"),
            ("Cashback received", "You received ₹450 cashback on a recent purchase.", "info"),
        ]
        for i in range(20):
            template = notif_templates[i % len(notif_templates)]
            y, m = rng.choice(months)
            day = rng.randint(1, 27)
            month_label = rent_month_names[m - 1]
            title, message_tpl, category = template
            created = datetime(y, m, day, rng.randint(8, 21), rng.randint(0, 59))
            db.session.add(Notification(
                user_id=user.id, title=title, message=message_tpl.format(month=month_label),
                category=category, is_read=(i < 14),
                created_at=created,
            ))

        db.session.commit()
        app.logger.info(
            f"Presentation account ready: {len(income_rows)} income rows, {len(expense_rows)} expense rows, "
            f"{budget_rows_created} budgets, {len(goal_defs)} savings goals, 20 notifications."
        )
