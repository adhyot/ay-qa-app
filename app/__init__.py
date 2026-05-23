import os
from flask import Flask
from app.config import config_map
from app.extensions import db, migrate, login_manager, jwt, csrf


def create_app(config_name: str = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_map.get(config_name, config_map['development']))

    os.makedirs(app.instance_path, exist_ok=True)

    _init_extensions(app)
    _register_blueprints(app)
    _register_shell_context(app)

    return app


def _init_extensions(app: Flask):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(user_id)

    # AUTH BYPASS — auto-login the first user so login is skipped.
    # Remove this block when ready to activate authentication.
    @app.before_request
    def auto_login():
        from flask_login import current_user, login_user
        from flask import request
        if not current_user.is_authenticated:
            user = User.query.filter_by(is_active=True).first()
            if user:
                login_user(user, remember=True)

    from app.simulator import start_scheduler
    start_scheduler(app)


def _register_blueprints(app: Flask):
    from app.blueprints.core import core_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.execution import execution_bp
    from app.blueprints.action_center import action_center_bp
    from app.blueprints.analytics import analytics_bp
    from app.blueprints.automation import automation_bp
    from app.blueprints.planning import planning_bp

    app.register_blueprint(core_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(execution_bp)
    app.register_blueprint(action_center_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(automation_bp)
    app.register_blueprint(planning_bp)

    from app.blueprints.settings import settings_bp
    app.register_blueprint(settings_bp)


def _register_shell_context(app: Flask):
    from app import models

    @app.shell_context_processor
    def shell_ctx():
        return {
            'db': db,
            'User': models.User,
            'Organization': models.Organization,
            'TestSuite': models.TestSuite,
            'TestRun': models.TestRun,
            'Bug': models.Bug,
        }
