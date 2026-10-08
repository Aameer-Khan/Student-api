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

    errors = []

    name = data["name"]
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        errors.append("name must be a non-empty string of at most 100 characters")

    email = data["email"]
    if not isinstance(email, str) or "@" not in email:
        errors.append("email must be a valid email address")

    age = data["age"]
    if not isinstance(age, int) or age < 5 or age > 100:
        errors.append("age must be a whole number between 5 and 100")

    if errors:
        return jsonify({"error": "Invalid data", "details": errors}), 400


    student = Student(name=name, email=email, age=age)
    
    db.session.add(student)
    db.session.commit()

    return jsonify(student.to_dict()), 201