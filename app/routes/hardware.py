from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import EventLog, Basket, Product, BasketModule


router = APIRouter(
    prefix="/hardware",
    tags=["Hardware"]
)


# ============================================================
# HARDWARE EVENT
# ============================================================

class HardwareEvent(BaseModel):
    basket_id: int
    event_type: str
    event_description: str
    product_id: int | None = None
    measured_weight: float | None = None


@router.post("/events")
def create_hardware_event(
    event: HardwareEvent,
    db: Session = Depends(get_db)
):

    basket = db.query(Basket).filter(
        Basket.basket_id == event.basket_id
    ).first()

    if not basket:
        raise HTTPException(
            status_code=404,
            detail="Basket not found"
        )

    if event.product_id is not None:

        product = db.query(Product).filter(
            Product.product_id == event.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

    metadata = {
        "product_id": event.product_id,
        "measured_weight": event.measured_weight
    }

    new_event = EventLog(
        user_id=basket.current_user_id,
        basket_id=event.basket_id,
        event_type=event.event_type,
        event_description=event.event_description,
        event_metadata=metadata
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return {
        "message": "Hardware event recorded successfully",
        "event_id": new_event.event_id,
        "basket_id": new_event.basket_id,
        "user_id": new_event.user_id,
        "event_type": new_event.event_type,
        "event_description": new_event.event_description,
        "metadata": new_event.event_metadata
    }


# ============================================================
# WEIGHT VERIFICATION
# ============================================================

class WeightVerification(BaseModel):
    basket_id: int
    product_id: int
    measured_weight: float


@router.post("/verify-weight")
def verify_weight(
    data: WeightVerification,
    db: Session = Depends(get_db)
):

    basket = db.query(Basket).filter(
        Basket.basket_id == data.basket_id
    ).first()

    if not basket:
        raise HTTPException(
            status_code=404,
            detail="Basket not found"
        )

    if basket.basket_status != "in_use":
        raise HTTPException(
            status_code=400,
            detail="Basket is not currently in use"
        )

    product = db.query(Product).filter(
        Product.product_id == data.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    expected_weight = float(product.weight)
    measured_weight = data.measured_weight

    tolerance_percent = 5.0

    tolerance = expected_weight * (
        tolerance_percent / 100
    )

    minimum_weight = expected_weight - tolerance
    maximum_weight = expected_weight + tolerance

    weight_verified = (
        minimum_weight <= measured_weight <= maximum_weight
    )

    if weight_verified:

        event_type = "weight_verified"

        description = (
            f"Load cell verified {product.product_name}. "
            f"Expected weight: {expected_weight} kg, "
            f"measured weight: {measured_weight} kg"
        )

    else:

        event_type = "weight_mismatch"

        description = (
            f"Weight mismatch detected for "
            f"{product.product_name}. "
            f"Expected weight: {expected_weight} kg, "
            f"measured weight: {measured_weight} kg"
        )

    metadata = {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "expected_weight": expected_weight,
        "measured_weight": measured_weight,
        "tolerance_percent": tolerance_percent,
        "minimum_accepted_weight": minimum_weight,
        "maximum_accepted_weight": maximum_weight,
        "verified": weight_verified
    }

    new_event = EventLog(
        user_id=basket.current_user_id,
        basket_id=basket.basket_id,
        event_type=event_type,
        event_description=description,
        event_metadata=metadata
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    if weight_verified:

        return {
            "message": "Weight verified successfully",
            "verified": True,
            "event_id": new_event.event_id,
            "basket_id": basket.basket_id,
            "product_id": product.product_id,
            "product_name": product.product_name,
            "expected_weight": expected_weight,
            "measured_weight": measured_weight,
            "tolerance_percent": tolerance_percent,
            "accepted_range": {
                "minimum": round(minimum_weight, 3),
                "maximum": round(maximum_weight, 3)
            }
        }

    return {
        "message": "Weight mismatch detected",
        "verified": False,
        "event_id": new_event.event_id,
        "basket_id": basket.basket_id,
        "product_id": product.product_id,
        "product_name": product.product_name,
        "expected_weight": expected_weight,
        "measured_weight": measured_weight,
        "tolerance_percent": tolerance_percent,
        "accepted_range": {
            "minimum": round(minimum_weight, 3),
            "maximum": round(maximum_weight, 3)
        }
    }


# ============================================================
# SERVO CONTROL
# ============================================================

class ServoCommand(BaseModel):
    basket_id: int
    product_id: int | None = None


def get_servo(
    basket_id: int,
    db: Session
):

    servo = db.query(BasketModule).filter(
        BasketModule.basket_id == basket_id,
        BasketModule.module_type == "Servo"
    ).first()

    if not servo:
        raise HTTPException(
            status_code=404,
            detail="Servo module not found"
        )

    if servo.connection_status != "online":
        raise HTTPException(
            status_code=400,
            detail="Servo is offline"
        )

    if servo.module_status != "active":
        raise HTTPException(
            status_code=400,
            detail="Servo module is not active"
        )

    return servo


# ============================================================
# OPEN SERVO
# ============================================================

@router.post("/servo/open")
def open_servo(
    data: ServoCommand,
    db: Session = Depends(get_db)
):

    basket = db.query(Basket).filter(
        Basket.basket_id == data.basket_id
    ).first()

    if not basket:
        raise HTTPException(
            status_code=404,
            detail="Basket not found"
        )

    if basket.basket_status != "in_use":
        raise HTTPException(
            status_code=400,
            detail="Basket is not currently in use"
        )

    servo = get_servo(
        data.basket_id,
        db
    )

    # 120 degrees = OPEN
    servo.current_value = 120

    metadata = {
        "action": "open",
        "servo_position": 120,
        "product_id": data.product_id
    }

    event = EventLog(
        user_id=basket.current_user_id,
        basket_id=basket.basket_id,
        event_type="servo_opened",
        event_description="Servo door opened",
        event_metadata=metadata
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "message": "Servo opened successfully",
        "basket_id": basket.basket_id,
        "module_id": servo.module_id,
        "module_identifier": servo.module_identifier,
        "servo_position": float(servo.current_value),
        "product_id": data.product_id,
        "event_id": event.event_id
    }


# ============================================================
# CLOSE SERVO
# ============================================================

@router.post("/servo/close")
def close_servo(
    data: ServoCommand,
    db: Session = Depends(get_db)
):

    basket = db.query(Basket).filter(
        Basket.basket_id == data.basket_id
    ).first()

    if not basket:
        raise HTTPException(
            status_code=404,
            detail="Basket not found"
        )

    servo = get_servo(
        data.basket_id,
        db
    )

    # 0 degrees = CLOSED
    servo.current_value = 0

    metadata = {
        "action": "close",
        "servo_position": 0,
        "product_id": data.product_id
    }

    event = EventLog(
        user_id=basket.current_user_id,
        basket_id=basket.basket_id,
        event_type="servo_closed",
        event_description="Servo door closed",
        event_metadata=metadata
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "message": "Servo closed successfully",
        "basket_id": basket.basket_id,
        "module_id": servo.module_id,
        "module_identifier": servo.module_identifier,
        "servo_position": float(servo.current_value),
        "product_id": data.product_id,
        "event_id": event.event_id
    }
# ============================================================
# LOAD CELL UPDATE
# ============================================================

class LoadCellUpdate(BaseModel):
    basket_id: int
    measured_weight: float


@router.post("/load-cell/update")
def update_load_cell(
    data: LoadCellUpdate,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Check basket
    # --------------------------------------------------------

    basket = db.query(Basket).filter(
        Basket.basket_id == data.basket_id
    ).first()

    if not basket:
        raise HTTPException(
            status_code=404,
            detail="Basket not found"
        )

    # --------------------------------------------------------
    # 2. Find Load Cell
    # --------------------------------------------------------

    load_cell = db.query(BasketModule).filter(
        BasketModule.basket_id == data.basket_id,
        BasketModule.module_type == "Load Cell"
    ).first()

    if not load_cell:
        raise HTTPException(
            status_code=404,
            detail="Load Cell module not found"
        )

    # --------------------------------------------------------
    # 3. Check connection
    # --------------------------------------------------------

    if load_cell.connection_status != "online":
        raise HTTPException(
            status_code=400,
            detail="Load Cell is offline"
        )

    if load_cell.module_status != "active":
        raise HTTPException(
            status_code=400,
            detail="Load Cell module is not active"
        )

    # --------------------------------------------------------
    # 4. Update measured weight
    # --------------------------------------------------------

    load_cell.current_value = data.measured_weight

    # Update last communication time
    from sqlalchemy import func

    load_cell.last_seen = func.now()

    # --------------------------------------------------------
    # 5. Log hardware event
    # --------------------------------------------------------

    metadata = {
        "measured_weight": data.measured_weight,
        "module_id": load_cell.module_id,
        "module_identifier": load_cell.module_identifier
    }

    new_event = EventLog(
        user_id=basket.current_user_id,
        basket_id=basket.basket_id,
        event_type="load_cell_reading",
        event_description=(
            f"Load Cell measured "
            f"{data.measured_weight} kg"
        ),
        event_metadata=metadata
    )

    db.add(new_event)

    db.commit()
    db.refresh(load_cell)
    db.refresh(new_event)

    return {
        "message": "Load Cell reading updated successfully",
        "basket_id": basket.basket_id,
        "module_id": load_cell.module_id,
        "module_identifier": load_cell.module_identifier,
        "measured_weight": float(load_cell.current_value),
        "unit": load_cell.unit,
        "event_id": new_event.event_id
    }