from fastapi import FastAPI

from app.models import (
    User,
    Basket,
    BasketModule,
    Session,
    Product,
    CartItem,
    Transaction,
    EventLog,
)

from app.routes.products import router as products_router


app = FastAPI(
    title="Smart Trolley API",
    description="Backend API for the Smart Trolley system",
    version="1.0.0"
)


app.include_router(products_router)


@app.get("/")
def root():
    return {
        "message": "Smart Trolley Backend is running",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }