import logging
logger = logging.getLogger(__name__)
from flask import jsonify
from werkzeug.exceptions import HTTPException


def handle_http_error(error):
    return jsonify({"error": error.description}), error.code

def handle_unexpected_error(error):
    logger.exception("Unhandled exception")
    return jsonify({"error": "Internal server error"}), 500