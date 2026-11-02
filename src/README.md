# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher-only signups and unregistration
- Public activity and participant lists

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Configure teacher credentials and a session signing secret in the environment.
   Do not commit credentials or secrets to the repository:

   ```
   export TEACHER_USERNAME=teacher
   export TEACHER_PASSWORD='use-a-unique-strong-password'
   export SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```

   For local HTTP testing only, set `COOKIE_SECURE=false`. The session cookie is
   Secure by default and should be used with HTTPS outside local development.

3. Run the application from the repository root:

   ```
   uvicorn app:app --app-dir src --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc
   - Activities page: http://localhost:8000/

## API Endpoints

| Method | Endpoint                                                              | Description                                                |
| ------ | --------------------------------------------------------------------- | ---------------------------------------------------------- |
| GET    | `/activities`                                                         | Public list of activities and participants                 |
| GET    | `/auth/session`                                                       | Check whether the current browser has a teacher session    |
| POST   | `/auth/login`                                                         | Log in with configured teacher credentials                 |
| POST   | `/auth/logout`                                                        | End the current teacher session                            |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu`     | Teacher-only student signup                               |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only student unregistration                        |

Teacher credentials are supplied through environment variables rather than a
checked-in file. A session expires after eight hours; the signing secret must
be at least 32 characters long. Login returns a clear configuration error until
all required values are set.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
