from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from .models import HR, CV, CVStatus, Template, FieldConfig
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


# --- Template Operations (PostgreSQL Storage) ---

def list_templates(db: Session) -> List[Template]:
    return db.query(Template).order_by(Template.is_system.desc(), Template.name.asc()).all()


def get_template_by_id(db: Session, template_id: str) -> Optional[Template]:
    return db.query(Template).filter(Template.template_id == template_id).first()


def get_active_template(db: Session) -> Optional[Template]:
    active = db.query(Template).filter(Template.is_active == True).first()
    if not active:
        active = db.query(Template).filter(Template.template_id == "default").first()
    return active


def create_template(
    db: Session,
    name: str,
    filename: str,
    file_bytes: bytes,
    template_id: Optional[str] = None,
    description: Optional[str] = None,
    is_system: bool = False,
    is_active: bool = False,
    make_active: Optional[bool] = None,
    fields_config: Optional[Dict[str, Any]] = None,
    hr_id: Optional[int] = None,
) -> Template:
    active = is_active if make_active is None else make_active
    tid = template_id or f"tpl_{uuid.uuid4().hex[:8]}"
    if active:
        db.query(Template).update({Template.is_active: False})

    tpl = Template(
        template_id=tid,
        name=name,
        description=description,
        filename=filename,
        file_bytes=file_bytes,
        is_system=is_system,
        is_active=active,
        fields_config=fields_config,
        created_at=datetime.now(timezone.utc).isoformat(),
        hr_id=hr_id,
    )
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


def set_active_template(db: Session, template_id: str) -> Optional[Template]:
    tpl = get_template_by_id(db, template_id)
    if not tpl:
        return None
    db.query(Template).update({Template.is_active: False})
    tpl.is_active = True
    db.commit()
    db.refresh(tpl)
    return tpl


def delete_template(db: Session, template_id: str) -> bool:
    tpl = get_template_by_id(db, template_id)
    if not tpl:
        return False
    if tpl.is_system or tpl.template_id == "default":
        raise ValueError("Нельзя удалить базовый системный шаблон")

    was_active = tpl.is_active
    db.delete(tpl)
    if was_active:
        default_tpl = get_template_by_id(db, "default")
        if default_tpl:
            default_tpl.is_active = True
    db.commit()
    return True


# --- FieldConfig Operations (PostgreSQL Storage) ---

def get_field_config(db: Session, config_key: str = "default") -> Optional[FieldConfig]:
    return db.query(FieldConfig).filter(FieldConfig.config_key == config_key).first()


def save_field_config(
    db: Session,
    fields: Dict[str, bool],
    config_key: str = "default",
    name: str = "Конфигурация полей",
    hr_id: Optional[int] = None,
) -> FieldConfig:
    cfg = get_field_config(db, config_key)
    now_iso = datetime.now(timezone.utc).isoformat()
    if not cfg:
        cfg = FieldConfig(
            config_key=config_key,
            name=name,
            fields=fields,
            updated_at=now_iso,
            hr_id=hr_id,
        )
        db.add(cfg)
    else:
        cfg.fields = fields
        cfg.updated_at = now_iso
        if hr_id:
            cfg.hr_id = hr_id
    db.commit()
    db.refresh(cfg)
    return cfg
