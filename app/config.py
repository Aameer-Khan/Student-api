import os

class Config:
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]