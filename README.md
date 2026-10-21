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
14. [CI pipeline](#ci-pipeline)
15. [Production deploy](#production-deploy)
16. [Deploying on Kubernetes: overview](#deploying-on-kubernetes-overview)
17. [Kubernetes: prerequisites](#kubernetes-prerequisites)
18. [Kubernetes: repository layout](#kubernetes-repository-layout)
19. [Kubernetes: Makefile targets](#kubernetes-makefile-targets)
20. [Kubernetes: first-time setup](#kubernetes-first-time-setup)
21. [Kubernetes: day-to-day operations](#kubernetes-day-to-day-operations)
22. [Kubernetes: troubleshooting](#kubernetes-troubleshooting)
23. [Kubernetes: design decisions](#kubernetes-design-decisions)
24. [Kubernetes: known limitations](#kubernetes-known-limitations)
25. [Learning journey](#learning-journey)

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
| Ruff                 | Linting (rules in `ruff.toml`)                                    |
| Gunicorn             | Production WSGI server (runs the app inside the container)        |
| Docker               | Container image (multi-stage build, non-root user)                |
| Docker Compose       | Runs the API and the database together                            |
| nginx 1.28           | Load balancer in front of two API replicas (production deploy)    |
| Postman / newman     | API smoke tests (`make smoke`)                                    |
| OpenAPI 3.0          | Machine-readable API documentation (`openapi.yml`)                |
| GitHub Actions       | CI pipeline, on a self-hosted runner on AWS EC2                   |
| Amazon ECR           | Container registry for the images CI builds                       |

The exact pinned versions are in [`requirements.txt`](requirements.txt). The development tools (pytest, Ruff) are in [`requirements-dev.txt`](requirements-dev.txt), which also includes `requirements.txt`. The reason for each of the original packages is explained in [docs/02-dependencies.md](docs/02-dependencies.md).

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
├── .github/workflows/
│   └── ci.yml                    ← CI pipeline: build, lint, test, push to ECR
├── deploy/                       ← production setup: nginx + 2 API replicas + PostgreSQL
│   ├── docker-compose.yml        ← db, api1, api2 and nginx
│   ├── .env.example              ← template for deploy/.env
│   ├── nginx/nginx.conf          ← load balancer config
│   └── postman/                  ← smoke-test collection + environment
├── infra/                        ← EC2 setup
│   ├── runner-bootstrap.sh       ← user data: turns a fresh instance into a CI runner host
│   ├── ecr-push-policy.json      ← IAM policy for the runner's instance role
│   └── server-bootstrap.sh       ← user data: prepares the server that runs the production stack
├── scripts/
│   └── setup.sh                  ← checks for (and installs) make and Docker
├── docs/                         ← learning notes written during setup
├── openapi.yml                   ← OpenAPI 3.0 spec for every endpoint
├── Dockerfile                    ← multi-stage image build: builder → slim runtime
├── .dockerignore                 ← files kept out of the image (.env, .venv, tests…)
├── docker-compose.yml            ← development: two services, db (PostgreSQL) and api
├── Makefile                      ← shortcuts for Docker, local development and CI
├── requirements.txt              ← pinned runtime dependencies
├── requirements-dev.txt          ← runtime + dev tools (pytest, ruff)
├── ruff.toml                     ← lint rules
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
make install           # create .venv and install requirements-dev.txt
make migrate           # create the tables in instance/app.db
make run               # dev server on http://localhost:5001, with debug and auto-reload
make test              # run the test suite
```

The local targets use `DATABASE_URL` from `.env`, which is `sqlite:///app.db` by default.

---

## Architecture

This section describes the **development** setup. `docker compose` runs two services, defined in [`docker-compose.yml`](docker-compose.yml). The production setup, with a load balancer and two API replicas, is described in [Production deploy](#production-deploy).

The two development services:

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
| `make install` | Create `.venv` with Python 3.12 and install `requirements-dev.txt` (runtime + pytest + ruff) |
| `make migrate` | Apply database migrations (`flask db upgrade`) to the local database |
| `make run`     | Start the Flask dev server on port 5001 with debug mode on      |
| `make test`    | Run the pytest suite with verbose output                        |
| `make build`   | Run `install`, then byte-compile `app/` to catch syntax errors (used by CI) |
| `make lint`    | Run `ruff check app tests`                                      |
| `make version` | Print `VERSION` (CI uses it for the image tag)                  |

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

## CI pipeline

The pipeline is defined in [`.github/workflows/ci.yml`](.github/workflows/ci.yml). It runs on GitHub Actions, on a **self-hosted runner on AWS EC2**. It builds, lints and tests the code, then pushes a Docker image to **Amazon ECR**.

### Triggers

| Trigger                 | When it runs                                                                    |
|-------------------------|---------------------------------------------------------------------------------|
| `push` to `main`        | Only when the push changes at least one of the paths below                      |
| `workflow_dispatch`     | Manually, from **Actions → CI → Run workflow** on GitHub                        |

**Paths that trigger a run:**

| Path                          | Why it matters                                  |
|-------------------------------|-------------------------------------------------|
| `app/**`                      | Application code                                |
| `tests/**`                    | Tests                                           |
| `migrations/**`               | Database schema                                 |
| `requirements*.txt`           | `requirements.txt` and `requirements-dev.txt`   |
| `Dockerfile`                  | The image build                                 |
| `Makefile`                    | The commands CI runs (and the image `VERSION`)  |
| `ruff.toml`                   | Lint rules                                      |
| `.github/workflows/ci.yml`    | The pipeline itself                             |

Changes to documentation alone (`README.md`, `docs/`, `openapi.yml`) or to files outside the list (`docker-compose.yml`, `deploy/`, `scripts/`, `infra/`) **don't** start a run. To build after such a change, trigger it manually.

The workflow has read-only access to the repository (`permissions: contents: read`).

### Stages

All stages run in order in one job (`ci`). If any stage fails, the job stops.

| # | Stage                    | Command                         | What it does                                                                   |
|---|--------------------------|---------------------------------|--------------------------------------------------------------------------------|
| 1 | Check out the code       | `actions/checkout@v5`           | Fetches the commit being built                                                 |
| 2 | Set up Python 3.12       | `actions/setup-python@v5`       | Makes Python 3.12 available on the runner                                      |
| 3 | Build API                | `make build`                    | Creates `.venv`, installs `requirements-dev.txt`, byte-compiles `app/` to catch syntax errors |
| 4 | Lint                     | `make lint`                     | Runs `ruff check app tests` with the rules in `ruff.toml`                      |
| 5 | Run tests                | `make test`                     | Runs the pytest suite against in-memory SQLite                                 |
| 6 | Docker login to ECR      | `aws ecr get-login-password`    | Looks up the AWS account ID, works out the registry URL and logs Docker in to ECR |
| 7 | Docker build and push    | `docker build` / `docker push`  | Builds and pushes the image, unless that tag already exists (see below)        |

The image is only pushed if the build, lint and tests all pass.

### Self-hosted runner on EC2

The job runs on `runs-on: [self-hosted, ec2]`, which means a runner registered with the **`ec2`** label.

- **The host:** an Ubuntu 24.04 EC2 instance (x86_64, since the bootstrap installs the x86_64 AWS CLI).
- **What gets installed on first boot:** make, git, Python 3.12 venv support, Docker and AWS CLI v2. This is done by [`infra/runner-bootstrap.sh`](infra/runner-bootstrap.sh), which runs as EC2 user data.
- **AWS access comes from an IAM instance role, not stored keys.** The instance has an IAM role attached through its instance profile. The AWS CLI picks up short-lived credentials from it automatically. There are **no AWS access keys** stored in GitHub secrets or on the runner.
- **What the role allows:** it has [`infra/ecr-push-policy.json`](infra/ecr-push-policy.json) attached. It allows `ecr:GetAuthorizationToken` (for `docker login`), plus checking for, pushing and reading images in the `student-api` repository only. It has no other AWS permissions.
- **Region:** `us-east-1`, set as `AWS_REGION` in the workflow.

### ECR image tags

Images are pushed to:

```
<account-id>.dkr.ecr.us-east-1.amazonaws.com/student-api:<version>-<commit>
```

| Part        | Comes from                                         | Example   |
|-------------|----------------------------------------------------|-----------|
| `<version>` | `VERSION` in the Makefile (read with `make -s version`) | `1.1.0` |
| `<commit>`  | The first 7 characters of the commit SHA (`GITHUB_SHA`) | `78d5261` |

So an image looks like `student-api:1.1.0-78d5261`. **There is never a `latest` tag.**

- **Immutable tags.** The ECR repository has tag immutability turned on, so once a tag has been pushed, it can never be overwritten. Each tag always points at exactly one image, built from exactly one commit.
- **Skipped if it already exists.** Before building, the pipeline checks ECR with `aws ecr describe-images`:
  - **The tag exists:** it logs `Image <tag> already exists in ECR, nothing to push` and ends successfully. This happens when you re-run the workflow on the same commit. Without the check, the push would fail because the tag is immutable.
  - **`ImageNotFoundException`:** the tag is new, so it builds and pushes.
  - **Any other error,** such as missing permissions or a wrong region: it prints the error and **fails the job**, so a real problem is never mistaken for "not found".
- **Releasing a new version:** bump `VERSION` in the Makefile. Every commit after that gets tags starting with the new version.

### Setup files in `infra/`

| File                                                       | What it is                                                                 |
|------------------------------------------------------------|----------------------------------------------------------------------------|
| [`infra/runner-bootstrap.sh`](infra/runner-bootstrap.sh)   | EC2 **user data** script. It runs once as root on first boot and installs make, git, Python 3.12 venv, Docker and AWS CLI v2. It adds `ubuntu` to the `docker` group, creates `/home/ubuntu/actions-runner`, and writes `/home/ubuntu/BOOTSTRAP_DONE` when finished. Its output goes to `/var/log/cloud-init-output.log`. |
| [`infra/ecr-push-policy.json`](infra/ecr-push-policy.json) | The **IAM policy** for the runner's instance role. It covers logging in to ECR and checking for, pushing and pulling images, limited to the `student-api` repository in `us-east-1`. |

`infra/` also holds [`server-bootstrap.sh`](infra/server-bootstrap.sh), which sets up the server that *runs* the app. It isn't part of the pipeline. See [Production deploy](#production-deploy).

### Setting up the pipeline from scratch

1. **Create the ECR repository** with immutable tags:
   ```bash
   aws ecr create-repository --repository-name student-api \
     --image-tag-mutability IMMUTABLE --region us-east-1
   ```
2. **Create an IAM role** for EC2, attach `infra/ecr-push-policy.json` to it as a policy, and wrap it in an instance profile.
3. **Launch an EC2 instance:** Ubuntu 24.04 on x86_64, with that instance profile attached and `infra/runner-bootstrap.sh` pasted in as **user data**. Wait until `/home/ubuntu/BOOTSTRAP_DONE` exists.
4. **Register the runner by hand.** This step can't be automated, because it needs a short-lived token from GitHub.
   1. On GitHub, go to **Settings → Actions → Runners → New self-hosted runner** and choose Linux / x64.
   2. On the instance, as `ubuntu`, run the download and `./config.sh` commands GitHub shows, inside `/home/ubuntu/actions-runner`. Add `--labels ec2` to `./config.sh`.
   3. Install it as a service so it survives reboots: `sudo ./svc.sh install ubuntu && sudo ./svc.sh start`.
5. **Run the workflow** from **Actions → CI → Run workflow**, and check that the image shows up in ECR.

---

## Production deploy

[`deploy/`](deploy/) holds a production-style setup: **two API replicas behind an nginx load balancer**, with PostgreSQL behind them. It is separate from the development `docker-compose.yml` in the project root and has its own Compose project, `student-api-prod`.

```
deploy/
├── docker-compose.yml                       ← db, api1, api2 and nginx
├── .env.example                             ← template for deploy/.env
├── nginx/
│   └── nginx.conf                           ← load balancer config
└── postman/
    ├── student-api.postman_collection.json  ← 6 requests with tests
    └── local.postman_environment.json       ← base_url = http://localhost:8080
```

### Architecture

```
   you ──▶ localhost:8080 ──▶ ┌───────┐ ──▶ api1:5000 ──┐
                              │ nginx │                  ├──▶ db:5432 ──▶ volume: pgdata
                              └───────┘ ──▶ api2:5000 ──┘
                                 (the only published port)
```

| Service | Image                     | Role                                                                    |
|---------|---------------------------|-------------------------------------------------------------------------|
| `nginx` | `nginx:1.28-alpine`       | The only service exposed to the host: port **8080** → container port 80. Spreads requests across both replicas. |
| `api1`  | `student-api:<VERSION>`   | API replica 1. This is the service that builds the image.               |
| `api2`  | `student-api:<VERSION>`   | API replica 2. It reuses the image `api1` built, so nothing is built twice. |
| `db`    | `postgres:17-alpine`      | PostgreSQL, with data in the named volume `pgdata`. The port is **not** published. |

- **Round-robin balancing.** The `upstream student_api` block in `nginx.conf` lists `api1:5000` and `api2:5000`. nginx alternates between them by default.
- **Failover.** `proxy_next_upstream error timeout http_502 http_503` retries a failed request on the other replica, and `proxy_connect_timeout 2s` makes a dead replica fail fast instead of hanging. A client doesn't see an error just because one replica is down.
- **See which replica answered.** Every response has an `X-Upstream` header with the address of the replica that served it.
- **Healthchecks.** Each API replica checks its own `/healthcheck` (which tests the database) every 10 seconds, and is marked unhealthy after 3 failures. nginx only starts once **both** replicas are healthy, and the replicas only start once the database is healthy.
- **Self-healing.** All services use `restart: unless-stopped`, so they come back after a crash or a server reboot, unless you stopped them yourself.
- **Image version.** Like the development setup, the image tag comes from `VERSION` in the Makefile, so use the `make` targets below rather than plain `docker compose`.

### Configuration

```bash
cp deploy/.env.example deploy/.env
```

| Variable            | Description                                                     |
|---------------------|-----------------------------------------------------------------|
| `POSTGRES_USER`     | PostgreSQL username                                             |
| `POSTGRES_PASSWORD` | PostgreSQL password. **Replace the placeholder with a strong password.** |
| `POSTGRES_DB`       | PostgreSQL database name                                        |
| `LOG_LEVEL`         | `DEBUG`, `INFO`, `WARNING` or `ERROR`                           |

Unlike the development setup, the production compose file has **no default values**, so every variable must be set in `deploy/.env`. This file is ignored by git (the `.env` rule in `.gitignore` matches it), so your real password is never committed. The two API replicas share one `DATABASE_URL`, which is built from the `POSTGRES_*` values.

### Make targets

| Target              | Depends on                | What it does                                                                |
|---------------------|---------------------------|-----------------------------------------------------------------------------|
| `make prod-build`   | none                      | Builds the API image (`student-api:<VERSION>`) through `api1`.              |
| `make prod-db`      | none                      | Starts PostgreSQL and waits until it is healthy.                            |
| `make prod-migrate` | `prod-db`                 | Applies the database migrations in a one-off container.                     |
| `make deploy`       | `prod-build`, `prod-migrate` | Runs both, then starts the whole stack in the background.               |
| `make prod-ps`      | none                      | Shows each service and its health.                                          |
| `make prod-logs`    | none                      | Follows the logs. Add `SVC=api1` for one service.                           |
| `make prod-stop`    | none                      | Stops the given service: `make prod-stop SVC=api1`. Without `SVC`, it stops everything. |
| `make prod-start`   | none                      | Starts it again: `make prod-start SVC=api1`.                                |
| `make prod-down`    | none                      | Stops and removes the containers. The `pgdata` volume is **kept**.          |
| `make smoke`        | none                      | Runs the Postman collection against `http://localhost:8080` with newman.    |

**Dependency chain:**

```
make deploy
├── prod-build            build the API image
└── prod-migrate          apply migrations
    └── prod-db           start PostgreSQL and wait until healthy
then: start db, api1, api2 and nginx
```

### Deploying

```bash
cp deploy/.env.example deploy/.env    # then edit it and set a real password
make deploy
make prod-ps                          # wait until api1, api2 and db show "healthy"
curl -i http://localhost:8080/healthcheck
```

The response should be `200` with `{"status": "ok"}` and an `X-Upstream` header.

### Smoke tests (Postman / newman)

```bash
make smoke
```

This runs [`student-api.postman_collection.json`](deploy/postman/student-api.postman_collection.json) with **newman**. The environment file points it at `http://localhost:8080`, so every request goes through nginx.

| # | Request          | Method and path                           |
|---|------------------|-------------------------------------------|
| 1 | Healthcheck      | `GET /healthcheck`                        |
| 2 | Create Student   | `POST /api/v1/students`                   |
| 3 | List Students    | `GET /api/v1/students`                    |
| 4 | Get student      | `GET /api/v1/students/{{student_id}}`     |
| 5 | Update student   | `PATCH /api/v1/students/{{student_id}}`   |
| 6 | Delete student   | `DELETE /api/v1/students/{{student_id}}`  |

Each request has tests that check the response. The student created in step 2 is stored in the `student_id` variable and used by steps 4–6, and step 6 deletes it again.

`make smoke` needs **Node.js** because it runs newman through `npx`. To use the collection in the Postman app instead, import both files from `deploy/postman/`.

### Trying out failover

```bash
make prod-stop SVC=api1               # take one replica down
curl -si http://localhost:8080/healthcheck | grep -i x-upstream
make prod-start SVC=api1              # bring it back
```

While `api1` is stopped, requests still succeed and every `X-Upstream` points at `api2`.

### Preparing the server: `infra/server-bootstrap.sh`

[`infra/server-bootstrap.sh`](infra/server-bootstrap.sh) is EC2 **user data** for the machine that runs the stack. On first boot it runs as root and:

1. Installs `make`, `git` and `curl`.
2. Installs Docker with the `get.docker.com` script (skipped if Docker is already there), and enables it at boot.
3. Adds the `ubuntu` user to the `docker` group.
4. Prints the Docker, Docker Compose and make versions, so you can see them in the boot log.
5. Creates `/home/ubuntu/BOOTSTRAP_DONE` when it has finished.

It doesn't fetch the code or start anything. After the file appears, log in and run [Deploying](#deploying): clone the repository, create `deploy/.env` and run `make deploy`. This is a different script from `infra/runner-bootstrap.sh`, which prepares the [CI runner](#self-hosted-runner-on-ec2).

---

## Deploying on Kubernetes: overview

The API and its Postgres database run on a local multi-node Kubernetes cluster, created with **kind**.

Database credentials are **not** stored in Git and are **not** created by hand. They live in **HashiCorp Vault**. The **External Secrets Operator (ESO)** copies them into a Kubernetes Secret automatically.

```
kind cluster "student-api" (Kubernetes v1.37.0)
├── control-plane node            (tainted: no app workloads)
├── worker   label type=application         → namespace student-api: 2 API pods
├── worker2  label type=database            → namespace student-api: 1 Postgres pod + 1Gi PVC
└── worker3  label type=dependent_services  → namespace vault: Vault
                                            → namespace external-secrets: ESO (3 pods)

Secret flow:
Vault KV path secret/student-api/db
   → ESO logs in with Kubernetes auth (service account "eso-vault", role "student-api", read-only policy)
   → ESO creates Kubernetes Secret "db-credentials" in namespace student-api
   → Postgres and API pods read it as environment variables

Traffic: your Mac localhost:8080 → kind port mapping → NodePort 30080 → Service "student-api" → API pods (port 5000)
The database Service "db" is ClusterIP (internal only).
```

---

## Kubernetes: prerequisites

| Tool            | Notes                                                    |
|-----------------|----------------------------------------------------------|
| Docker Desktop  | Give it at least 8 GB of memory.                         |
| kind            | Creates the cluster.                                     |
| kubectl         | Talks to the cluster.                                    |
| Helm            | Installs Vault and ESO.                                  |
| jq              | Reads the Vault init file.                               |
| openssl         | Generates the database password.                         |
| Node.js         | Needed for `npx` / newman (`make smoke`).                |

On macOS, install them with:

```bash
brew install kind kubernetes-cli helm jq node
```

Add the Helm repos once:

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
```

---

## Kubernetes: repository layout

| Path | What it holds |
|------|---------------|
| [`infra/k8s/kind-config.yaml`](infra/k8s/kind-config.yaml) | kind cluster: 1 control plane + 3 labelled workers, pinned node image, port mapping host 8080 → node 30080 on the application worker. |
| [`helm/student-api/`](helm/student-api/) | Own chart: ConfigMap, Deployment (init container `migrate`), Service (NodePort 30080). |
| [`helm/postgres/`](helm/postgres/) | Own chart: ServiceAccount `eso-vault`, SecretStore `vault-backend`, ExternalSecret `db-credentials`, PVC `<release>-data` (kept on uninstall), Deployment, Service `db`. |
| [`helm/vault/`](helm/vault/) | Official HashiCorp chart 0.34.1, vendored with `helm pull --untar`. |
| [`helm/external-secrets/`](helm/external-secrets/) | Official ESO chart 2.13.0, vendored. |
| [`helm/values/vault.yaml`](helm/values/vault.yaml), [`helm/values/external-secrets.yaml`](helm/values/external-secrets.yaml) | Our settings for the vendored charts. |
| [`helm/values/vault-student-api-policy.hcl`](helm/values/vault-student-api-policy.hcl) | Vault read-only policy. |

The `k8s/` manifests were removed. They remain in Git history.

---

## Kubernetes: Makefile targets

| Target              | What it does                                                                                  |
|---------------------|-----------------------------------------------------------------------------------------------|
| `make cluster-up`   | Creates the kind cluster from `infra/k8s/kind-config.yaml`. Skips if it already exists.       |
| `make cluster-down` | Deletes the kind cluster.                                                                     |
| `make docker-build` | Builds the API image `student-api:1.1.0`.                                                     |
| `make helm-platform` | Installs or upgrades Vault and ESO from the vendored charts.                                |
| `make vault-unseal` | Unseals Vault using the key saved in `~/.vault-lab/init.json`.                                |
| `make helm-lint`    | Lints the `postgres` and `student-api` charts.                                                |
| `make helm-deploy`  | Runs `helm-lint`, loads the image into kind, then runs `helm upgrade --install postgres`, then `student-api` with `image.tag=$(VERSION)`. |
| `make smoke`        | Runs the Postman collection with Newman against `http://localhost:8080`.                      |

---

## Kubernetes: first-time setup

Use these steps on a fresh cluster.

### Step 1: Cluster and image

```bash
make cluster-up
make docker-build
```

### Step 2: Vault and ESO

```bash
make helm-platform
kubectl -n vault get pods
```

`vault-0` shows `0/1` until it is unsealed. This is expected.

### Step 3: Initialize and unseal Vault

Do this once per new cluster.

```bash
mkdir -p ~/.vault-lab && chmod 700 ~/.vault-lab
kubectl -n vault exec vault-0 -- vault operator init -key-shares=1 -key-threshold=1 -format=json > ~/.vault-lab/init.json
chmod 600 ~/.vault-lab/init.json
make vault-unseal
kubectl -n vault exec vault-0 -- vault status
```

Expect `Sealed false` in the output of `vault status`.

> **Warning:** `~/.vault-lab/init.json` contains the unseal key and the root token. Never commit or share it. If it is lost, Vault's data cannot be recovered.

### Step 4: Configure Vault

Do this once per new cluster. Run all of it in the same terminal.

```bash
ROOT_TOKEN=$(jq -r '.root_token' ~/.vault-lab/init.json)
vault_cmd() { kubectl -n vault exec vault-0 -- env VAULT_TOKEN="$ROOT_TOKEN" vault "$@"; }

vault_cmd secrets enable -path=secret kv-v2
vault_cmd kv put secret/student-api/db POSTGRES_USER=student POSTGRES_PASSWORD="$(openssl rand -hex 16)" POSTGRES_DB=studentdb

vault_cmd auth enable kubernetes
vault_cmd write auth/kubernetes/config kubernetes_host="https://kubernetes.default.svc:443"
kubectl -n vault exec -i vault-0 -- env VAULT_TOKEN="$ROOT_TOKEN" vault policy write student-api-read - < helm/values/vault-student-api-policy.hcl
vault_cmd write auth/kubernetes/role/student-api bound_service_account_names=eso-vault bound_service_account_namespaces=student-api policies=student-api-read ttl=1h
```

> **Note:** Postgres sets its password only when its data volume is first created. If the database already exists, the password in Vault must match the existing one. Do not generate a new one.

### Step 5: Deploy the app

```bash
make helm-deploy
kubectl -n student-api get pods -o wide
```

### Step 6: Verify

```bash
kubectl -n student-api get secretstore,externalsecret
curl -si http://localhost:8080/healthcheck | head -1
make smoke
```

Expected results:

| Command | Expect |
|---------|--------|
| `kubectl -n student-api get secretstore,externalsecret` | SecretStore `Valid`. ExternalSecret `SecretSynced`, READY `True`. |
| `curl -si http://localhost:8080/healthcheck \| head -1` | `HTTP/1.1 200 OK` |
| `make smoke` | 0 failures |

---

## Kubernetes: day-to-day operations

### Pause

Quit Docker Desktop. All data is kept.

### Resume

```bash
docker start student-api-control-plane student-api-worker student-api-worker2 student-api-worker3
make vault-unseal
kubectl -n student-api get pods
```

Vault is always sealed after a restart, so run `make vault-unseal` every time.

### Remove the API only

This keeps the database.

```bash
helm uninstall student-api -n student-api
```

The charts do not create the Namespace, so `helm uninstall` does not delete it.

> **Warning:** deleting the ExternalSecret also deletes the Secret `db-credentials`. ESO owns it (`creationPolicy: Owner`).

### Rotate the database password

> **TODO:** not covered yet. Changing the password in Vault alone does not change Postgres's password.

### Helm operations

List all releases:

```bash
helm list -A
```

Show the revision history of the API release:

```bash
helm history student-api -n student-api
```

Roll back to an earlier revision:

```bash
helm rollback student-api <REVISION> -n student-api --wait
```

Render the manifests without installing anything:

```bash
helm template student-api helm/student-api --set replicaCount=3
```

Change a setting and upgrade:

```bash
helm upgrade --install student-api helm/student-api -n student-api --set config.LOG_LEVEL=DEBUG --wait
```

The pods restart automatically because of the `checksum/config` annotation.

Remove the app only:

```bash
helm uninstall student-api -n student-api
```

> **Note:** `helm uninstall postgres` keeps the PVC (annotation `helm.sh/resource-policy: keep`), so the data survives.

---

## Kubernetes: troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `vault-0` is `0/1 Running` | Vault is sealed. | `make vault-unseal` |
| ExternalSecret shows `SecretSyncedError` | Vault is sealed, or the path or permission is wrong. | `kubectl -n student-api describe externalsecret db-credentials` and read the Events. |
| Pod shows `CreateContainerConfigError` | The Secret `db-credentials` is missing. | Check the ExternalSecret status. |
| `ErrImageNeverPull` or `ImagePullBackOff` | The image is not in the kind nodes. | `make docker-build && make k8s-load` |
| Port 8080 is already in use | The Docker Compose prod stack is running. | `make prod-down` |
| An API pod shows 1 restart on the first deploy | Both replicas ran the migration init container at the same time. | Harmless. See [Kubernetes: known limitations](#kubernetes-known-limitations). |

---

## Kubernetes: design decisions

- **kind instead of minikube.** The whole cluster is declared in one YAML file kept in Git.
- **Control plane plus 3 labelled workers.** kind taints the control plane, so apps need their own nodes.
- **Postgres is pinned to the database node.** Its disk (a local-path PVC) lives on that node.
- **Recreate strategy for Postgres.** There are never two Postgres processes on one disk.
- **Two different probes.** The liveness probe checks only the TCP port, so a database outage does not restart every API pod. The readiness probe checks `/healthcheck` and removes a pod from traffic when the database is unreachable.
- **Settings in two places.** Non-secret settings are in a ConfigMap. `DATABASE_URL` is built from the Secret's variables, so the password lives in one place.
- **Vault is set up like a real service.** It runs in standalone mode with persistent storage (not dev mode). It uses Kubernetes auth, so no tokens are stored. The policy is read-only (least privilege).
- **ESO instead of the Vault Secrets Operator.** ESO supports many providers (for example AWS Secrets Manager). Switching provider only changes the SecretStore.

### Helm design decisions

- **Own charts for the API and Postgres.** Community charts for Vault and ESO, vendored into `helm/` and pinned.
- **One source of truth for the image version.** The image tag defaults to the chart `appVersion` and is overridden with `--set image.tag=$(VERSION)`.
- **Charts do not create the Namespace.** Helm uses `--namespace` / `--create-namespace`. This fixes the old risk of deleting the namespace by deleting a manifest file.
- **Standard `app.kubernetes.io` labels.** **TODO:** the rest of this bullet was cut off in the source text. Complete it.

---

## Kubernetes: known limitations

This is a lab setup, not a production one.

- **Vault TLS is disabled** (`tls_disable = 1`). Production must use TLS.
- **One unseal key is stored on the laptop.** Production uses several key shares or cloud KMS auto-unseal.
- **The root token is used for the initial configuration.** Production would revoke it afterwards.
- **The migration runs as an init container in every API pod** (required by the bootcamp). With two replicas, they can race on the first deploy. A Kubernetes Job is the cleaner pattern.

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
| 20 | Linting                  | Ruff, and separating runtime from dev dependencies (`requirements-dev.txt`) |
| 21 | CI pipeline              | GitHub Actions on a self-hosted EC2 runner, an IAM instance role, immutable `<version>-<commit>` tags in ECR |
| 22 | Production deploy        | An nginx load balancer, two API replicas, container healthchecks, failover, Postman/newman smoke tests and a server bootstrap script |

> **Note:** the notes in `docs/` were written during the early setup stage, when the virtual environment and `requirements.txt` lived inside `app/`. They have since moved back to the project root, where they are now.
