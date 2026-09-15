import os

from flask import Flask, render_template

from config import Config
from app.extensions import db, migrate, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///") and ":memory:" not in db_uri:
        db_path = db_uri.replace("sqlite:///", "", 1)
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        except OSError:
            # Read-only filesystem (e.g. a serverless deployment with no
            # cloud DATABASE_URL configured yet) - nothing we can do locally.
            pass

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.models.user import User
    from app.models import area, review, report  # noqa: F401 (register tables)

    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.area import area_bp
    from app.routes.review import review_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(area_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.context_processor
    def inject_globals():
        from app.models.report import REPORT_REASONS
        from app.models.review import FAMILY_TYPES

        return {"REPORT_REASONS": REPORT_REASONS, "FAMILY_TYPES": FAMILY_TYPES}

    return app
