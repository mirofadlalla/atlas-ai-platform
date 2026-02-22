from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schema.auth_admin import UserCreate, Token ,UserLogin

from app.core.db import get_db


router = APIRouter(
    prefix="/auth" 
)

from app.controllers.auth_controller import AuthController

@router.post("/register" , response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return AuthController.register(user, db)


@router.post("/login" , response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    return AuthController.login(user, db)

# @router.post("/refresh" , response_model=Token)
# def refresh(token: str, db: Session = Depends(get_db)):
#     return AuthController.refresh(token, db)