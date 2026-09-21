import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import CartItem, User, Basket, Product


router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


class CartItemCreate(BaseModel):
    cart_id: str | None = None
    user_id: int
    basket_id: int
    product_id: int
    quantity: int = 1


@router.post("/items")
def add_cart_item(
    item: CartItemCreate,
    db: Session = Depends(get_db)
):
    # ---------------------------------------------------------
    # 1. Check user
    # ---------------------------------------------------------
    user = db.query(User).filter(
        User.user_id == item.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # ---------------------------------------------------------
    # 2. Check basket
    # ---------------------------------------------------------
    basket = db.query(Basket).filter(
        Basket.basket_id == item.basket_id
    ).first()

    if not basket:
        raise HTTPException(
            status_code=404,
            detail="Basket not found"
        )

    # ---------------------------------------------------------
    # 3. Basket must be in use
    # ---------------------------------------------------------
    if basket.basket_status != "in_use":
        raise HTTPException(
            status_code=400,
            detail="Basket is not currently in use"
        )

    # ---------------------------------------------------------
    # 4. Make sure basket belongs to this user
    # ---------------------------------------------------------
    if basket.current_user_id != item.user_id:
        raise HTTPException(
            status_code=400,
            detail="Basket is assigned to a different user"
        )

    # ---------------------------------------------------------
    # 5. Check product
    # ---------------------------------------------------------
    product = db.query(Product).filter(
        Product.product_id == item.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # ---------------------------------------------------------
    # 6. Check quantity
    # ---------------------------------------------------------
    if item.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    # ---------------------------------------------------------
    # 7. Check stock
    # ---------------------------------------------------------
    if item.quantity > product.stock_quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient product stock"
        )

    # ---------------------------------------------------------
    # 8. Use existing cart ID or create a new cart
    # ---------------------------------------------------------
    if item.cart_id:
        try:
            cart_id = uuid.UUID(item.cart_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid cart_id"
            )
    else:
        cart_id = uuid.uuid4()

    # ---------------------------------------------------------
    # 9. Check whether product already exists in cart
    # ---------------------------------------------------------
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart_id,
        CartItem.product_id == item.product_id
    ).first()

    if existing_item:
        new_quantity = existing_item.quantity + item.quantity

        if new_quantity > product.stock_quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient product stock"
            )

        existing_item.quantity = new_quantity
        existing_item.weight = product.weight * new_quantity

        db.commit()
        db.refresh(existing_item)

        return {
            "message": "Cart item quantity updated successfully",
            "cart_item_id": existing_item.cart_item_id,
            "cart_id": str(existing_item.cart_id),
            "user_id": existing_item.user_id,
            "basket_id": existing_item.basket_id,
            "product_id": existing_item.product_id,
            "product_name": existing_item.product_name,
            "quantity": existing_item.quantity,
            "unit_price": existing_item.unit_price,
            "discount_percent": existing_item.discount_percent,
            "weight": existing_item.weight
        }

    # ---------------------------------------------------------
    # 10. Create new cart item
    # ---------------------------------------------------------
    new_item = CartItem(
        cart_id=cart_id,
        user_id=item.user_id,
        basket_id=item.basket_id,
        product_id=item.product_id,
        product_name=product.product_name,
        quantity=item.quantity,
        unit_price=product.price,
        discount_percent=product.discount_percent,
        weight=product.weight * item.quantity
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {
        "message": "Product added to cart successfully",
        "cart_item_id": new_item.cart_item_id,
        "cart_id": str(new_item.cart_id),
        "user_id": new_item.user_id,
        "basket_id": new_item.basket_id,
        "product_id": new_item.product_id,
        "product_name": new_item.product_name,
        "quantity": new_item.quantity,
        "unit_price": new_item.unit_price,
        "discount_percent": new_item.discount_percent,
        "weight": new_item.weight
    }


@router.get("/{cart_id}")
def get_cart(
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

    return items 