# 02 — Dependencies (`app/requirements.txt`)

`app/requirements.txt` lists every package installed in `app/.venv`, each pinned to an exact version with `==`. Pinning means anyone who installs from this file gets exactly the same setup.

**How it was generated** (from the repo root, with the venv active):

```bash
pip freeze > app/requirements.txt
```

**How to install from it** (from the repo root, for example on a new machine):

```bash
pip install -r app/requirements.txt
```

## Packages that were chosen on purpose (direct)

| Package              | What it's for                                                                                   |
|----------------------|-------------------------------------------------------------------------------------------------|
| **Flask**            | A lightweight web framework for building the API                                                |
| **Flask-SQLAlchemy** | Connects Flask to SQLAlchemy so Python classes can be used as database tables                   |
| **Flask-Migrate**    | Tracks and applies changes to the database structure over time ("migrations")                   |
| **pytest**           | Runs automated tests                                                                            |
| **python-dotenv**    | Loads settings from a `.env` file into environment variables                                    |

## Packages that came along with them (dependencies of dependencies)

You never installed these yourself. `pip` added them because the packages above need them.

| Package                | Pulled in by             | What it does                                      |
|------------------------|--------------------------|---------------------------------------------------|
| Werkzeug               | Flask                    | Low-level HTTP handling: requests, responses, dev server |
| Jinja2                 | Flask                    | Template engine                                   |
| MarkupSafe             | Flask / Jinja2           | Escapes text safely for HTML                      |
| itsdangerous           | Flask                    | Signs data securely (for example, session cookies) |
| click                  | Flask                    | Powers the `flask` command-line tool              |
| blinker                | Flask                    | Signals/events inside Flask                       |
| SQLAlchemy             | Flask-SQLAlchemy         | The database toolkit / ORM                        |
| typing_extensions      | SQLAlchemy, alembic      | Newer typing features                             |
| alembic                | Flask-Migrate            | The migration engine underneath Flask-Migrate     |
| Mako                   | alembic                  | Templates used to generate migration files        |
| iniconfig              | pytest                   | Reads pytest config files                         |
| pluggy                 | pytest                   | pytest's plugin system                            |
| packaging              | pytest                   | Handles version numbers                           |
| Pygments               | pytest                   | Colors the test output                            |

**Why keep them in the file?** Pinning the indirect packages too means installs are exactly repeatable. A new version of Werkzeug, for example, can't sneak in and break something.
