# Student API

A small REST API for managing student records, built with **Flask** and **SQLAlchemy**. With **Docker Compose** it runs next to a **PostgreSQL** database. For quick local development without Docker, it can use **SQLite** instead.

It supports creating, listing, reading, updating and deleting students. Every input is validated, duplicate emails are rejected, errors always come back as JSON, logs go to stdout, database migrations are versioned, the healthcheck tests the database connection, and the whole API is described in an OpenAPI spec and covered by pytest tests.

This was built step by step as a learning project. The [Learning journey](#learning-journey) section at the end shows how it was built up.

---

## Contents

1. [Tech stack](#tech-stack)
2. [Project structure](#project-structure)
3. [Getting started](#getting-started)
4. [Architecture](#architecture)
5. [Make targets](#make-targets)
6. [Configuration](#configuration)
7. [API reference](#api-reference)
8. [Healthcheck](#healthcheck)
9. [Validation rules](#validation-rules)
10. [Error responses](#error-responses)
11. [Logging](#logging)
12. [Database migrations](#database-migrations)
13. [Testing](#testing)
14. [Learning journey](#learning-journey)

---

## Tech stack

| Tool                 | Used for                                                          |
|----------------------|-------------------------------------------------------------------|
| Python 3.12          | Language                                                          |
| Flask 3.1            | Web framework: routing, requests and responses                    |
| Flask-SQLAlchemy     | Python classes used as database tables (the ORM)                  |
| Flask-Migrate        | Versioned database schema changes (built on Alembic)              |
| PostgreSQL 17        | The database when running with Docker Compose (`postgres:17-alpine`) |
| psycopg 3            | PostgreSQL driver used by SQLAlchemy (`postgresql+psycopg://`)    |
| SQLite               | Database for local development and tests: one file, no server     |
| python-dotenv        | Loads settings from a `.env` file                                 |
| pytest               | Automated tests                                                   |
| Gunicorn             | Production WSGI server (runs the app inside the container)        |
| Docker               | Container image (multi-stage build, non-root user)                |
| Docker Compose       | Runs the API and the database together                            |
| OpenAPI 3.0          | Machine-readable API documentation (`openapi.yml`)                |

The exact pinned versions are in [`requirements.txt`](requirements.txt). The reason for each of the original packages is explained in [docs/02-dependencies.md](docs/02-dependencies.md).

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
├── scripts/
│   └── setup.sh                  ← checks for (and installs) make and Docker
├── docs/                         ← learning notes written during setup
├── openapi.yml                   ← OpenAPI 3.0 spec for every endpoint
├── Dockerfile                    ← multi-stage image build: builder → slim runtime
├── .dockerignore                 ← files kept out of the image (.env, .venv, tests…)
├── docker-compose.yml            ← two services: db (PostgreSQL) and api
├── Makefile                      ← shortcuts for Docker and local development
├── requirements.txt              ← pinned dependencies
├── .env.example                  ← template for .env: every setting with a working default
├── .env                          ← your local settings (not committed)
├── instance/                     ← SQLite database file for local development (not committed)
└── .venv/                        ← virtual environment for local development (not committed)
```

### How a request flows through the app

1. **`create_app()`** in `app/__init__.py` loads `.env`, reads the settings in `Config`, sets up logging, connects the database and migrations, and registers the routes and error handlers.
2. A request arrives at a route in **`routes.py`**. The route reads the JSON body and checks it with **`validate_student_fields()`**.
3. The route reads or writes **`Student`** rows through SQLAlchemy (`models.py`).
4. The response is JSON. Any error, whether it's an unknown URL, bad JSON or a crash, is caught by **`errors.py`** and returned as `{"error": "..."}`.

---

## Getting started

### Prerequisites

| Tool                 | Why                                         | Check with       |
|----------------------|---------------------------------------------|------------------|
| **Git**              | To clone the repository                     | `git --version`  |
| **Docker**           | Builds and runs the containers. The Docker Engine must be **running**. | `docker info` |
| **make**             | Runs the shortcuts in the `Makefile`        | `make --version` |

Docker Compose is included with Docker Desktop.

#### `scripts/setup.sh`

This script sets up the tools for you:

```bash
./scripts/setup.sh
```

It does three things, in order:

1. **Checks for `make`** and installs it if it's missing. On macOS it uses `xcode-select --install`, and on Linux `apt-get install make`.
2. **Checks for `docker`** and installs it if it's missing. On macOS it uses `brew install --cask docker`, which needs [Homebrew](https://brew.sh), and on Linux the official script from `get.docker.com`.
3. **Checks that the Docker Engine is running.** If it isn't, it tells you to start Docker Desktop and run the script again.

Each tool that is already installed is reported with ✔ and skipped, so it's safe to run the script any number of times.

### Quick start (one command after setup)

```bash
git clone https://github.com/Aameer-Khan/Student-api.git && cd Student-api
./scripts/setup.sh
cp .env.example .env
make docker-run
```

`make docker-run` builds the API image, starts PostgreSQL and waits until it's healthy, applies the migrations, and then starts the API in the background. See [Make targets](#make-targets) for each step.

Check that it's up:

```bash
curl http://localhost:5001/healthcheck
```

You should get `{"status": "ok"}`, which means the API is running **and** can reach the database.

To stop everything:

```bash
make down
```

Your data is kept in the `pgdata` volume, so it's still there the next time you run `make docker-run`.

> **Why port 5001?** On macOS, port 5000 is taken by the AirPlay Receiver. The Docker API and the local dev server (`make run`) both use 5001, so run only one of them at a time.

### Local development (without Docker)

To run the app directly on your machine against a SQLite file, you also need **Python 3.12**. Check with `python3.12 --version`, and on macOS install it with `brew install python@3.12`.

```bash
cp .env.example .env   # if you haven't already
make install           # create .venv and install requirements.txt
make migrate           # create the tables in instance/app.db
make run               # dev server on http://localhost:5001, with debug and auto-reload
make test              # run the test suite
```

The local targets use `DATABASE_URL` from `.env`, which is `sqlite:///app.db` by default.

---

## Architecture

`docker compose` runs two services, defined in [`docker-compose.yml`](docker-compose.yml):

```
              your machine
                   │
           localhost:5001
                   │
 ┌─────────────────┼──────────── compose network (private) ───┐
 │                 ▼                                           │
 │   ┌──────────────────────────┐       ┌───────────────────┐  │
 │   │ api                      │       │ db                │  │
 │   │ student-api:<VERSION>    │──────▶│ postgres:17-alpine│  │
 │   │ Gunicorn on port 5000    │ db:5432  port 5432        │  │
 │   └──────────────────────────┘       └─────────┬─────────┘  │
 │                                                │            │
 └────────────────────────────────────────────────┼────────────┘
                                                  ▼
                                         volume: pgdata
```

- **A private network.** Compose puts both services on their own network. The API reaches the database at the hostname **`db`**, which is the service name, on port 5432.
- **Only the API is published.** Its container port 5000 is mapped to **localhost:5001**. The database port is **not** published, so nothing outside the compose network can connect to PostgreSQL directly.
- **Data lives in a named volume.** PostgreSQL stores its files in the volume **`pgdata`**. It survives `make down` and container rebuilds. To start over with an empty database, run `docker compose down -v`, which also deletes the volume.
- **Startup order.** The `db` service has a healthcheck that runs `pg_isready` every 5 seconds. The `api` service has `depends_on: db: condition: service_healthy`, so the API only starts once PostgreSQL is accepting connections.
- **Settings stay out of the image.** `.env` is excluded by `.dockerignore`. Compose reads `.env` and passes the values to the containers when they start. See [Configuration](#configuration).

### The image

The `Dockerfile` uses a **multi-stage build**:
1. Dependencies are installed in a full `python:3.12` builder stage.
2. Only the installed packages and the code are copied into a slim `python:3.12-slim` runtime image.

The API is served by **Gunicorn** and runs as a **non-root user** (`appuser`). The image was about 290 MB at version 1.0.1, compared with 1.7 GB for a single-stage build.

Images are tagged with semantic versions (`MAJOR.MINOR.PATCH`), currently **`1.1.0`**, and **never `latest`**. The version is set by `VERSION` in the `Makefile`, which passes it to Compose.

> **Always use the `make` targets** to build and run with Docker. `docker-compose.yml` takes the image tag from `VERSION`, which only the Makefile sets. A plain `docker compose build` would leave the tag empty and fail.

---

## Make targets

### Docker (API + PostgreSQL)

| Target              | Depends on                   | What it does                                                                                       |
|---------------------|------------------------------|----------------------------------------------------------------------------------------------------|
| `make db-up`        | none                         | Starts the PostgreSQL container and waits until its healthcheck passes. Does nothing if it's already running. |
| `make db-migrate`   | `db-up`                      | Applies the database migrations in a one-off API container. Does nothing if they're already applied. |
| `make docker-build` | none                         | Builds the API image, tagged `student-api:<VERSION>` (`VERSION` is set in the Makefile).           |
| `make docker-run`   | `docker-build`, `db-migrate` | Runs both of those, then starts the API container in the background.                              |
| `make down`         | none                         | Stops and removes the containers. The `pgdata` database volume is **kept**.                        |

**Dependency chain:**

```
make docker-run
├── docker-build          build the API image
└── db-migrate            apply migrations
    └── db-up             start PostgreSQL and wait until healthy
then: start the API container
```

### Local development (SQLite)

| Target         | What it does                                                    |
|----------------|-----------------------------------------------------------------|
| `make install` | Create `.venv` with Python 3.12 and install `requirements.txt`  |
| `make migrate` | Apply database migrations (`flask db upgrade`) to the local database |
| `make run`     | Start the Flask dev server on port 5001 with debug mode on      |
| `make test`    | Run the pytest suite with verbose output                        |

The local targets call `.venv/bin/python` directly, so you don't need to activate the virtual environment first.

---

## Configuration

Settings come from environment variables. Copy [`.env.example`](.env.example) to `.env`, which already lists every variable with a working placeholder value:

```bash
cp .env.example .env
```

| Variable            | Used by                         | Default (if unset)  | Description                                                     |
|---------------------|---------------------------------|---------------------|-----------------------------------------------------------------|
| `POSTGRES_USER`     | Docker: `db` service + API      | `student`           | PostgreSQL username                                             |
| `POSTGRES_PASSWORD` | Docker: `db` service + API      | `student_pass`      | PostgreSQL password                                             |
| `POSTGRES_DB`       | Docker: `db` service + API      | `studentdb`         | PostgreSQL database name                                        |
| `LOG_LEVEL`         | Docker and local                | `INFO`              | Lowest log level to print: `DEBUG`, `INFO`, `WARNING`, `ERROR`   |
| `DATABASE_URL`      | Local development only          | none (**required** locally) | SQLAlchemy database URL, for example `sqlite:///app.db`  |

**How the Docker settings are used:**
- `docker-compose.yml` passes the three `POSTGRES_*` values to the **`db`** service, which creates the user and database on first start.
- It also uses them to **build the API's `DATABASE_URL`**:
  ```
  postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
  ```
- So inside Docker, the `DATABASE_URL` line in `.env` is ignored. Compose sets it for the container.

`.env` is listed in `.gitignore`, so your real settings never get committed. `.env.example` is committed. When you add a new setting, add it there too.

> **Changing the Postgres credentials later:** PostgreSQL only reads `POSTGRES_*` when the `pgdata` volume is first created. To change them after that, run `docker compose down -v` to remove the volume, which deletes the data, and then `make docker-run` again.

---

## API reference

| Method   | Path                        | Description            | Success | Possible errors    |
|----------|-----------------------------|------------------------|---------|--------------------|
| `GET`    | `/healthcheck`              | Is the service up and the database reachable? | 200 | 503 |
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

## Healthcheck

`GET /healthcheck` doesn't just report that the web server is up. It runs **`SELECT 1`** against the database, so it also proves the API can reach the database.

| Database        | Status                    | Body                                              |
|-----------------|---------------------------|---------------------------------------------------|
| Reachable       | `200 OK`                  | `{"status": "ok"}`                                |
| Not reachable   | `503 Service Unavailable` | `{"status": "error", "database": "unreachable"}`  |

When the check fails, the reason is logged at `ERROR` level (`Healthcheck failed: ...`). The error details are never sent to the client.

This makes it a good target for a load balancer or orchestrator. A `503` means "don't send traffic to this instance right now".

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

Every error is returned as JSON.

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
| 503    | `/healthcheck` can't reach the database         | `{"status": "error", "database": "unreachable"}`                             |

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
| Healthcheck can't reach the database| `ERROR`   |
| Unhandled exception (with traceback)| `ERROR`   |

Set `LOG_LEVEL` in `.env` to control how much is printed. Inside Docker, Gunicorn also writes one access-log line per request. To follow the API's logs, run:

```bash
docker compose logs -f api
```

---

## Database migrations

The database schema is managed with **Flask-Migrate**, which runs Alembic underneath. Each change to the schema is a versioned script in `migrations/versions/`, so every copy of the database, whether it's SQLite locally or PostgreSQL in Docker, can be brought to the same state.

| Task                                     | Command                                                 |
|------------------------------------------|---------------------------------------------------------|
| Apply all migrations (Docker/PostgreSQL) | `make db-migrate`                                       |
| Apply all migrations (local/SQLite)      | `make migrate`                                          |
| Create a migration after editing a model | `.venv/bin/python -m flask --app app db migrate -m "describe the change"` |
| Undo the last migration (local)          | `.venv/bin/python -m flask --app app db downgrade`      |
| Show the current version (local)         | `.venv/bin/python -m flask --app app db current`        |

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

The tests run locally and use an **in-memory SQLite database**, so they never touch your real data and don't need Docker. Each test gets a fresh, empty database.

| File                  | What it covers                                                                           |
|-----------------------|------------------------------------------------------------------------------------------|
| `conftest.py`         | `app` and `client` fixtures: builds the app with `TESTING=True` and creates and drops the tables around each test |
| `test_health.py`      | `GET /healthcheck` returns 200 and `{"status": "ok"}`                                    |
| `test_students.py`    | Create (201, 400 missing, 400 invalid, 409 duplicate), list, get (200, 404), update and delete |
| `test_validation.py`  | `validate_student_fields()` on its own, including the age boundaries 4, 5, 100 and 101 and text instead of a number |

Current result: **17 passed**.

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
| 16 | Docker image             | Gunicorn, `.dockerignore`, a multi-stage build, a non-root user, semver image tags |
| 17 | PostgreSQL               | The psycopg driver, and a healthcheck that tests the database (`503` when it's down) |
| 18 | Docker Compose           | Two services, a private network, a named volume, `depends_on` with a healthcheck |
| 19 | One-command setup        | `scripts/setup.sh` and Make targets that chain together (`docker-run` → `db-migrate` → `db-up`) |

> **Note:** the notes in `docs/` were written during the early setup stage, when the virtual environment and `requirements.txt` lived inside `app/`. They have since moved back to the project root, where they are now.
