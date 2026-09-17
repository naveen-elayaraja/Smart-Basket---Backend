from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import BasketModule, Basket


router = APIRouter(
    prefix="/basket-modules",
    tags=["Basket Modules"]
)


class BasketModuleCreate(BaseModel):
    basket_id: int
    module_type: str
    module_identifier: str | None = None
    connection_status: str = "offline"
    module_status: str = "active"
    current_value: float | None = None
    unit: str | None = None


@router.post("/")
def create_basket_module(
    module: BasketModuleCreate,
    db: Session = Depends(get_db)
):
    # Check whether the basket exists
    basket = (
        db.query(Basket)
        .filter(Basket.basket_id == module.basket_id)
        .first()
    )

    if not basket:
        raise HTTPException(
            status_code=404,
            detail="Basket not found"
        )

    new_module = BasketModule(
        basket_id=module.basket_id,
        module_type=module.module_type,
        module_identifier=module.module_identifier,
        connection_status=module.connection_status,
        module_status=module.module_status,
        current_value=module.current_value,
        unit=module.unit
    )

    db.add(new_module)
    db.commit()
    db.refresh(new_module)

    return {
        "message": "Basket module created successfully",
        "module_id": new_module.module_id,
        "basket_id": new_module.basket_id,
        "module_type": new_module.module_type,
        "module_identifier": new_module.module_identifier,
        "connection_status": new_module.connection_status,
        "module_status": new_module.module_status,
        "current_value": new_module.current_value,
        "unit": new_module.unit
    }


@router.get("/")
def get_basket_modules(db: Session = Depends(get_db)):
    return db.query(BasketModule).all()


@router.get("/{module_id}")
def get_basket_module(
    module_id: int,
    db: Session = Depends(get_db)
):
    module = (
        db.query(BasketModule)
        .filter(BasketModule.module_id == module_id)
        .first()
    )

    if not module:
        raise HTTPException(
            status_code=404,
            detail="Basket module not found"
        )

    return module