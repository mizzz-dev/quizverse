from flask import Flask

from .api.health import health_bp
from .config import Config
from .extensions import db, jwt, migrate
from . import models  # noqa: F401


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(health_bp)

    return app


app = create_app()
