"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import hashlib
import hmac
import os
from pathlib import Path
import time

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

SESSION_COOKIE = "teacher_session"
SESSION_DURATION = 8 * 60 * 60
TEACHER_USERNAME = os.environ.get("TEACHER_USERNAME")
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD")
SESSION_SECRET = os.environ.get("SESSION_SECRET")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"


class TeacherCredentials(BaseModel):
    username: str
    password: str


def _auth_is_configured():
    return (
        TEACHER_USERNAME is not None
        and TEACHER_PASSWORD is not None
        and SESSION_SECRET is not None
        and len(SESSION_SECRET.encode("utf-8")) >= 32
    )


def _require_auth_configuration():
    if not _auth_is_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Teacher authentication is not configured. Set "
                "TEACHER_USERNAME, TEACHER_PASSWORD, and a SESSION_SECRET "
                "of at least 32 characters."
            ),
        )


def _session_signature(expiration):
    return hmac.new(
        SESSION_SECRET.encode("utf-8"),
        str(expiration).encode("ascii"),
        hashlib.sha256,
    ).hexdigest()


def _constant_time_equal(first, second):
    return hmac.compare_digest(first.encode("utf-8"), second.encode("utf-8"))


def _is_teacher_authenticated(request: Request):
    if not _auth_is_configured():
        return False

    session = request.cookies.get(SESSION_COOKIE, "")
    try:
        expiration_text, signature = session.split(".", maxsplit=1)
        expiration = int(expiration_text)
    except ValueError:
        return False

    return (
        expiration > int(time.time())
        and hmac.compare_digest(signature, _session_signature(expiration))
    )


def _require_teacher(request: Request):
    _require_auth_configuration()
    if not _is_teacher_authenticated(request):
        raise HTTPException(status_code=401, detail="Teacher login required")


# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/auth/session")
def get_auth_session(request: Request):
    return {"authenticated": _is_teacher_authenticated(request)}


@app.post("/auth/login")
def login(credentials: TeacherCredentials, response: Response):
    _require_auth_configuration()
    if not (
        _constant_time_equal(credentials.username, TEACHER_USERNAME)
        and _constant_time_equal(credentials.password, TEACHER_PASSWORD)
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    expiration = int(time.time()) + SESSION_DURATION
    response.set_cookie(
        key=SESSION_COOKIE,
        value=f"{expiration}.{_session_signature(expiration)}",
        max_age=SESSION_DURATION,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
    )
    return {"message": "Logged in as a teacher"}


@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
    )
    return {"message": "Logged out"}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, request: Request):
    """Sign up a student for an activity"""
    _require_teacher(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, request: Request):
    """Unregister a student from an activity"""
    _require_teacher(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
