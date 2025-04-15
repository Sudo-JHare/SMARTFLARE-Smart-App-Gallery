#app/__init__.py

import os
import hashlib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_oauthlib.client import OAuth
from config import Config
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
oauth = OAuth()

def create_app():
    app = Flask(__name__, instance_relative_config=True, static_folder='/app/static')
    app.config.from_object(Config)

    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs('/app/uploads', exist_ok=True)
    except OSError:
        pass

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    oauth.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.template_filter('md5')
    def md5_filter(s):
        if s:
            return hashlib.md5(s.encode('utf-8').lower().strip()).hexdigest()
        return ''

    @app.template_filter('datetimeformat')
    def datetimeformat(value):
        if value == 'now':
            return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        return value

    @app.template_filter('rejectattr')
    def rejectattr_filter(d, attr):
        if not isinstance(d, dict):
            return {}
        return {k: v for k, v in d.items() if k != attr}

    from app.routes import gallery_bp
    from app.auth import auth_bp
    app.register_blueprint(gallery_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    with app.app_context():
        db.create_all()

    return app