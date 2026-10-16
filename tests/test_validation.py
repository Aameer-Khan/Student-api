from app.routes import validate_student_fields

def test_valid_data_has_no_errors():
    errors = validate_student_fields({"name": "Aameer", "email": "a@example.com", "age": 25})
    assert errors == []

def test_age_out_of_range_is_rejected():
    errors = validate_student_fields({"age": 2})
    assert len(errors) == 1

def test_age_101_is_rejected():
    errors = validate_student_fields({"age": 101})
    assert len(errors) == 1

def test_age_4_is_rejected():
    errors = validate_student_fields({"age": 4})
    assert len(errors) == 1

def test_age_5_is_accepted():
    errors = validate_student_fields({"age": 5})
    assert errors == []

def test_age_100_is_accepted():
    errors = validate_student_fields({"age": 100})
    assert errors == []

def test_age_as_text_is_rejected():
    errors = validate_student_fields({"age": "twenty"})
    assert len(errors) == 1