from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...core.security import get_current_user
from .models import ModuleAssessment

router = APIRouter(tags=['Assessment History'])

ALLOWED_MODULES = {'cad', 'readmission'}


class ModuleHistoryCreate(BaseModel):
    payload: Dict[str, Any]
    result: Dict[str, Any]


class ModuleHistoryOut(BaseModel):
    id: int
    module: str
    created_at: datetime
    payload: Dict[str, Any]
    result: Dict[str, Any]


def _check_module(module: str) -> None:
    if module not in ALLOWED_MODULES:
        raise HTTPException(status_code=404, detail='Unknown assessment module.')


def _row_out(row: ModuleAssessment) -> ModuleHistoryOut:
    return ModuleHistoryOut(
        id=row.id,
        module=row.module,
        created_at=row.created_at,
        payload=row.payload or {},
        result=row.result or {}
    )


@router.post('/{module}', response_model=ModuleHistoryOut, status_code=201)
def save_module_assessment(
    module: str,
    body: ModuleHistoryCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_module(module)
    row = ModuleAssessment(
        user_id=current_user.id,
        module=module,
        payload=body.payload,
        result=body.result
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _row_out(row)


@router.get('/{module}', response_model=List[ModuleHistoryOut])
def list_module_assessments(
    module: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_module(module)
    rows = (
        db.query(ModuleAssessment)
        .filter(
            ModuleAssessment.user_id == current_user.id,
            ModuleAssessment.module == module
        )
        .order_by(ModuleAssessment.created_at.desc())
        .all()
    )
    return [_row_out(r) for r in rows]


@router.delete('/{module}/{assessment_id}', status_code=204)
def delete_module_assessment(
    module: str,
    assessment_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_module(module)
    row = (
        db.query(ModuleAssessment)
        .filter(
            ModuleAssessment.id == assessment_id,
            ModuleAssessment.module == module,
            ModuleAssessment.user_id == current_user.id
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail='Assessment not found.')
    db.delete(row)
    db.commit()
