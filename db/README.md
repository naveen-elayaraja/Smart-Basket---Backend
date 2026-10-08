# Smart Basket Database

This directory contains the database schema and database-related files for the Smart Basket backend.

## Database

- Database: PostgreSQL
- Database name: `smart_basket`

## Main Tables

- `users` — customer information
- `baskets` — smart basket/trolley information and current state
- `basket_modules` — hardware modules assigned to baskets
- `sessions` — user/basket sessions
- `products` — supermarket product information
- `cart_items` — products currently in a shopping cart
- `transactions` — billing and payment transactions
- `events_log` — hardware and system event history

## Architecture

```text
Frontend
   |
   v
FastAPI Backend
   |
   v
PostgreSQL
   |
   +-- Users
   +-- Baskets
   +-- Products
   +-- Cart
   +-- Transactions
   +-- Events