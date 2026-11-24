from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Literal, Optional
from datetime import date, time, datetime

AppointmentStatus = Literal["scheduled", "confirmed", "completed", "cancelled"]

# Common configuration for response schemas
class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------- DEPARTMENT ----------------

class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DepartmentResponse(ORMBase):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


# ---------------- DOCTOR ----------------

class DoctorCreate(BaseModel):
    department_id: int
    name: str
    specialization: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None


class DoctorUpdate(BaseModel):
    department_id: Optional[int] = None
    name: Optional[str] = None
    specialization: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class DoctorResponse(ORMBase):
    id: int
    department_id: int
    name: str
    specialization: Optional[str]
    email: str
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime


# ---------------- PATIENT ----------------

class PatientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None


class PatientResponse(ORMBase):
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    date_of_birth: Optional[date]
    created_at: datetime
    updated_at: datetime


# ---------------- APPOINTMENT ----------------

class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    appointment_date: date
    appointment_time: time
    status: AppointmentStatus
    reason: Optional[str] = None


class AppointmentUpdate(BaseModel):
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = None


class AppointmentResponse(ORMBase):
    id: int
    doctor_id: int
    patient_id: int
    appointment_date: date
    appointment_time: time
    status: str
    reason: Optional[str]
    created_at: datetime
    updated_at: datetime


    # ---------------- APPOINTMENT (JOINED VIEW) ----------------

class AppointmentDetailResponse(ORMBase):
    id: int
    doctor_id: int
    doctor_name: str
    patient_id: int
    patient_name: str
    appointment_date: date
    appointment_time: time
    status: str
    reason: Optional[str]
    created_at: datetime
    updated_at: datetime