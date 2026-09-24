# 01 — Environment Setup

## Python version

This project uses **Python 3.12** (3.12.14, installed with Homebrew).

The git history has a commit called *"Rebuild venv on python3.12"*. The virtual environment was deleted and recreated on 3.12 so that everyone working on the project uses the same Python version.

## Virtual environment (`app/.venv/`)

A **virtual environment** is a private folder of Python packages for this one project.

**Why use one?**
- Packages installed here don't clash with other projects or with the system's Python.
- Each project can have its own package versions.
- The whole thing can be deleted and rebuilt from `requirements.txt` at any time.

It lives inside `app/`, next to `requirements.txt`, because it belongs to the Python service. See [README → Project structure](../README.md#project-structure).

**How it was created** (from the repo root):

```bash
python3.12 -m venv app/.venv
```

**How to turn it on (activate it)** each time you open a new terminal:

```bash
source app/.venv/bin/activate
```

Once it's active, your prompt shows `(.venv)`, and `python` and `pip` use this project's packages.

**How to turn it off:**

```bash
deactivate
```

> **Note:** a virtual environment can't be moved. It stores full file paths inside it. To change where it lives, delete it and create it again in the new place.

## Why `.venv/` is not in git

`.venv` is listed in `.gitignore`. It is large, it only works on the machine that built it, and it can be rebuilt from `app/requirements.txt` whenever you need it. Git only tracks the *list* of packages, not the packages themselves.

## `.gitignore`

This is the standard GitHub template for Python projects. It tells git to ignore files that shouldn't be committed, including:
- `.venv`, the virtual environment (this matches `app/.venv` too)
- `__pycache__/` and `*.pyc`, compiled Python files that Python creates on its own
- `.env`, which holds secrets and local settings
- `instance/` and `db.sqlite3`, local database files
- `.pytest_cache/`, leftovers from test runs
