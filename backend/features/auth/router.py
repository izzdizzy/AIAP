from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...core.security import create_access_token, get_current_user, hash_password, verify_password
from .models import User
from .schemas import ChangePasswordRequest, LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(tags=['Authentication'])


@router.post('/register', response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail='An account with this email already exists.')

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserOut.model_validate(user)
    )


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Incorrect email or password.')

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserOut.model_validate(user)
    )


@router.get('/me', response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.post('/change-password')
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail='Current password is incorrect.')

    current_user.hashed_password = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()
    return {'message': 'Password updated successfully.'}
