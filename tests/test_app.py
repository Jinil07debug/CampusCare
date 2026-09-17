import pytest

from app import app, db, User, calculate_priority, complaint_similarity


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.app_context():
        db.drop_all()
        db.create_all()
        student = User(name="Test Student", email="student@test.edu", role="student", credibility_score=92)
        student.set_password("student-pass")
        admin = User(name="Test Admin", email="admin@test.edu", role="admin", credibility_score=100)
        admin.set_password("admin-pass")
        db.session.add_all([student, admin])
        db.session.commit()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_login_redirects_to_student_dashboard(client):
    response = client.post("/login", data={"role": "student", "email": "student@test.edu", "password": "student-pass"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Recent complaints" in response.data


def test_admin_can_open_dashboard(client):
    response = client.post("/login", data={"role": "admin", "email": "admin@test.edu", "password": "admin-pass"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Campus pulse, at a glance" in response.data


def test_priority_and_duplicate_rules():
    assert calculate_priority("Safety", 4, True, 80) == "Critical"
    assert calculate_priority("Academics", 0, False, 2) == "Low"
    assert complaint_similarity("water leakage north stairs", "water leakage near north stairs") > 0.5
