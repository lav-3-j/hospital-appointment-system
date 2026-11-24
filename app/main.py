from fastapi import FastAPI
from app.routes import departments, doctors, patients, appointments

app = FastAPI(title="Hospital Appointment System")

app.include_router(departments.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(appointments.router)


@app.get("/")
def home():
    return {"message": "Hospital Appointment System API is running"}