from flask import Flask

from myapp.config import Config
from myapp.extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    db.init_app(app)

    from myapp.api.health import health_bp
    from myapp.api.users import users_api_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(users_api_bp)

    return app