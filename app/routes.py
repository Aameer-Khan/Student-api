from flask import Blueprint, jsonify, request
from app.models import Student, db
from sqlalchemy.exc import IntegrityError

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

def validate_student_fields(data):
    errors = []

    if "name" in data:
        name = data["name"]
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            errors.append("name must be a non-empty string of at most 100 characters")
        # your existing name check goes here (indented one more level)

    if "email" in data:
        email = data["email"]
        if not isinstance(email, str) or "@" not in email:
            errors.append("email must be a valid email address")

    if "age" in data:
        age = data["age"]
        if not isinstance(age, int) or age < 5 or age > 100:
            errors.append("age must be a whole number between 5 and 100")

    return errors


@students_bp.route("/students", methods=["POST"])
def create_student():
    data = request.get_json()
    missing = []
    for field in ["name", "email", "age"]:
        if field not in data:
            missing.append(field)
    if missing:
        return jsonify({"error": "Missing required fields", "missing": missing}), 400

    errors = validate_student_fields(data)

    if errors:
        return jsonify({"error": "Invalid data", "details": errors}), 400


    student = Student(name=data["name"], email=data["email"], age=data["age"])
    db.session.add(student)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A student with this email already exists"}), 409

    return jsonify(student.to_dict()), 201


@students_bp.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student.to_dict()), 200


@students_bp.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        return jsonify({"error": "Student not found"}), 404
    db.session.delete(student)
    db.session.commit()
    return "", 204