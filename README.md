# Smart Trolley Backend

Backend API for the Smart Trolley system, designed to support a smart supermarket shopping experience with automated product management, cart tracking, billing, and payment processing.

## 🚀 Project Overview

The Smart Trolley is designed to make supermarket shopping faster, safer, and more convenient.

The trolley communicates with the backend to manage customers, products, baskets, shopping carts, transactions, and system events.

## ✨ Features

- Customer management
- Smart trolley/basket management
- Product management
- Product barcode lookup
- Shopping cart management
- Automated billing
- Discount and GST calculation
- Payment transaction tracking
- Event logging
- PostgreSQL database integration
- RESTful API using FastAPI

## 🛠️ Tech Stack

- **Python**
- **FastAPI**
- **SQLAlchemy**
- **PostgreSQL**
- **Uvicorn**
- **Git & GitHub**

## 📁 Project Structure

```text
smart-basket-backend/
│
├── app/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   │
│   └── routes/
│       └── products.py
│
├── db/
│   └── schema.sql
│
├── .gitignore
└── README.md
## 🔌 API

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Check backend status |
| GET | `/health` | Health check |

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/` | Get all products |
| POST | `/products/` | Create a product |
| GET | `/products/{barcode}` | Get product by barcode |

## 🗄️ Database

The backend uses PostgreSQL with the following tables:

- Users
- Baskets
- Basket Modules
- Sessions
- Products
- Cart Items
- Transactions
- Events Log

## ▶️ Running the Backend

Activate the virtual environment:

```bash
source venv/bin/activate