"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

DB_PATH = os.environ.get(
    "ACTIVITY_DB_PATH",
    str(Path(__file__).resolve().parent / "activities.db"),
)

INITIAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


def init_db() -> None:
    """Create the SQLite schema and seed the default activity data if needed."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                activity_name TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                schedule TEXT NOT NULL,
                max_participants INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS participants (
                activity_name TEXT NOT NULL,
                email TEXT NOT NULL,
                PRIMARY KEY (activity_name, email),
                FOREIGN KEY (activity_name) REFERENCES activities(activity_name)
            )
            """
        )

        for activity_name, details in INITIAL_ACTIVITIES.items():
            conn.execute(
                """
                INSERT OR IGNORE INTO activities (
                    activity_name, description, schedule, max_participants
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    activity_name,
                    details["description"],
                    details["schedule"],
                    details["max_participants"],
                ),
            )

            for email in details["participants"]:
                conn.execute(
                    "INSERT OR IGNORE INTO participants (activity_name, email) VALUES (?, ?)",
                    (activity_name, email),
                )

        conn.commit()


def get_activities() -> dict:
    """Return all activities with participant lists."""
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT a.activity_name, a.description, a.schedule, a.max_participants,
                   p.email
            FROM activities a
            LEFT JOIN participants p
                ON p.activity_name = a.activity_name
            ORDER BY a.activity_name, p.email
            """
        ).fetchall()

    activities = {}
    for row in rows:
        activity_name = row["activity_name"]
        if activity_name not in activities:
            activities[activity_name] = {
                "description": row["description"],
                "schedule": row["schedule"],
                "max_participants": row["max_participants"],
                "participants": [],
            }
        if row["email"] is not None:
            activities[activity_name]["participants"].append(row["email"])

    return activities


def get_activity(activity_name: str):
    """Fetch one activity from the database."""
    activities = get_activities()
    if activity_name not in activities:
        return None
    return activities[activity_name]


def signup_for_activity(activity_name: str, email: str):
    """Register a student for an activity and persist the result."""
    activity = get_activity(activity_name)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is full")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO participants (activity_name, email) VALUES (?, ?)",
            (activity_name, email),
        )
        conn.commit()

    return {"message": f"Signed up {email} for {activity_name}"}


def unregister_from_activity(activity_name: str, email: str):
    """Remove a student from an activity and persist the result."""
    activity = get_activity(activity_name)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")

    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity",
        )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM participants WHERE activity_name = ? AND email = ?",
            (activity_name, email),
        )
        conn.commit()

    return {"message": f"Unregistered {email} from {activity_name}"}


app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(Path(__file__).parent, "static")),
    name="static",
)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def list_activities():
    return get_activities()


@app.post("/activities/{activity_name}/signup")
def signup_route(activity_name: str, email: str):
    """Sign up a student for an activity."""
    return signup_for_activity(activity_name, email)


@app.delete("/activities/{activity_name}/unregister")
def unregister_route(activity_name: str, email: str):
    """Unregister a student from an activity."""
    return unregister_from_activity(activity_name, email)
