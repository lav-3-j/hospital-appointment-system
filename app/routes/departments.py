from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/departments",
    tags=["Departments"]
)


@router.post("", response_model=schemas.DepartmentResponse, status_code=201)
def create_department(
    department: schemas.DepartmentCreate,
    db: Session = Depends(get_db)
):
    new_department = models.Department(**department.model_dump())
    db.add(new_department)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Department already exists")

    db.refresh(new_department)
    return new_department


@router.get("", response_model=list[schemas.DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    return db.query(models.Department).all()


@router.get("/{department_id}", response_model=schemas.DepartmentResponse)
def get_department(department_id: int, db: Session = Depends(get_db)):
    department = db.query(models.Department).filter(
        models.Department.id == department_id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    return department


@router.put("/{department_id}", response_model=schemas.DepartmentResponse)
def update_department(
    department_id: int,
    updated_data: schemas.DepartmentUpdate,
    db: Session = Depends(get_db)
):
    department = db.query(models.Department).filter(
        models.Department.id == department_id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    changes = updated_data.model_dump(exclude_unset=True)

    if "name" in changes and changes["name"] is None:
        raise HTTPException(status_code=400, detail="Department name cannot be empty")

    for key, value in changes.items():
        setattr(department, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Department name already exists")

    db.refresh(department)
    return department


@router.delete("/{department_id}")
def delete_department(department_id: int, db: Session = Depends(get_db)):
    department = db.query(models.Department).filter(
        models.Department.id == department_id
    ).first()

    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    db.delete(department)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Department has doctors and cannot be deleted"
        )

    return {"message": "Department deleted successfully"}