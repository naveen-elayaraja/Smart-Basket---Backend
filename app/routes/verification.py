
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Basket, Product, EventLog
from app.services.camera_recognition import capture_product_image
from app.services.product_matcher import recognize_product

router = APIRouter(prefix="/verification", tags=["Camera Verification"])


class CameraVerificationRequest(BaseModel):
    basket_id: int = Field(ge=1)
    selected_product_id: int = Field(ge=1)
    action: Literal["add", "remove"] = "add"


class CameraResultRequest(BaseModel):
    basket_id: int = Field(ge=1)
    action: Literal["add", "remove"] = "add"


@router.post("/scan")
def verify_product(
    data: CameraVerificationRequest,
    db: Session = Depends(get_db),
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

    product = db.query(Product).filter(
        Product.product_id == data.selected_product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        # Invalidate previous authorizations for this basket.
        db.execute(
            text("""
                UPDATE servo_authorizations
                   SET consumed_at = NOW()
                 WHERE basket_id = :basket_id
                   AND consumed_at IS NULL
            """),
            {"basket_id": basket.basket_id},
        )

        event = EventLog(
            user_id=basket.current_user_id,
            basket_id=basket.basket_id,
            event_type="camera_verification_requested",
            event_description="Product camera verification requested",
            event_metadata={
                "selected_product_id": product.product_id,
                "action": data.action,
            },
        )
        db.add(event)
        db.commit()
        db.refresh(event)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to record camera verification request",
        )

    return {
        "basket_id": basket.basket_id,
        "selected_product_id": product.product_id,
        "selected_product_name": product.product_name,
        "action": data.action,
        "event_id": event.event_id,
        "message": "Request recorded. Submit the camera result to verify the product.",
    }


@router.post("/camera-result")
def submit_camera_result(
    data: CameraResultRequest,
    db: Session = Depends(get_db),
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

    # Use the most recent request matching this basket and action.
    request_event = (
        db.query(EventLog)
        .filter(
            EventLog.basket_id == basket.basket_id,
            EventLog.event_type == "camera_verification_requested",
        )
        .order_by(EventLog.event_id.desc())
        .first()
    )

    if not request_event or not request_event.event_metadata:
        raise HTTPException(
            status_code=409,
            detail="No pending camera verification request",
        )

    metadata = request_event.event_metadata

    if metadata.get("action") != data.action:
        raise HTTPException(
            status_code=409,
            detail="Camera action does not match the pending request",
        )

    selected_product_id = metadata.get("selected_product_id")

    product = db.query(Product).filter(
        Product.product_id == selected_product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Prevent the same request from issuing multiple tokens.
    # Mark the request consumed before capturing the image.
    request_event.event_type = "camera_verification_processing"
    db.commit()

    try:
        image_path = capture_product_image()
        result = recognize_product(image_path=image_path)

        candidate_id = result.get("candidate_product_id")
        recognized = result.get("recognized", False)

        if not recognized:
            outcome = "UNCERTAIN"
        elif candidate_id != selected_product_id:
            outcome = "MISMATCH"
        else:
            outcome = "MATCH"

        authorization_token = None

        if outcome == "MATCH":
            # The hardware authorization helper expects a UUID.
            authorization_token = str(uuid4())

            db.execute(
                text("""
                    INSERT INTO servo_authorizations
                        (token, basket_id, product_id, operation, expires_at)
                    VALUES
                        (
                            CAST(:token AS UUID),
                            :basket_id,
                            :product_id,
                            :operation,
                            :expires_at
                        )
                """),
                {
                    "token": authorization_token,
                    "basket_id": basket.basket_id,
                    "product_id": product.product_id,
                    "operation": (
                        "add" if data.action == "add" else "removal"
                    ),
                    "expires_at": (
                        datetime.now(timezone.utc) + timedelta(seconds=30)
                    ),
                },
            )

        result_event = EventLog(
            user_id=basket.current_user_id,
            basket_id=basket.basket_id,
            event_type=(
                "camera_verification_passed"
                if outcome == "MATCH"
                else "camera_verification_failed"
            ),
            event_description=f"Camera verification result: {outcome}",
            event_metadata={
                "selected_product_id": selected_product_id,
                "candidate_product_id": candidate_id,
                "action": data.action,
                "outcome": outcome,
                "best_score": result.get("best_score"),
                "runner_up_score": result.get("runner_up_score"),
                "score_ratio": result.get("score_ratio"),
            },
        )
        db.add(result_event)
        db.commit()
        db.refresh(result_event)

        return {
            "basket_id": basket.basket_id,
            "selected_product_id": selected_product_id,
            "selected_product_name": product.product_name,
            "action": data.action,
            "outcome": outcome,
            "recognition": result,
            "event_id": result_event.event_id,
            "servo_authorized": authorization_token is not None,
            "authorization_token": authorization_token,
        }

    except HTTPException:
        raise
    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Camera verification failed: {type(error).__name__}",
        ) from error
