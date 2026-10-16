from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from pydantic import BaseModel, Field

from app.state_machine import TrolleyState, transition

from app.services.esp32_client import (
    send_servo_command,
    send_all_servos_command,
)

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

    basket_id: int = Field(ge=1)

    product_id: int = Field(ge=1)

    measured_weight: float = Field(ge=0)

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

    weight_difference = abs(

        measured_weight - expected_weight

    )

    weight_difference_percent = (

        (weight_difference / expected_weight) * 100

        if expected_weight > 0 else 0

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

        "weight_difference": weight_difference,

        "weight_difference_percent": weight_difference_percent,

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

    basket_id: int = Field(ge=1)

    servo_number: int = Field(default=1, ge=1, le=4)

    product_id: int | None = None

def get_servo(

    basket_id: int,

    db: Session,

    servo_number: int = 1,

):

    # Preserve the existing identifier for Servo 1.

    base_identifier = f"SERVO-SB{basket_id:03d}"

    servo_identifier = (

        base_identifier

        if servo_number == 1

        else f"{base_identifier}-{servo_number}"

    )

    servo = db.query(BasketModule).filter(

        BasketModule.basket_id == basket_id,

        BasketModule.module_type == "Servo",

        BasketModule.module_identifier == servo_identifier,

    ).first()

    if not servo:

        raise HTTPException(

            status_code=404,

            detail=f"Servo {servo_number} module not found"

        )

    if servo.connection_status != "online":

        raise HTTPException(

            status_code=400,

            detail=f"Servo {servo_number} is offline"

        )

    if servo.module_status != "active":

        raise HTTPException(

            status_code=400,

            detail=f"Servo {servo_number} module is not active"

        )

    return servo

# ============================================================

# OPEN SERVO

# ============================================================

@router.post(

    "/servo/open",

    summary="Open servo door",

    description="Commands the ESP32 to open the basket servo door."

)

def open_servo(

    data: ServoCommand,

    db: Session = Depends(get_db)

):

    basket = db.query(Basket).filter(

        Basket.basket_id == data.basket_id

    ).first()

    if not basket:

        raise HTTPException(status_code=404, detail="Basket not found")

    if basket.basket_status != "in_use":

        raise HTTPException(

            status_code=400,

            detail="Basket is not currently in use"

        )

    try:

        current_state = TrolleyState(basket.current_state)

    except ValueError:

        raise HTTPException(

            status_code=500,

            detail="Basket has an invalid trolley state"

        )

    allowed_states = {

        TrolleyState.CAMERA_VERIFYING_ADD,

        TrolleyState.CAMERA_VERIFYING_REMOVAL,

    }

    if current_state not in allowed_states:

        raise HTTPException(

            status_code=400,

            detail=f"Servo cannot open from current state: {current_state.value}"

        )

    servo = get_servo(data.basket_id, db, data.servo_number)

    try:

        new_state = transition(

            current_state,

            TrolleyState.SERVO_OPENING

        )

    except ValueError as error:

        raise HTTPException(status_code=400, detail=str(error))

    try:

        controller_response = send_servo_command(
            "open",
            servo=data.servo_number
        )

    except RuntimeError as error:

        raise HTTPException(

            status_code=503,

            detail=f"ESP32 servo command failed: {error}"

        )

    basket.current_state = (

        TrolleyState.WAITING_FOR_ADD.value

        if current_state == TrolleyState.CAMERA_VERIFYING_ADD

        else TrolleyState.WAITING_FOR_REMOVAL.value

    )

    servo.current_value = 120

    event = EventLog(

        user_id=basket.current_user_id,

        basket_id=basket.basket_id,

        event_type="servo_open_command_accepted",

        event_description="ESP32 acknowledged the servo open command",

        event_metadata={

            "action": "open",

            "servo_position": 120,

            "servo_channel": data.servo_number,

            "product_id": data.product_id,

            "controller_response": controller_response,

        }

    )

    db.add(event)

    db.commit()

    db.refresh(event)

    return {

        "message": "ESP32 acknowledged the servo open command",

        "basket_id": basket.basket_id,

        "module_id": servo.module_id,

        "module_identifier": servo.module_identifier,

        "servo_number": data.servo_number,

        "servo_position": 120,

        "product_id": data.product_id,

        "event_id": event.event_id,

    }

# ============================================================

# CLOSE SERVO

# ============================================================

@router.post(

    "/servo/close",

    summary="Close servo door",

    description="Commands the ESP32 to close the basket servo door."

)

def close_servo(

    data: ServoCommand,

    db: Session = Depends(get_db)

):

    basket = db.query(Basket).filter(

        Basket.basket_id == data.basket_id

    ).first()

    if not basket:

        raise HTTPException(status_code=404, detail="Basket not found")

    if basket.basket_status != "in_use":

        raise HTTPException(

            status_code=400,

            detail="Basket is not currently in use"

        )

    try:

        current_state = TrolleyState(basket.current_state)

    except ValueError:

        raise HTTPException(

            status_code=500,

            detail="Basket has an invalid trolley state"

        )

    if current_state != TrolleyState.SERVO_CLOSING:

        raise HTTPException(

            status_code=400,

            detail=f"Servo cannot close from current state: {current_state.value}"

        )

    servo = get_servo(data.basket_id, db, data.servo_number)

    try:

        controller_response = send_servo_command(
            "close",
            servo=data.servo_number
        )

    except RuntimeError as error:

        raise HTTPException(

            status_code=503,

            detail=f"ESP32 servo command failed: {error}"

        )

    servo.current_value = 0

    basket.current_state = TrolleyState.SHOPPING.value

    event = EventLog(

        user_id=basket.current_user_id,

        basket_id=basket.basket_id,

        event_type="servo_close_command_accepted",

        event_description="ESP32 acknowledged the servo close command",

        event_metadata={

            "action": "close",

            "servo_position": 0,

            "servo_channel": data.servo_number,

            "product_id": data.product_id,

            "controller_response": controller_response,

        }

    )

    db.add(event)

    db.commit()

    db.refresh(event)

    return {

        "message": "ESP32 acknowledged the servo close command",

        "basket_id": basket.basket_id,

        "module_id": servo.module_id,

        "module_identifier": servo.module_identifier,

        "servo_number": data.servo_number,

        "servo_position": 0,

        "product_id": data.product_id,

        "event_id": event.event_id,

    }

# ============================================================

# LOAD CELL UPDATE

# ============================================================

class LoadCellUpdate(BaseModel):

    basket_id: int

    measured_weight: float = Field(ge=0)

@router.post(

    "/load-cell/update",

    summary="Update load cell reading",

    description="Updates the basket's measured weight using the connected load cell."

)

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

    if basket.basket_status != "in_use":

        raise HTTPException(

            status_code=400,

            detail="Basket is not currently in use"

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

    basket.current_weight = data.measured_weight

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

# ============================================================
# COORDINATED FOUR-SERVO CONTROL
# ============================================================

SERVO_ANGLES = {
    "open": {1: 120, 2: 120, 3: 0, 4: 0},
    "close": {1: 0, 2: 0, 3: 120, 4: 120},
}


def get_all_servos(basket_id: int, db: Session):
    servos = [
        get_servo(basket_id, db, servo_number)
        for servo_number in range(1, 5)
    ]
    return servos


def control_all_servos(
    action: str,
    data: ServoCommand,
    db: Session,
):
    basket = db.query(Basket).filter(
        Basket.basket_id == data.basket_id
    ).first()

    if not basket:
        raise HTTPException(status_code=404, detail="Basket not found")

    if basket.basket_status != "in_use":
        raise HTTPException(
            status_code=400,
            detail="Basket is not currently in use",
        )

    try:
        current_state = TrolleyState(basket.current_state)
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="Basket has an invalid trolley state",
        )

    if action == "open":
        allowed_states = {
            TrolleyState.CAMERA_VERIFYING_ADD,
            TrolleyState.CAMERA_VERIFYING_REMOVAL,
        }

        if current_state not in allowed_states:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Servos cannot open from current state: "
                    f"{current_state.value}"
                ),
            )

        try:
            transition(current_state, TrolleyState.SERVO_OPENING)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error))

    elif current_state != TrolleyState.SERVO_CLOSING:
        raise HTTPException(
            status_code=400,
            detail=(
                "Servos cannot close from current state: "
                f"{current_state.value}"
            ),
        )

    servos = get_all_servos(data.basket_id, db)

    try:
        controller_response = send_all_servos_command(action)
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=f"ESP32 coordinated servo command failed: {error}",
        )

    angles = SERVO_ANGLES[action]

    for servo in servos:
        channel = next(
            number for number in range(1, 5)
            if servo.module_identifier == (
                f"SERVO-SB{data.basket_id:03d}"
                if number == 1
                else f"SERVO-SB{data.basket_id:03d}-{number}"
            )
        )
        servo.current_value = angles[channel]

    if action == "open":
        basket.current_state = (
            TrolleyState.WAITING_FOR_ADD.value
            if current_state == TrolleyState.CAMERA_VERIFYING_ADD
            else TrolleyState.WAITING_FOR_REMOVAL.value
        )
    else:
        basket.current_state = TrolleyState.SHOPPING.value

    event = EventLog(
        user_id=basket.current_user_id,
        basket_id=basket.basket_id,
        event_type=f"servo_{action}_all_accepted",
        event_description=(
            f"ESP32 acknowledged the {action}-all command "
            "for all four servos"
        ),
        event_metadata={
            "action": f"{action}_all",
            "servo_angles": angles,
            "product_id": data.product_id,
            "controller_response": controller_response,
        },
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "message": f"All four servos acknowledged the {action} command",
        "basket_id": basket.basket_id,
        "servo_angles": angles,
        "current_state": basket.current_state,
        "event_id": event.event_id,
        "controller_response": controller_response,
    }


@router.post(
    "/servos/open-all",
    summary="Open the basket door using all four servos",
)
def open_all_servos(
    data: ServoCommand,
    db: Session = Depends(get_db),
):
    return control_all_servos("open", data, db)


@router.post(
    "/servos/close-all",
    summary="Close the basket door using all four servos",
)
def close_all_servos(
    data: ServoCommand,
    db: Session = Depends(get_db),
):
    return control_all_servos("close", data, db)
