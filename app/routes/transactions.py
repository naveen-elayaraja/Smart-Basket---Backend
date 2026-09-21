import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Transaction, CartItem, User, Basket, Product


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


# ============================================================
# CREATE TRANSACTION
# ============================================================

@router.post("/")
def create_transaction(
    cart_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    items = db.query(CartItem).filter(
        CartItem.cart_id == cart_id
    ).all()

    if not items:
        raise HTTPException(
            status_code=404,
            detail="Cart not found or cart is empty"
        )

    user_id = items[0].user_id
    basket_id = items[0].basket_id

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    basket = db.query(Basket).filter(
        Basket.basket_id == basket_id
    ).first()

    if not basket:
        raise HTTPException(
            status_code=404,
            detail="Basket not found"
        )

    total_amount = 0
    discount_amount = 0
    gst_amount = 0

    transaction_items = []

    for item in items:

        product = db.query(Product).filter(
            Product.product_id == item.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )

        item_total = float(item.unit_price) * item.quantity

        item_discount = (
            item_total
            * float(item.discount_percent)
            / 100
        )

        taxable_amount = item_total - item_discount

        # Calculate GST using the product's GST percentage
        item_gst = (
            taxable_amount
            * float(product.gst_percent)
            / 100
        )

        total_amount += item_total
        discount_amount += item_discount
        gst_amount += item_gst

        transaction_items.append({
            "product_id": item.product_id,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "discount_percent": float(item.discount_percent),
            "gst_percent": float(product.gst_percent),
            "weight": float(item.weight)
        })

    final_amount = (
        total_amount
        - discount_amount
        + gst_amount
    )

    transaction = Transaction(
        user_id=user_id,
        basket_id=basket_id,
        cart_id=cart_id,
        items=transaction_items,
        total_amount=round(total_amount, 2),
        discount_amount=round(discount_amount, 2),
        gst_amount=round(gst_amount, 2),
        final_amount=round(final_amount, 2),
        payment_method="UPI",
        payment_status="pending"
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return {
        "message": "Transaction created successfully",
        "transaction_id": transaction.transaction_id,
        "user_id": transaction.user_id,
        "basket_id": transaction.basket_id,
        "cart_id": str(transaction.cart_id),
        "total_amount": float(transaction.total_amount),
        "discount_amount": float(transaction.discount_amount),
        "gst_amount": float(transaction.gst_amount),
        "final_amount": float(transaction.final_amount),
        "payment_method": transaction.payment_method,
        "payment_status": transaction.payment_status,
        "items": transaction.items
    }


# ============================================================
# GET TRANSACTION
# ============================================================

@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction


# ============================================================
# PAYMENT UPDATE MODEL
# ============================================================

class PaymentUpdate(BaseModel):
    payment_status: str
    payment_reference: str | None = None


# ============================================================
# UPDATE PAYMENT
# ============================================================

@router.post("/{transaction_id}/payment")
def update_payment(
    transaction_id: int,
    payment: PaymentUpdate,
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    # These values are allowed by the database constraint
    allowed_statuses = [
        "pending",
        "successful",
        "failed",
        "cancelled"
    ]

    if payment.payment_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment status"
        )

    # Update payment status
    transaction.payment_status = payment.payment_status

    # Save payment reference if provided
    if payment.payment_reference:
        transaction.payment_reference = payment.payment_reference

    # If payment is successful,
    # return the basket to available status
    if payment.payment_status == "successful":

        basket = db.query(Basket).filter(
            Basket.basket_id == transaction.basket_id
        ).first()

        if basket:
            basket.basket_status = "available"

    # Save transaction + basket changes
    db.commit()
    db.refresh(transaction)

    return {
        "message": "Payment status updated successfully",
        "transaction_id": transaction.transaction_id,
        "payment_status": transaction.payment_status,
        "payment_reference": transaction.payment_reference,
        "final_amount": float(transaction.final_amount)
    }