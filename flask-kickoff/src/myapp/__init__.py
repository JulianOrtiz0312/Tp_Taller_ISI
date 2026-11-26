from flask import Flask

from myapp.config import Config
from myapp.extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from myapp.api.answers import api_answers_bp
    from myapp.api.auth import auth_bp
    from myapp.api.categories import categories_bp
    from myapp.api.health import health_bp
    from myapp.api.questions import api_questions_bp
    from myapp.api.users import api_users_bp
    from myapp.web.answers import answers_bp
    from myapp.web.categories import web_categories_bp
    from myapp.web.questions import questions_bp
    from myapp.web.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(api_questions_bp)
    app.register_blueprint(api_users_bp)
    app.register_blueprint(api_answers_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(answers_bp)
    app.register_blueprint(web_categories_bp)

    return app
