from flask import Blueprint, jsonify, request
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

@students_bp.route("/students", methods=["POST"])
def create_student():
    data = request.get_json()
    missing = []
    for field in ["name", "email", "age"]:
        if field not in data:
            missing.append(field)
    if missing:
        return jsonify({"error": "Missing required fields", "missing": missing}), 400
    student = Student(
        name=data["name"],
        email=data["email"],
        age=data["age"]
    )
    db.session.add(student)
    db.session.commit()

    return jsonify(student.to_dict()), 201