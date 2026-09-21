import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CartItem, Product


router = APIRouter(
    prefix="/billing",
    tags=["Billing"]
)


@router.get("/{cart_id}")
def calculate_bill(
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

    subtotal = Decimal("0.00")
    discount_amount = Decimal("0.00")
    gst_amount = Decimal("0.00")

    bill_items = []

    for item in items:

        product = db.query(Product).filter(
            Product.product_id == item.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )

        item_total = Decimal(item.unit_price) * item.quantity

        item_discount = (
            item_total *
            Decimal(item.discount_percent) /
            Decimal("100")
        )

        taxable_item_amount = item_total - item_discount

        item_gst = (
            taxable_item_amount *
            Decimal(product.gst_percent) /
            Decimal("100")
        )

        subtotal += item_total
        discount_amount += item_discount
        gst_amount += item_gst

        bill_items.append({
            "product_id": item.product_id,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "item_total": round(float(item_total), 2),
            "discount_percent": float(item.discount_percent),
            "discount_amount": round(float(item_discount), 2),
            "gst_percent": float(product.gst_percent),
            "gst_amount": round(float(item_gst), 2),
            "weight": float(item.weight)
        })

    taxable_amount = subtotal - discount_amount
    final_amount = taxable_amount + gst_amount

    return {
        "cart_id": str(cart_id),
        "items": bill_items,
        "subtotal": round(float(subtotal), 2),
        "discount_amount": round(float(discount_amount), 2),
        "taxable_amount": round(float(taxable_amount), 2),
        "gst_amount": round(float(gst_amount), 2),
        "final_amount": round(float(final_amount), 2)
    }