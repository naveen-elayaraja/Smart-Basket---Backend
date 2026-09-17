from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


class UserCreate(BaseModel):
    name: str
    phone_number: str


@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = (
        db.query(User)
        .filter(User.phone_number == user.phone_number)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this phone number already exists"
        )

    new_user = User(
        name=user.name,
        phone_number=user.phone_number
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user_id": new_user.user_id,
        "name": new_user.name,
        "phone_number": new_user.phone_number
    }


@router.get("/")
def get_users(db: Session = Depends(get_db)):

    users = db.query(User).all()

    return users


@router.get("/{phone_number}")
def get_user(
    phone_number: str,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.phone_number == phone_number)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user