from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Basket, User


router = APIRouter(
    prefix="/baskets",
    tags=["Baskets"]
)


class BasketCreate(BaseModel):
    basket_number: str
    current_user_id: int | None = None
    battery_status: float | None = None
    current_weight: float = 0
    connection_status: str = "offline"
    current_location: str | None = None
    basket_status: str = "available"


@router.post("/")
def create_basket(
    basket: BasketCreate,
    db: Session = Depends(get_db)
):
    existing_basket = (
        db.query(Basket)
        .filter(Basket.basket_number == basket.basket_number)
        .first()
    )

    if existing_basket:
        raise HTTPException(
            status_code=400,
            detail="Basket with this basket number already exists"
        )

    if basket.current_user_id is not None:
        user = (
            db.query(User)
            .filter(User.user_id == basket.current_user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

    new_basket = Basket(
        basket_number=basket.basket_number,
        current_user_id=basket.current_user_id,
        battery_status=basket.battery_status,
        current_weight=basket.current_weight,
        connection_status=basket.connection_status,
        current_location=basket.current_location,
        basket_status=basket.basket_status
    )

    db.add(new_basket)
    db.commit()
    db.refresh(new_basket)

    return {
        "message": "Basket created successfully",
        "basket_id": new_basket.basket_id,
        "basket_number": new_basket.basket_number,
        "current_user_id": new_basket.current_user_id,
        "battery_status": new_basket.battery_status,
        "current_weight": new_basket.current_weight,
        "connection_status": new_basket.connection_status,
        "current_location": new_basket.current_location,
        "basket_status": new_basket.basket_status
    }


@router.get("/")
def get_baskets(db: Session = Depends(get_db)):
    return db.query(Basket).all()


@router.get("/{basket_id}")
def get_basket(
    basket_id: int,
    db: Session = Depends(get_db)
):
    basket = (
        db.query(Basket)
        .filter(Basket.basket_id == basket_id)
        .first()
    )

    if not basket:
        raise HTTPException(
            status_code=404,
            detail="Basket not found"
        )

    return basket