from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)


# CREATE PATIENT
@router.post("", response_model=schemas.PatientResponse, status_code=201)
def create_patient(
    patient: schemas.PatientCreate,
    db: Session = Depends(get_db)
):
    new_patient = models.Patient(**patient.model_dump())
    db.add(new_patient)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Patient email already exists")

    db.refresh(new_patient)
    return new_patient


# GET PATIENTS (with optional name search and pagination)
@router.get("", response_model=list[schemas.PatientResponse])
def get_patients(
    name: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(models.Patient)

    if name:
        query = query.filter(models.Patient.name.ilike(f"%{name}%"))

    return (
        query.order_by(models.Patient.id)
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )


# GET PATIENT BY ID
@router.get("/{patient_id}", response_model=schemas.PatientResponse)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient


# UPDATE PATIENT
@router.put("/{patient_id}", response_model=schemas.PatientResponse)
def update_patient(
    patient_id: int,
    updated_data: schemas.PatientUpdate,
    db: Session = Depends(get_db)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    changes = updated_data.model_dump(exclude_unset=True)

    # name is required, so it cannot be set to null.
    # email and phone are optional, so null is allowed.
    if "name" in changes and changes["name"] is None:
        raise HTTPException(status_code=400, detail="name cannot be null")

    for key, value in changes.items():
        setattr(patient, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Patient email already exists")

    db.refresh(patient)
    return patient


# DELETE PATIENT
@router.delete("/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    db.delete(patient)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Patient has appointments and cannot be deleted"
        )

    return {"message": "Patient deleted successfully"}