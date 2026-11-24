# Hospital Appointment System

A backend REST API with a simple web page for managing hospital departments, doctors, patients, and appointments.

## Tech Stack

- Python 3.14
- FastAPI (REST API and Swagger docs)
- SQLAlchemy (ORM)
- PostgreSQL (database)
- HTML, CSS, and JavaScript (simple frontend, served by FastAPI)

## Database Design

The ER diagram is in `er-diagram.png`.

- `departments` has many `doctors` (one-to-many, through `doctors.department_id`)
- `doctors` and `patients` are linked many-to-many through `appointments`
- Foreign keys: `doctors.department_id`, `appointments.doctor_id`, `appointments.patient_id`

**Business rule:** a doctor cannot have two active appointments (status `scheduled` or `confirmed`) at the same date and time. The database enforces this with a partial unique index, and the API returns `409 Conflict`. Cancelled and completed appointments do not block a slot.

**Status rule:** `status` must be one of `scheduled`, `confirmed`, `completed`, `cancelled`. The database enforces this with a CHECK constraint.

## Setup

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a PostgreSQL database named `hospital_appointment_system`.
4. Create a file named `.env` in the project root:
   ```
   DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/hospital_appointment_system
   ```
   The `.env` file is not committed to Git, so the password stays on your computer.
5. Run the server from the project root:
   ```
   uvicorn app.main:app --reload
   ```
6. Open the app:
   - Web page: http://127.0.0.1:8000/ui/
   - API docs (Swagger): http://127.0.0.1:8000/docs

## Sample API Calls

Create a department:
```
POST /departments
{"name": "Cardiology", "description": "Heart care"}
```

Book an appointment:
```
POST /appointments
{"doctor_id": 1, "patient_id": 3, "appointment_date": "2026-11-25",
 "appointment_time": "15:00:00", "status": "scheduled", "reason": "Checkup"}
```

Double booking (returns 409 Conflict):
```
POST /appointments
{"doctor_id": 1, "patient_id": 3, "appointment_date": "2026-11-25",
 "appointment_time": "15:00:00", "status": "scheduled"}
```

Cancel an appointment:
```
PUT /appointments/1
{"status": "cancelled"}
```

View appointments with doctor and patient names:
```
GET /appointments?status=scheduled&page=1&size=10
```

## Endpoints

Each table has five endpoints: Create, Read all, Read one, Update, and Delete.

| Resource     | Base path       |
|--------------|-----------------|
| Departments  | `/departments`  |
| Doctors      | `/doctors`      |
| Patients     | `/patients`     |
| Appointments | `/appointments` |

Read-all endpoints support pagination (`page`, `size`). Search is available on doctors (`specialization`), patients (`name`), and appointments (`status`).

## Error Codes

| Code | Meaning |
|------|---------|
| 200  | Read, update, or delete succeeded |
| 201  | Create succeeded |
| 404  | Row not found |
| 409  | Rule violated, such as a double booking or duplicate email |
| 422  | Invalid input (FastAPI validation, for example a bad email) |

## Project Structure

```
app/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── static/
│   └── index.html
└── routes/
    ├── departments.py
    ├── doctors.py
    ├── patients.py
    └── appointments.py
```

## Author

Lavanya J
