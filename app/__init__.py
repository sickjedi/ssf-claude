import logging
import os
from datetime import datetime, timezone

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config


class _DailyFileHandler(logging.FileHandler):
    """Writes to YYYYMMDD-SSF.log, opening a new file automatically at midnight."""

    def __init__(self, log_dir):
        os.makedirs(log_dir, exist_ok=True)
        self._log_dir = log_dir
        self._current_date = datetime.now(timezone.utc).date()
        super().__init__(self._path_for(self._current_date), mode='a', encoding='utf-8')

    def _path_for(self, date):
        return os.path.join(self._log_dir, date.strftime('%Y%m%d') + '-SSF.log')

    def emit(self, record):
        today = datetime.now(timezone.utc).date()
        if today != self._current_date:
            self.close()
            self._current_date = today
            self.baseFilename = os.path.abspath(self._path_for(today))
            self.stream = self._open()
        super().emit(record)


def _setup_audit_logging(app):
    log_dir = os.path.join(os.path.dirname(app.root_path), 'logs')
    handler = _DailyFileHandler(log_dir)
    handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger = logging.getLogger('ssf.audit')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.members import bp as members_bp
    app.register_blueprint(members_bp, url_prefix='/members')

    from app.customers import bp as customers_bp
    app.register_blueprint(customers_bp, url_prefix='/customers')

    from app.invoices import bp as invoices_bp
    app.register_blueprint(invoices_bp, url_prefix='/invoices')

    from app.items import bp as items_bp
    app.register_blueprint(items_bp, url_prefix='/items')

    from app.settings import bp as settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')

    _setup_audit_logging(app)

    with app.app_context():
        from app.cli import create_user  # noqa: F401

    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('members.index'))

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('errors/500.html'), 500

    return app
