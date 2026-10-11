from flask import jsonify
from werkzeug.exceptions import HTTPException


def handle_http_error(error):
    return jsonify({"error": error.description}), error.code