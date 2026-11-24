from flask import Flask

from myapp.config import Config
from myapp.extensions import db

def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    db.init_app(app)

    from myapp.api.categories import categories_bp
    from myapp.api.health import health_bp
    from myapp.api.users import api_users_bp
    from myapp.web.users import users_bp

    app.register_blueprint(categories_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(api_users_bp)

    from myapp.api.auth import auth_bp

    app.register_blueprint(auth_bp)

    return app
