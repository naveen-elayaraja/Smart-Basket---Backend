from fastapi import FastAPI

from app.routes.products import router as products_router
from app.routes.users import router as users_router
from app.routes.baskets import router as baskets_router
from app.routes.basket_modules import router as basket_modules_router


app = FastAPI(
    title="Smart Trolley Backend",
    description="Backend API for the Smart Trolley system",
    version="1.0.0"
)


# Product APIs
app.include_router(products_router)

# User APIs
app.include_router(users_router)

# Basket APIs
app.include_router(baskets_router)

# Basket Module APIs
app.include_router(basket_modules_router)


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