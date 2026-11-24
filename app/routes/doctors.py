from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/doctors",
    tags=["Doctors"]
)


# CREATE DOCTOR
@router.post("", response_model=schemas.DoctorResponse, status_code=201)
def create_doctor(
    doctor: schemas.DoctorCreate,
    db: Session = Depends(get_db)
):
    department = db.query(models.Department).filter(
        models.Department.id == doctor.department_id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    new_doctor = models.Doctor(**doctor.model_dump())
    db.add(new_doctor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Doctor email already exists")

    db.refresh(new_doctor)
    return new_doctor


# GET DOCTORS (with optional search and pagination)
@router.get("", response_model=list[schemas.DoctorResponse])
def get_doctors(
    specialization: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(models.Doctor)

    if specialization:
        query = query.filter(
            models.Doctor.specialization.ilike(f"%{specialization}%")
        )

    return (
        query.order_by(models.Doctor.id)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )


# GET DOCTOR BY ID
@router.get("/{doctor_id}", response_model=schemas.DoctorResponse)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(models.Doctor).filter(
        models.Doctor.id == doctor_id
    ).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return doctor


# UPDATE DOCTOR
@router.put("/{doctor_id}", response_model=schemas.DoctorResponse)
def update_doctor(
    doctor_id: int,
    updated_data: schemas.DoctorUpdate,
    db: Session = Depends(get_db)
):
    doctor = db.query(models.Doctor).filter(
        models.Doctor.id == doctor_id
    ).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    changes = updated_data.model_dump(exclude_unset=True)

    for field in ("department_id", "name", "email"):
        if field in changes and changes[field] is None:
            raise HTTPException(status_code=400, detail=f"{field} cannot be null")

    if "department_id" in changes:
        department = db.query(models.Department).filter(
            models.Department.id == changes["department_id"]
        ).first()

        if not department:
            raise HTTPException(status_code=404, detail="Department not found")

    for key, value in changes.items():
        setattr(doctor, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Doctor email already exists")

    db.refresh(doctor)
    return doctor


# DELETE DOCTOR
@router.delete("/{doctor_id}")
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    doctor = db.query(models.Doctor).filter(
        models.Doctor.id == doctor_id
    ).first()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    db.delete(doctor)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Doctor has appointments and cannot be deleted"
        )

    return {"message": "Doctor deleted successfully"}