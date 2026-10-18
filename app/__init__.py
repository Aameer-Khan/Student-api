import logging
import sys

from dotenv import load_dotenv

load_dotenv()
from flask import Flask
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.errors import handle_http_error, handle_unexpected_error
from app.models import db
from app.routes import health_bp, students_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("werkzeug").setLevel(app.config["LOG_LEVEL"])
    db.init_app(app)
    Migrate(app, db)
    app.register_blueprint(health_bp)
    app.register_blueprint(students_bp)
    app.register_error_handler(HTTPException, handle_http_error)
    app.register_error_handler(Exception, handle_unexpected_error)
    return app
