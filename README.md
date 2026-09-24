# Student-api

A small Flask + SQLAlchemy REST API for managing students (see `notes.md` for the field rules).

## Run

    source .venv/bin/activate
    python run.py            # http://localhost:5001 (5000 is taken by AirPlay on macOS)

## Test

    python -m pytest

## Endpoints

| Method | Path             | Success | Errors        |
|--------|------------------|---------|---------------|
| GET    | /students        | 200     |               |
| GET    | /students/<id>   | 200     | 404           |
| POST   | /students        | 201     | 400, 409      |
| PATCH  | /students/<id>   | 200     | 400, 404, 409 |
| DELETE | /students/<id>   | 204     | 404           |
