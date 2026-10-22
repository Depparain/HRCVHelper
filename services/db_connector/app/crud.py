from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from .models import HR, CV, CVStatus
from .schemas import HRCreate, CVCreate, CVUpdate


# --- HR Operations ---

def get_hr_by_id(db: Session, hr_id: int) -> Optional[HR]:
    return db.query(HR).filter(HR.hr_id == hr_id).first()


def get_hr_by_login(db: Session, login: str) -> Optional[HR]:
    return db.query(HR).filter(HR.login == login).first()


def create_hr(db: Session, hr_in: HRCreate) -> HR:
    db_hr = HR(
        full_name=hr_in.full_name,
        login=hr_in.login,
        hash_pass=hr_in.hash_pass,
        role=hr_in.role or "hr",
    )
    db.add(db_hr)
    db.commit()
    db.refresh(db_hr)
    return db_hr


def list_hrs(db: Session, skip: int = 0, limit: int = 100) -> List[HR]:
    return db.query(HR).offset(skip).limit(limit).all()


# --- CV Operations ---

def get_cv_by_id(db: Session, cv_id: int) -> Optional[CV]:
    return db.query(CV).filter(CV.cv_id == cv_id).first()


def list_cvs_by_hr(db: Session, hr_id: int, skip: int = 0, limit: int = 100) -> List[CV]:
    return db.query(CV).filter(CV.hr_id == hr_id).order_by(CV.cv_id.desc()).offset(skip).limit(limit).all()


def list_all_cvs(db: Session, skip: int = 0, limit: int = 100) -> List[CV]:
    return db.query(CV).order_by(CV.cv_id.desc()).offset(skip).limit(limit).all()


def create_cv(db: Session, cv_in: CVCreate) -> CV:
    db_cv = CV(
        hr_id=cv_in.hr_id,
        jsonb=cv_in.jsonb,
        status=cv_in.status or CVStatus.UPLOADED.value,
        docx=cv_in.docx,
    )
    db.add(db_cv)
    db.commit()
    db.refresh(db_cv)
    return db_cv


def update_cv(db: Session, cv_id: int, cv_update: CVUpdate) -> Optional[CV]:
    db_cv = get_cv_by_id(db, cv_id)
    if not db_cv:
        return None

    if cv_update.jsonb is not None:
        db_cv.jsonb = cv_update.jsonb
    if cv_update.status is not None:
        db_cv.status = cv_update.status
    if cv_update.docx is not None:
        db_cv.docx = cv_update.docx

    db.commit()
    db.refresh(db_cv)
    return db_cv


def update_cv_status(db: Session, cv_id: int, status: str) -> Optional[CV]:
    db_cv = get_cv_by_id(db, cv_id)
    if not db_cv:
        return None
    db_cv.status = status
    db.commit()
    db.refresh(db_cv)
    return db_cv


def update_cv_docx(db: Session, cv_id: int, docx_key: str, status: Optional[str] = CVStatus.READY.value) -> Optional[CV]:
    db_cv = get_cv_by_id(db, cv_id)
    if not db_cv:
        return None
    db_cv.docx = docx_key
    if status:
        db_cv.status = status
    db.commit()
    db.refresh(db_cv)
    return db_cv
