# CampusCare — Flask + SQLite

A premium responsive campus complaint-management portal built with **Python, Flask, SQLite, SQLAlchemy, Flask-Login, Werkzeug password hashing, Bootstrap 5, Font Awesome, Chart.js, HTML5, CSS3, and vanilla JavaScript**.

## Run in Visual Studio Code

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Demo accounts

- Student: `aarav@college.edu` / `campus-demo`
- Admin: `admin@college.edu` / `admin-demo`

## Routes

- `/login` — Student/Admin role-aware login
- `/student` — Student dashboard and complaint submission
- `/admin` — Admin metrics, queue, filters, and assignment actions
- `/logout` — End the session

## Notes

The SQLite database is created automatically as `campuscare.db` on first run. Uploaded evidence is stored in `uploads/`. Change `SECRET_KEY` in a production environment. The current project includes a clear, explainable Python rule engine for smart priority and token/sequence similarity duplicate hints.

## Test

```bash
pytest -q
```
