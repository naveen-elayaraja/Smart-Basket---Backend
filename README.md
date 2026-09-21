SMART TROLLEY
Backend
────────────────────────────────────────

Backend service for the Smart Trolley system — a connected supermarket shopping solution designed to streamline product management, basket tracking, cart operations, billing, payments, and hardware communication.

Built with Python, FastAPI, SQLAlchemy, and PostgreSQL.


OVERVIEW
────────

The Smart Trolley aims to make supermarket shopping more efficient by combining a physical trolley with software-driven product recognition, cart management, automated billing, and payment verification.

The backend acts as the central service connecting:

• Customers
• Smart trolleys
• Products
• Shopping carts
• Billing
• Transactions
• Hardware modules
• System events


FEATURES
────────

• Customer management
• Smart trolley / basket management
• Basket assignment and status tracking
• Basket module management
• Product management
• Barcode-based product lookup
• Shopping cart operations
• Cart item addition and removal
• Quantity and stock validation
• Automated bill calculation
• Discount and GST calculation
• Transaction management
• Payment status tracking
• Hardware communication endpoints
• Event logging
• PostgreSQL database integration
• RESTful API architecture


TECHNOLOGY STACK
────────────────

Python        Backend programming
FastAPI       REST API framework
SQLAlchemy    Database ORM
PostgreSQL    Relational database
Pydantic      Request validation
Uvicorn       ASGI server
Git           Version control
GitHub        Repository management


PROJECT STRUCTURE
─────────────────

smart-basket-backend/
│
├── app/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   │
│   └── routes/
│       ├── users.py
│       ├── products.py
│       ├── baskets.py
│       ├── basket_modules.py
│       ├── cart.py
│       ├── billing.py
│       ├── transactions.py
│       └── hardware.py
│
├── db/
│   └── schema.sql
│
├── .gitignore
└── README.md


API MODULES
───────────

System

GET  /        Backend status
GET  /health  Health check


Users

Customer-related operations and user management.


Products

Product registration, retrieval, and barcode-based lookup.


Baskets

Smart trolley registration, assignment, status, and basket information.


Basket Modules

Management of hardware modules associated with smart baskets.


Cart

Shopping cart operations including:

• Adding products
• Updating quantities
• Retrieving cart contents
• Removing cart items


Billing

Bill generation and calculation using:

• Product prices
• Quantities
• Discounts
• GST


Transactions

Payment and transaction record management associated with completed purchases.


Hardware

Backend endpoints for communication with smart trolley hardware components.


DATABASE
────────

PostgreSQL is used as the primary database.

Main tables:

• users
• baskets
• basket_modules
• sessions
• products
• cart_items
• transactions
• events_log

Database schema:

db/schema.sql


LOCAL SETUP
───────────

Clone the repository:

git clone https://github.com/naveen-elayaraja/Smart-Basket---Backend.git
cd Smart-Basket---Backend


Create and activate the virtual environment:

python3 -m venv venv
source venv/bin/activate


Install dependencies:

pip install -r requirements.txt


Configure PostgreSQL and apply the database schema:

psql -d smart_basket -f db/schema.sql


RUNNING THE BACKEND
───────────────────

Start the development server:

uvicorn app.main:app --reload


The API will be available at:

http://127.0.0.1:8000


Interactive API documentation:

http://127.0.0.1:8000/docs


Alternative API documentation:

http://127.0.0.1:8000/redoc


DEVELOPMENT WORKFLOW
────────────────────

Python files can be checked before committing:

python -m py_compile app/main.py app/routes/*.py


Git is used for version control and GitHub is used for remote repository management.


CURRENT STATUS
──────────────

The backend currently contains the core API modules required for:

• User management
• Product management
• Basket management
• Basket modules
• Cart operations
• Billing
• Transactions
• Hardware integration

Further development will focus on connecting these APIs with the physical Smart Trolley hardware and completing the end-to-end shopping workflow.


FUTURE DEVELOPMENT
───────────────────

• Real-time hardware communication
• Product recognition integration
• Load-cell based weight verification
• Automated basket state updates
• Payment gateway integration
• Purchase verification
• Security and anti-theft mechanisms
• Frontend integration
• End-to-end workflow testing


PROJECT
───────

Smart Trolley

Backend API and database layer for a connected supermarket shopping system.

Built as part of an integrated hardware and software project.
