import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import app


def test_db_initializes_and_loads_seed_activities(tmp_path, monkeypatch):
    db_path = tmp_path / "test_activities.db"
    monkeypatch.setattr(app, "DB_PATH", str(db_path), raising=False)

    app.init_db()
    activities = app.get_activities()

    assert "Chess Club" in activities
    assert activities["Chess Club"]["max_participants"] == 12
    assert "michael@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_persists_to_database(tmp_path, monkeypatch):
    db_path = tmp_path / "test_activities.db"
    monkeypatch.setattr(app, "DB_PATH", str(db_path), raising=False)

    app.init_db()
    app.signup_for_activity("Chess Club", "newstudent@mergington.edu")

    activities = app.get_activities()
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            "SELECT email FROM participants WHERE activity_name = ?",
            ("Chess Club",),
        ).fetchall()

    assert ("newstudent@mergington.edu",) in rows


def test_unregister_persists_to_database(tmp_path, monkeypatch):
    db_path = tmp_path / "test_activities.db"
    monkeypatch.setattr(app, "DB_PATH", str(db_path), raising=False)

    app.init_db()
    app.signup_for_activity("Chess Club", "newstudent@mergington.edu")
    app.unregister_from_activity("Chess Club", "newstudent@mergington.edu")

    activities = app.get_activities()
    assert "newstudent@mergington.edu" not in activities["Chess Club"]["participants"]

    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            "SELECT email FROM participants WHERE activity_name = ?",
            ("Chess Club",),
        ).fetchall()

    assert ("newstudent@mergington.edu",) not in rows
