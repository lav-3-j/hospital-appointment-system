from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)

# Must match the WHERE clause of uq_doctor_active_slot in the database
ACTIVE_STATUSES = ("scheduled", "confirmed")

SLOT_TAKEN_MESSAGE = "Doctor already has an appointment at this time"


# ---------- HELPERS ----------

def ensure_doctor_and_patient_exist(db: Session, doctor_id: int, patient_id: int):
    doctor = db.query(models.Doctor.id).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    patient = db.query(models.Patient.id).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")


def ensure_slot_free(
    db: Session,
    doctor_id: int,
    appointment_date,
    appointment_time,
    status: str,
    exclude_id: Optional[int] = None
):
    # Cancelled and completed bookings don't block a slot
    if status not in ACTIVE_STATUSES:
        return

    query = db.query(models.Appointment.id).filter(
        models.Appointment.doctor_id == doctor_id,
        models.Appointment.appointment_date == appointment_date,
        models.Appointment.appointment_time == appointment_time,
        models.Appointment.status.in_(ACTIVE_STATUSES),
    )

    # When updating, ignore the appointment being changed
    if exclude_id is not None:
        query = query.filter(models.Appointment.id != exclude_id)

    if query.first():
        raise HTTPException(status_code=409, detail=SLOT_TAKEN_MESSAGE)


def get_appointment_or_404(db: Session, appointment_id: int) -> models.Appointment:
    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return appointment


def joined_query(db: Session):
    # JOIN connects each appointment to its doctor and patient rows,
    # so we can return their names in one query
    return (
        db.query(
            models.Appointment,
            models.Doctor.name.label("doctor_name"),
            models.Patient.name.label("patient_name"),
        )
        .join(models.Doctor, models.Appointment.doctor_id == models.Doctor.id)
        .join(models.Patient, models.Appointment.patient_id == models.Patient.id)
    )


def to_detail(appointment, doctor_name: str, patient_name: str) -> dict:
    return {
        "id": appointment.id,
        "doctor_id": appointment.doctor_id,
        "doctor_name": doctor_name,
        "patient_id": appointment.patient_id,
        "patient_name": patient_name,
        "appointment_date": appointment.appointment_date,
        "appointment_time": appointment.appointment_time,
        "status": appointment.status,
        "reason": appointment.reason,
        "created_at": appointment.created_at,
        "updated_at": appointment.updated_at,
    }


# ---------- CREATE ----------

@router.post("", response_model=schemas.AppointmentResponse, status_code=201)
def create_appointment(
    appointment: schemas.AppointmentCreate,
    db: Session = Depends(get_db)
):
    ensure_doctor_and_patient_exist(db, appointment.doctor_id, appointment.patient_id)
    ensure_slot_free(
        db,
        appointment.doctor_id,
        appointment.appointment_date,
        appointment.appointment_time,
        appointment.status,
    )

    new_appointment = models.Appointment(**appointment.model_dump())
    db.add(new_appointment)

    try:
        db.commit()
    except IntegrityError:
        # Two requests can pass the check above at the same moment.
        # The database index catches the second one.
        db.rollback()
        raise HTTPException(status_code=409, detail=SLOT_TAKEN_MESSAGE)

    db.refresh(new_appointment)
    return new_appointment


# ---------- READ ALL (joined view, with filter and pagination) ----------

@router.get("", response_model=list[schemas.AppointmentDetailResponse])
def get_appointments(
    status: Optional[schemas.AppointmentStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = joined_query(db)

    if status:
        query = query.filter(models.Appointment.status == status)

    rows = (
        query.order_by(models.Appointment.id)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return [to_detail(appt, doctor_name, patient_name) for appt, doctor_name, patient_name in rows]


# ---------- READ ONE (joined view) ----------

@router.get("/{appointment_id}", response_model=schemas.AppointmentDetailResponse)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    row = joined_query(db).filter(models.Appointment.id == appointment_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt, doctor_name, patient_name = row
    return to_detail(appt, doctor_name, patient_name)


# ---------- UPDATE ----------

@router.put("/{appointment_id}", response_model=schemas.AppointmentResponse)
def update_appointment(
    appointment_id: int,
    updated_data: schemas.AppointmentUpdate,
    db: Session = Depends(get_db)
):
    appointment = get_appointment_or_404(db, appointment_id)
    changes = updated_data.model_dump(exclude_unset=True)

    # Required fields cannot be set to null
    for field in ("doctor_id", "patient_id", "appointment_date", "appointment_time", "status"):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=400, detail=f"{field} cannot be null")

    # The final values after this update, so the rules check the result
    doctor_id = changes.get("doctor_id", appointment.doctor_id)
    patient_id = changes.get("patient_id", appointment.patient_id)
    appointment_date = changes.get("appointment_date", appointment.appointment_date)
    appointment_time = changes.get("appointment_time", appointment.appointment_time)
    status = changes.get("status", appointment.status)

    if "doctor_id" in changes or "patient_id" in changes:
        ensure_doctor_and_patient_exist(db, doctor_id, patient_id)

    ensure_slot_free(
        db, doctor_id, appointment_date, appointment_time, status,
        exclude_id=appointment_id
    )

    for key, value in changes.items():
        setattr(appointment, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=SLOT_TAKEN_MESSAGE)

    db.refresh(appointment)
    return appointment


# ---------- DELETE ----------

@router.delete("/{appointment_id}")
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = get_appointment_or_404(db, appointment_id)

    db.delete(appointment)
    db.commit()

    return {"message": "Appointment deleted successfully"}