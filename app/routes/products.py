from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date

from app.database import get_db
from app.models import Product


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


class ProductCreate(BaseModel):
    barcode: str
    product_name: str
    category: str | None = None
    price: float
    discount_percent: float = 0
    gst_percent: float = 0
    weight: float
    stock_quantity: int = 0
    image_url: str | None = None
    description: str | None = None
    manufacture_date: date | None = None
    expiry_date: date | None = None


@router.post("/")
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    existing_product = (
        db.query(Product)
        .filter(Product.barcode == product_data.barcode)
        .first()
    )

    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product with this barcode already exists"
        )

    product = Product(
        barcode=product_data.barcode,
        product_name=product_data.product_name,
        category=product_data.category,
        price=product_data.price,
        discount_percent=product_data.discount_percent,
        gst_percent=product_data.gst_percent,
        weight=product_data.weight,
        stock_quantity=product_data.stock_quantity,
        image_url=product_data.image_url,
        description=product_data.description,
        manufacture_date=product_data.manufacture_date,
        expiry_date=product_data.expiry_date,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return {
        "message": "Product added successfully",
        "product_id": product.product_id,
        "product_name": product.product_name,
        "barcode": product.barcode
    }


@router.get("/")
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()

    return products


@router.get("/{barcode}")
def get_product(
    barcode: str,
    db: Session = Depends(get_db)
):
    product = (
        db.query(Product)
        .filter(Product.barcode == barcode)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product