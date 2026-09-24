from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from . import db
from .models import Student

bp = Blueprint("students", __name__, url_prefix="/students")

READ_ONLY = {"id", "created_at"}
FIELDS = {"name", "email", "age"}


def validate(data, partial=False):
    """Return a dict of field -> error message (empty if valid)."""
    errors = {}
    if not isinstance(data, dict):
        return {"body": "Request body must be a JSON object"}

    for field in READ_ONLY & data.keys():
        errors[field] = "Field is read-only"
    for field in data.keys() - FIELDS - READ_ONLY:
        errors[field] = "Unknown field"

    if not partial:
        for field in FIELDS - data.keys():
            errors[field] = "Field is required"

    if "name" in data:
        name = data["name"]
        if not isinstance(name, str) or not name.strip():
            errors["name"] = "Must be a non-empty string"
        elif len(name) > 100:
            errors["name"] = "Must be at most 100 characters"

    if "email" in data:
        email = data["email"]
        if not isinstance(email, str) or "@" not in email:
            errors["email"] = "Must be a string containing @"

    if "age" in data:
        age = data["age"]
        # bool is a subclass of int, so rule it out explicitly
        if not isinstance(age, int) or isinstance(age, bool):
            errors["age"] = "Must be an integer"
        elif not 5 <= age <= 100:
            errors["age"] = "Must be between 5 and 100"

    return errors


def error(message, status, details=None):
    body = {"error": message}
    if details:
        body["details"] = details
    return jsonify(body), status


def save(student, status):
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("A student with that email already exists", 409)
    return jsonify(student.to_dict()), status


@bp.get("")
def list_students():
    students = db.session.scalars(db.select(Student).order_by(Student.id)).all()
    return jsonify([s.to_dict() for s in students])


@bp.get("/<int:student_id>")
def get_student(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        return error("Student not found", 404)
    return jsonify(student.to_dict())


@bp.post("")
def create_student():
    data = request.get_json(silent=True)
    if errors := validate(data):
        return error("Validation failed", 400, errors)
    student = Student(name=data["name"].strip(), email=data["email"], age=data["age"])
    db.session.add(student)
    return save(student, 201)


@bp.patch("/<int:student_id>")
def update_student(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        return error("Student not found", 404)
    data = request.get_json(silent=True)
    if errors := validate(data, partial=True):
        return error("Validation failed", 400, errors)
    for field, value in data.items():
        setattr(student, field, value.strip() if field == "name" else value)
    return save(student, 200)


@bp.delete("/<int:student_id>")
def delete_student(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        return error("Student not found", 404)
    db.session.delete(student)
    db.session.commit()
    return "", 204
