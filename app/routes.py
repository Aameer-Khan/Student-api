from flask import Blueprint, jsonify
from app.models import Student, db

health_bp = Blueprint("health", __name__)
students_bp = Blueprint("students", __name__, url_prefix="/api/v1")


@health_bp.route("/healthcheck", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200



@students_bp.route("/students", methods=["GET"])
def get_students():
    students = Student.query.all()
    result = []
    for student in students:
        result.append(student.to_dict())
    return jsonify(result), 200
