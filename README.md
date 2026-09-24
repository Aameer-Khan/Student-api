# Student-api

A learning project: building a REST API for managing students with Flask.

## Progress so far

- [x] Created the repo and `.gitignore`
- [x] Set up a Python 3.12 virtual environment
- [x] Installed dependencies and pinned them in `app/requirements.txt`
- [x] Planned the Student schema and its validation rules
- [x] Organized the repo into folders (`app/`, `docs/`)

## Project structure

```
student-api/
├── README.md              ← you are here: overview + progress
├── .gitignore             ← files git should ignore (applies to every folder)
├── app/                   ← the Python service
│   ├── requirements.txt   ← pinned package list
│   └── .venv/             ← virtual environment (not committed)
└── docs/                  ← learning notes, in order
    ├── 01-environment-setup.md
    ├── 02-dependencies.md
    └── 03-student-schema.md
```

### Why it's organized this way

- **`app/`** holds everything that belongs to the Python service. Later, its source code, tests and **Dockerfile** will live here too. A Docker build can only use files inside the folder it builds from, so keeping the Dockerfile in `app/` means the image gets just the app.
- **`docs/`** holds notes about the project, kept apart from the code.
- **Root level:** only files about the whole repo (`README.md`, `.gitignore`).
- **Later:** deployment files (Kubernetes manifests, `docker-compose.yml`) will go in a separate `deploy/` folder. It will be created when it's first needed.

## Notes

1. [Environment setup](docs/01-environment-setup.md): Python 3.12, the virtual environment and `.gitignore`
2. [Dependencies](docs/02-dependencies.md): what each package in `app/requirements.txt` does
3. [Student schema](docs/03-student-schema.md): the fields, validation rules and the reasons behind them

## Quick start

Run from the repo root:

```bash
python3.12 -m venv app/.venv
source app/.venv/bin/activate
pip install -r app/requirements.txt
```
