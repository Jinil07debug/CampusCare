import os
import re
from datetime import datetime
from difflib import SequenceMatcher

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "doc", "docx"}
configured_database_url = os.environ.get("FLASK_DATABASE_URL") or os.environ.get("DATABASE_URL", "")
database_url = configured_database_url if configured_database_url.startswith("sqlite") else "sqlite:///campuscare.db"

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "campuscare-dev-secret-change-me"),
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_FOLDER=UPLOAD_FOLDER,
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.template_filter("format_number")
def format_number(value):
    return f"{int(value):02d}"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to access your workspace."


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    credibility_score = db.Column(db.Integer, default=92)
    complaints = db.relationship("Complaint", backref="reporter", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), nullable=False)
    location = db.Column(db.String(160), nullable=False)
    noticed_date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="Pending verification")
    priority = db.Column(db.String(20), nullable=False, default="Medium")
    evidence_filename = db.Column(db.String(255))
    rejection_reason = db.Column(db.Text)
    resolution_evidence = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def calculate_priority(category, urgency, safety, people_affected):
    score = max(0, int(urgency or 0)) + min(4, max(0, int(people_affected or 0)) // 25)
    if safety:
        score += 4
    if category in {"Safety", "Electrical", "Infrastructure"}:
        score += 1
    if score >= 8:
        return "Critical"
    if score >= 5:
        return "High"
    if score >= 2:
        return "Medium"
    return "Low"


def complaint_similarity(left, right):
    tokens_left = set(re.findall(r"[a-z0-9]{3,}", left.lower()))
    tokens_right = set(re.findall(r"[a-z0-9]{3,}", right.lower()))
    if not tokens_left or not tokens_right:
        return 0
    overlap = len(tokens_left & tokens_right) / len(tokens_left | tokens_right)
    return max(overlap, SequenceMatcher(None, left.lower(), right.lower()).ratio() * 0.45)


def seed_data():
    if User.query.count():
        return
    student = User(name="Aarav Mehta", email="aarav@college.edu", role="student", credibility_score=92)
    student.set_password("campus-demo")
    admin = User(name="Admin Desk", email="admin@college.edu", role="admin", credibility_score=100)
    admin.set_password("admin-demo")
    db.session.add_all([student, admin])
    db.session.flush()
    samples = [
        ("Projector not working in C-204", "The lecture projector powers on but shows no signal.", "IT & AV", "C Block · Room 204", "2026-09-21", "Assigned", "High", student.id),
        ("Water leakage near the north stairs", "Water is pooling near the north stairwell and may be a safety risk.", "Infrastructure", "Main Building · North stairwell", "2026-09-20", "In progress", "Critical", student.id),
        ("Dustbins overflowing after fest week", "Waste bins need collection near the student commons.", "Cleanliness", "Student Commons · Ground floor", "2026-09-18", "Resolved", "Medium", student.id),
        ("Three corridor lights are flickering", "The east wing lights flicker after 6 PM.", "Electrical", "Library · 2nd floor east wing", "2026-09-16", "Under review", "Medium", student.id),
    ]
    for row in samples:
        db.session.add(Complaint(title=row[0], description=row[1], category=row[2], location=row[3], noticed_date=row[4], status=row[5], priority=row[6], user_id=row[7]))
    db.session.commit()


@app.context_processor
def inject_globals():
    return {"app_name": "CampusCare", "year": datetime.utcnow().year}


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard" if current_user.role == "admin" else "student_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "student")
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        requested_role = request.form.get("role", "student")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.role == requested_role:
            login_user(user, remember=bool(request.form.get("remember")))
            return redirect(url_for("admin_dashboard" if user.role == "admin" else "student_dashboard"))
        flash("Use a valid account for the selected workspace. Demo: aarav@college.edu / campus-demo", "error")
        role = requested_role
    return render_template("login.html", role=role)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.route("/student")
@login_required
def student_dashboard():
    if current_user.role != "student":
        return redirect(url_for("admin_dashboard"))
    complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    return render_template("student.html", complaints=complaints, active="Overview")


@app.route("/complaints/create", methods=["POST"])
@login_required
def create_complaint():
    if current_user.role != "student":
        return redirect(url_for("admin_dashboard"))
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "Infrastructure")
    location = request.form.get("location", "Main Building")
    if not title or not description:
        flash("Title and description are required.", "error")
        return redirect(url_for("student_dashboard"))
    duplicates = Complaint.query.filter(Complaint.category == category).all()
    if any(complaint_similarity(title, item.title) >= 0.6 for item in duplicates):
        flash("A similar complaint already exists. Please review the campus issue queue first.", "error")
        return redirect(url_for("student_dashboard"))
    evidence = request.files.get("evidence")
    filename = None
    if evidence and evidence.filename and allowed_file(evidence.filename):
        filename = secure_filename(f"{current_user.id}_{datetime.utcnow().timestamp()}_{evidence.filename}")
        evidence.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    priority = calculate_priority(category, request.form.get("urgency", 1), request.form.get("safety") == "on", request.form.get("people_affected", 10))
    db.session.add(Complaint(title=title, description=description, category=category, location=location, noticed_date=request.form.get("noticed_date", datetime.utcnow().date().isoformat()), priority=priority, evidence_filename=filename, user_id=current_user.id))
    db.session.commit()
    flash("Complaint submitted for admin verification.", "success")
    return redirect(url_for("student_dashboard"))


@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("student_dashboard"))
    priority = request.args.get("priority", "All priorities")
    query = Complaint.query.order_by(Complaint.created_at.desc())
    if priority != "All priorities":
        query = query.filter_by(priority=priority)
    complaints = query.all()
    all_complaints = Complaint.query.all()
    stats = {"total": len(all_complaints), "critical": sum(c.priority == "Critical" for c in all_complaints), "resolved": round((sum(c.status == "Resolved" for c in all_complaints) / len(all_complaints) * 100) if all_complaints else 0), "open": sum(c.status != "Resolved" for c in all_complaints)}
    return render_template("admin.html", complaints=complaints, stats=stats, priority=priority)


@app.route("/admin/complaints/<int:complaint_id>/assign", methods=["POST"])
@login_required
def assign_complaint(complaint_id):
    if current_user.role != "admin":
        return redirect(url_for("student_dashboard"))
    complaint = db.get_or_404(Complaint, complaint_id)
    complaint.status = "Assigned"
    db.session.commit()
    flash(f"{complaint.title} assigned to the selected campus team.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/uploads/<path:filename>")
@login_required
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


with app.app_context():
    db.create_all()
    seed_data()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
