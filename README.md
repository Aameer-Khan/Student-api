# Student API

A small REST API for managing student records, built with **Flask**, **SQLAlchemy** and **SQLite**.

It supports creating, listing, reading, updating and deleting students. Every input is validated, duplicate emails are rejected, errors always come back as JSON, logs go to stdout, database migrations are versioned, and the whole API is described in an OpenAPI spec and covered by pytest tests.

This was built step by step as a learning project. The [Learning journey](#learning-journey) section at the end shows how it was built up.

---

## Contents

1. [Tech stack](#tech-stack)
2. [Project structure](#project-structure)
3. [Getting started](#getting-started)
4. [Configuration](#configuration)
5. [API reference](#api-reference)
6. [Validation rules](#validation-rules)
7. [Error responses](#error-responses)
8. [Logging](#logging)
9. [Database migrations](#database-migrations)
10. [Testing](#testing)
11. [Running with Docker](#running-with-docker)
12. [Makefile commands](#makefile-commands)
13. [Learning journey](#learning-journey)

---

## Tech stack

| Tool                 | Used for                                                   |
|----------------------|------------------------------------------------------------|
| Python 3.12          | Language                                                   |
| Flask 3.1            | Web framework: routing, requests and responses             |
| Flask-SQLAlchemy     | Python classes used as database tables (the ORM)           |
| Flask-Migrate        | Versioned database schema changes (built on Alembic)       |
| SQLite               | The database: one file, no server needed                   |
| python-dotenv        | Loads settings from a `.env` file                          |
| pytest               | Automated tests                                            |
| Gunicorn             | Production WSGI server (runs the app inside the container) |
| Docker               | Container image (multi-stage build)                        |
| OpenAPI 3.0          | Machine-readable API documentation (`openapi.yml`)         |

The exact pinned versions are in [`requirements.txt`](requirements.txt). The reason for each package is explained in [docs/02-dependencies.md](docs/02-dependencies.md).

---

## Project structure

```
student-api/
├── app/                          ← the Flask application
│   ├── __init__.py               ← app factory: create_app() wires everything together
│   ├── config.py                 ← settings read from environment variables
│   ├── models.py                 ← the Student database model
│   ├── routes.py                 ← the endpoints + the shared validation helper
│   └── errors.py                 ← turns every error into a JSON response
├── migrations/                   ← Flask-Migrate / Alembic migration history
│   └── versions/
│       └── b1e4d2d77ca5_create_students_table.py
├── tests/                        ← pytest test suite
│   ├── conftest.py               ← fixtures: a test app on an in-memory database
│   ├── test_health.py            ← healthcheck endpoint
│   ├── test_students.py          ← the student endpoints, end to end
│   └── test_validation.py        ← the validation helper on its own
├── docs/                         ← learning notes written during setup
├── openapi.yml                   ← OpenAPI 3.0 spec for every endpoint
├── Dockerfile                    ← multi-stage image build: builder → slim runtime
├── .dockerignore                 ← files kept out of the image (.env, .venv, tests…)
├── Makefile                      ← shortcuts: install, migrate, run, test, docker-*
├── requirements.txt              ← pinned dependencies
├── .env.example                  ← template for .env: every setting with a working default
├── .env                          ← your local settings (not committed)
├── instance/                     ← where the SQLite database file lives (not committed)
└── .venv/                        ← virtual environment (not committed)
```

### How a request flows through the app

1. **`create_app()`** in `app/__init__.py` loads `.env`, reads the settings in `Config`, sets up logging, connects the database and migrations, and registers the routes and error handlers.
2. A request arrives at a route in **`routes.py`**. The route reads the JSON body and checks it with **`validate_student_fields()`**.
3. The route reads or writes **`Student`** rows through SQLAlchemy (`models.py`).
4. The response is JSON. Any error, whether it's an unknown URL, bad JSON or a crash, is caught by **`errors.py`** and returned as `{"error": "..."}`.

---

## Getting started

### Prerequisites

- **Git.** Check with `git --version`. It comes with the Xcode Command Line Tools on macOS.
- **Python 3.12.** Check with `python3.12 --version`. On macOS: `brew install python@3.12`.
- **make.** It comes with the Xcode Command Line Tools on macOS.

### 1. Clone the repository

```bash
git clone https://github.com/Aameer-Khan/Student-api.git
cd Student-api
```

### 2. Install dependencies

```bash
make install
```

This creates a virtual environment in `.venv/`, upgrades pip and installs everything from `requirements.txt`.

### 3. Create your `.env` file

The app won't start without a `DATABASE_URL`. Copy the example file:

```bash
cp .env.example .env
```

The defaults work as they are. A relative SQLite path like `sqlite:///app.db` is created inside the `instance/` folder. See [Configuration](#configuration) for every setting.

### 4. Create the database tables

```bash
make migrate
```

This runs every migration in `migrations/versions/`, which creates the `students` table.

### 5. Run the server

```bash
make run
```

The API is now running at **http://localhost:5001**, with debug mode and auto-reload on.

> **Why port 5001?** On macOS, port 5000 is taken by the AirPlay Receiver.

Check that it's up:

```bash
curl http://localhost:5001/healthcheck
```

You should get `{"status": "ok"}`.

### 6. Run the tests

```bash
make test
```

---

## Configuration

Settings are read from environment variables. `python-dotenv` loads them from `.env` when the app starts.

| Variable       | Required | Default | Description                                                         |
|----------------|----------|---------|---------------------------------------------------------------------|
| `DATABASE_URL` | **Yes**  | none    | SQLAlchemy database URL, for example `sqlite:///app.db`             |
| `LOG_LEVEL`    | No       | `INFO`  | Lowest log level to print: `DEBUG`, `INFO`, `WARNING`, `ERROR`       |

`.env` is listed in `.gitignore`, so your real settings never get committed. [`.env.example`](.env.example) is committed and lists every setting. When you add a new setting, add it there too.

---

## API reference

| Method   | Path                        | Description            | Success | Possible errors    |
|----------|-----------------------------|------------------------|---------|--------------------|
| `GET`    | `/healthcheck`              | Is the service up?     | 200     | none               |
| `GET`    | `/api/v1/students`          | List all students      | 200     | none               |
| `POST`   | `/api/v1/students`          | Create a student       | 201     | 400, 409, 415      |
| `GET`    | `/api/v1/students/<id>`     | Get one student        | 200     | 404                |
| `PATCH`  | `/api/v1/students/<id>`     | Update some fields     | 200     | 400, 404, 409, 415 |
| `DELETE` | `/api/v1/students/<id>`     | Delete a student       | 204     | 404                |

The student endpoints share the `/api/v1` prefix, so a future v2 can live next to this version without breaking existing clients.

The full machine-readable spec is in [`openapi.yml`](openapi.yml). To browse it, paste it into [editor.swagger.io](https://editor.swagger.io) or open it with any OpenAPI viewer.

### The Student object

```json
{
  "id": 1,
  "name": "Aameer",
  "email": "aameer@example.com",
  "age": 25,
  "created_at": "2026-10-16T20:00:46"
}
```

`id` and `created_at` are filled in by the server.

### Examples

**Create a student**

```bash
curl -X POST http://localhost:5001/api/v1/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Aameer", "email": "aameer@example.com", "age": 25}'
```

```json
{"age": 25, "created_at": "2026-10-16T20:00:46", "email": "aameer@example.com", "id": 1, "name": "Aameer"}
```

Status: `201 Created`

**List all students**

```bash
curl http://localhost:5001/api/v1/students
```

This returns a JSON array of students, or `[]` if there are none.

**Get one student**

```bash
curl http://localhost:5001/api/v1/students/1
```

**Update some fields**

Only send the fields you want to change. Everything else stays as it is.

```bash
curl -X PATCH http://localhost:5001/api/v1/students/1 \
  -H "Content-Type: application/json" \
  -d '{"age": 30}'
```

```json
{"age": 30, "created_at": "2026-10-16T20:00:46", "email": "aameer@example.com", "id": 1, "name": "Aameer"}
```

**Delete a student**

```bash
curl -X DELETE http://localhost:5001/api/v1/students/1
```

Status: `204 No Content`. The response has no body.

---

## Validation rules

| Field        | Type     | Required on create | Rule                                         |
|--------------|----------|--------------------|----------------------------------------------|
| `id`         | integer  | No (generated)     | Set by the database                          |
| `name`       | string   | Yes                | Not empty, at most 100 characters            |
| `email`      | string   | Yes                | Must contain `@`, must be unique             |
| `age`        | integer  | Yes                | A whole number from 5 to 100                 |
| `created_at` | datetime | No (automatic)     | Set by the database when the row is created  |

- **On `POST`**, the three required fields are checked first. If any are missing, the response lists them. Then the values are checked.
- **On `PATCH`**, every field is optional, but any field you send must follow the same rules.
- **Shared helper:** both endpoints use the same `validate_student_fields()` helper in `routes.py`, so the rules can't drift apart.

The reasons behind each rule are written up in [docs/03-student-schema.md](docs/03-student-schema.md).

---

## Error responses

Every error is returned as JSON with an `error` message.

| Status | When                                            | Example body                                                                 |
|--------|-------------------------------------------------|------------------------------------------------------------------------------|
| 400    | Required fields missing (create)                | `{"error": "Missing required fields", "missing": ["name", "age"]}`           |
| 400    | Field values break the rules                    | `{"error": "Invalid data", "details": ["age must be a whole number between 5 and 100"]}` |
| 400    | The body isn't valid JSON                       | `{"error": "Failed to decode JSON object: ..."}`                              |
| 404    | No student with that ID                         | `{"error": "Student not found"}`                                             |
| 404    | The URL doesn't exist                           | `{"error": "The requested URL was not found on the server. ..."}`. This is Flask's built-in message. |
| 409    | The email is already used by another student    | `{"error": "A student with this email already exists"}`                      |
| 415    | The request isn't sent as `application/json`    | `{"error": "Did not attempt to load JSON data because the request Content-Type was not 'application/json'."}` |
| 500    | Anything unexpected                             | `{"error": "Internal server error"}`. The full traceback goes to the logs.    |

**How it works:** `errors.py` registers two handlers in `create_app()`:
- `handle_http_error` turns any `HTTPException` (404, 415 and so on) into `{"error": <description>}` with the matching status code.
- `handle_unexpected_error` catches every other exception. It logs the full traceback and returns a plain 500, so internal details never reach the client.

---

## Logging

Logs are written to **stdout** in this format:

```
2026-10-17 01:30:46,945 INFO app.routes: Created student 1
2026-10-17 01:30:46,957 WARNING app.routes: IntegrityError: A student with this email already exists
```

| Event                               | Level     |
|-------------------------------------|-----------|
| Student created / updated / deleted | `INFO`    |
| Duplicate email on create           | `WARNING` |
| Lookup of a student that's missing  | `WARNING` |
| Unhandled exception (with traceback)| `ERROR`   |

Set `LOG_LEVEL` in `.env` to control how much is printed. Logging to stdout is the standard for apps that may later run in Docker or Kubernetes, which collect a container's stdout automatically.

---

## Database migrations

The database schema is managed with **Flask-Migrate**, which runs Alembic underneath. Each change to the schema is a versioned script in `migrations/versions/`, so every copy of the database can be brought to the same state.

| Task                                    | Command                                                 |
|-----------------------------------------|---------------------------------------------------------|
| Apply all migrations                    | `make migrate`                                          |
| Create a migration after editing a model| `.venv/bin/python -m flask --app app db migrate -m "describe the change"` |
| Undo the last migration                 | `.venv/bin/python -m flask --app app db downgrade`      |
| Show the current version                | `.venv/bin/python -m flask --app app db current`        |

Always read a generated migration before applying it. Alembic's autogenerate is good but not perfect.

**Current migrations:**

| Revision        | Description            |
|-----------------|------------------------|
| `b1e4d2d77ca5`  | Create `students` table |

---

## Testing

```bash
make test
```

The tests use an **in-memory SQLite database**, so they never touch your real data. Each test gets a fresh, empty database.

| File                  | What it covers                                                                           |
|-----------------------|------------------------------------------------------------------------------------------|
| `conftest.py`         | `app` and `client` fixtures: builds the app with `TESTING=True` and creates and drops the tables around each test |
| `test_health.py`      | `GET /healthcheck` returns 200 and `{"status": "ok"}`                                    |
| `test_students.py`    | Create (201, 400 missing, 400 invalid, 409 duplicate), list, get (200, 404), update and delete |
| `test_validation.py`  | `validate_student_fields()` on its own, including the age boundaries 4, 5, 100 and 101 and text instead of a number |

Current result: **17 passed**.

## Running with Docker

The image uses a **multi-stage build**: dependencies are installed in a full `python:3.12` builder stage, and only the installed packages and the code are copied into a slim runtime image. The API is served by **Gunicorn** and runs as a **non-root user**. Image size: about 290 MB, down from 1.7 GB with a single-stage build.

### 1. Build the image

```bash
make docker-build
```

Images are tagged with semantic versions (`MAJOR.MINOR.PATCH`), never `latest`. The version is set by `VERSION` in the Makefile.

### 2. Create the database tables

```bash
make docker-migrate
```

### 3. Run the container

```bash
make docker-run
```

The API is now available at http://localhost:5001.

### Configuration

Settings are passed in when the container starts and are never baked into the image (`.env` is excluded by `.dockerignore`). The make targets read them from `.env`. You can also pass them directly:

```bash
docker run --rm -p 5001:5000 \
  -e DATABASE_URL=sqlite:///app.db \
  -e LOG_LEVEL=INFO \
  -v student-data:/app/instance \
  student-api:1.0.1
```

### Data

The SQLite database lives in a Docker volume named `student-data`, mounted at `/app/instance`, so data survives container restarts. To start over with an empty database, run `docker volume rm student-data`.

---

## Makefile commands

| Command        | What it does                                                    |
|----------------|-----------------------------------------------------------------|
| `make install` | Create `.venv` with Python 3.12 and install `requirements.txt`  |
| `make migrate` | Apply database migrations (`flask db upgrade`)                  |
| `make run`     | Start the dev server on port 5001 with debug mode on            |
| `make test`    | Run the pytest suite with verbose output                        |
| `make docker-build`   | Build the Docker image `student-api:<VERSION>`           |
| `make docker-migrate` | Apply migrations inside a container, on the `student-data` volume |
| `make docker-run`     | Run the container on port 5001, with settings from `.env`  |

The Makefile calls `.venv/bin/python` directly, so you don't need to activate the virtual environment first.

---

## Learning journey

This project was built one concept at a time, in roughly this order. `git log --oneline` shows the commit for each step.

| #  | Step                     | What was learned                                                         |
|----|--------------------------|--------------------------------------------------------------------------|
| 1  | Environment setup        | Python 3.12, virtual environments, `.gitignore`, pinning dependencies ([notes](docs/01-environment-setup.md), [deps](docs/02-dependencies.md)) |
| 2  | Schema planning          | Designing the fields and validation rules before writing code ([notes](docs/03-student-schema.md)) |
| 3  | App skeleton             | The app factory pattern and config from environment variables            |
| 4  | Healthcheck              | The first endpoint, and Blueprints                                       |
| 5  | Model + migrations       | The SQLAlchemy model and Flask-Migrate, with the first migration         |
| 6  | List students            | `GET /api/v1/students` and API versioning with a URL prefix              |
| 7  | Create + validation      | Required fields, value checks, `400` with clear messages                 |
| 8  | Duplicate emails         | Catching `IntegrityError` and returning `409 Conflict`                   |
| 9  | Refactor validation      | Pulling the checks into one helper shared by create and update           |
| 10 | Get / update / delete    | `404`, partial updates with `PATCH`, `204 No Content`                    |
| 11 | JSON errors              | Global error handlers, so the API never returns HTML                     |
| 12 | Logging                  | Logging to stdout, `LOG_LEVEL` from env, a logged `500` handler          |
| 13 | Tests                    | pytest fixtures, an in-memory test database, unit and endpoint tests     |
| 14 | Makefile                 | One command each for install, migrate, run and test                      |
| 15 | OpenAPI spec             | Documenting every endpoint, request and response in `openapi.yml`        |

> **Note:** the notes in `docs/` were written during the early setup stage, when the virtual environment and `requirements.txt` lived inside `app/`. They have since moved back to the project root, where they are now.
