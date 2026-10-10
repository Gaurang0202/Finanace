"""
app.py
------
Application entry point. Uses the Flask "app factory" pattern so the app
can be configured differently for development, testing and production,
and so Flask-Migrate's `flask db` commands can find the app cleanly.

Run with:  python app.py
Or via:    flask run
"""

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template
from flask_login import current_user

from config import config_by_name
from extensions import db, migrate, login_manager, csrf, mail
from models import User, Category, Settings
from models.category import DEFAULT_INCOME_CATEGORIES, DEFAULT_EXPENSE_CATEGORIES
from services.demo_seed import seed_presentation_account


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    os.makedirs(os.path.join(app.root_path, "database"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # --- Extensions -----------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # --- Blueprints -------------------------------------------------------
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.income import income_bp
    from routes.expenses import expenses_bp
    from routes.budget import budget_bp
    from routes.savings import savings_bp
    from routes.analytics import analytics_bp
    from routes.api import api_bp
    from routes.reports import reports_bp
    from routes.profile import profile_bp
    from routes.notifications import notifications_bp
    from routes.admin import admin_bp
    from routes.onboarding import onboarding_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(savings_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(onboarding_bp)

    # --- Logging ------------------------------------------------------
    if not app.debug:
        handler = RotatingFileHandler(os.path.join(app.root_path, "database", "app.log"), maxBytes=1_000_000, backupCount=3)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

    # --- Error handlers -------------------------------------------------
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Server error: %s", e)
        return render_template("errors/500.html"), 500

    # --- Template context: unread notification count + theme ------------
    @app.context_processor
    def inject_globals():
        unread_count = 0
        theme = "light"
        show_onboarding = False
        if current_user.is_authenticated:
            unread_count = current_user.notifications.filter_by(is_read=False).count()
            if current_user.settings:
                theme = current_user.settings.theme
            show_onboarding = not current_user.onboarding_completed
        return dict(unread_notifications=unread_count, active_theme=theme, show_onboarding=show_onboarding)

    # --- Landing page -----------------------------------------------
    @app.route("/")
    @app.route("/home")
    def landing():
        if current_user.is_authenticated:
            from flask import redirect, url_for
            return redirect(url_for("dashboard.index"))
        return render_template("index.html")

    return app


def seed_defaults(app):
    """Create default categories and a bootstrap admin account if missing."""
    with app.app_context():
        db.create_all()

        if Category.query.count() == 0:
            for name, icon, color in DEFAULT_INCOME_CATEGORIES:
                db.session.add(Category(name=name, type="income", icon=icon, color=color))
            for name, icon, color in DEFAULT_EXPENSE_CATEGORIES:
                db.session.add(Category(name=name, type="expense", icon=icon, color=color))
            db.session.commit()
            app.logger.info("Seeded default categories.")

        admin_email = app.config["ADMIN_EMAIL"]
        if not User.query.filter_by(email=admin_email).first():
            admin = User(name="Administrator", email=admin_email, role="admin")
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
            db.session.flush()
            db.session.add(Settings(user_id=admin.id))
            db.session.commit()
            app.logger.info(f"Created bootstrap admin account: {admin_email}")


def _ensure_columns(app):
    """Lightweight schema self-heal: add columns introduced after a database was
    first created (db.create_all() never alters existing tables)."""
    from sqlalchemy import inspect, text
    wanted = {
        "phone": "VARCHAR(30)",
        "address": "VARCHAR(255)",
        "occupation": "VARCHAR(120)",
        "onboarding_completed": "BOOLEAN NOT NULL DEFAULT FALSE",
    }
    with app.app_context():
        insp = inspect(db.engine)
        if "users" not in insp.get_table_names():
            return
        existing = {c["name"] for c in insp.get_columns("users")}
        for col, ddl in wanted.items():
            if col not in existing:
                db.session.execute(text(f"ALTER TABLE users ADD COLUMN {col} {ddl}"))
                app.logger.info(f"Added missing column users.{col}")
        db.session.commit()


def bootstrap(app):
    """Idempotent startup: tables, schema repair, default categories, admin,
    and the presentation account (created or repaired if needed)."""
    with app.app_context():
        db.create_all()
    _ensure_columns(app)
    seed_defaults(app)
    seed_presentation_account(app)


app = create_app()
bootstrap(app)  # runs however the app is launched (python app.py, flask run, gunicorn)

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", True), host="0.0.0.0", port=5000)
