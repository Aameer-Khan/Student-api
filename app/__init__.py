import logging
import sys
from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from app.config import Config
from app.routes import health_bp, students_bp
from flask_migrate import Migrate
from app.models import db
from app.errors import handle_http_error, handle_unexpected_error
from werkzeug.exceptions import HTTPException



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("werkzeug").setLevel(app.config["LOG_LEVEL"])
    db.init_app(app)
    migrate = Migrate(app, db)
    app.register_blueprint(health_bp)
    app.register_blueprint(students_bp)
    app.register_error_handler(HTTPException, handle_http_error)
    app.register_error_handler(Exception, handle_unexpected_error)
    return app
