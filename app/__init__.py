from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from app.config import Config
from app.routes import health_bp
from flask_migrate import Migrate
from app.models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate = Migrate(app, db)
    app.register_blueprint(health_bp)
    return app
