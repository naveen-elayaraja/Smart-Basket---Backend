from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Integer,
    Numeric,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(15), nullable=False, unique=True)
    address = Column(Text)
    role = Column(String(20), nullable=False, default="customer")
    registration_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    purchase_count = Column(Integer, nullable=False, default=0)
    account_status = Column(String(20), nullable=False, default="active")


class Basket(Base):
    __tablename__ = "baskets"

    basket_id = Column(BigInteger, primary_key=True)
    basket_number = Column(String(50), nullable=False, unique=True)
    current_user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"))
    battery_status = Column(Numeric(5, 2))
    current_weight = Column(Numeric(10, 3), nullable=False, default=0)
    connection_status = Column(String(20), nullable=False, default="offline")
    current_location = Column(String(150))
    basket_status = Column(String(20), nullable=False, default="available")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class BasketModule(Base):
    __tablename__ = "basket_modules"

    module_id = Column(BigInteger, primary_key=True)
    basket_id = Column(BigInteger, ForeignKey("baskets.basket_id", ondelete="CASCADE"), nullable=False)
    module_type = Column(String(50), nullable=False)
    module_identifier = Column(String(100))
    connection_status = Column(String(20), nullable=False, default="offline")
    module_status = Column(String(20), nullable=False, default="active")
    current_value = Column(Numeric(12, 3))
    unit = Column(String(30))
    last_seen = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    otp_hash = Column(Text)
    otp_verified = Column(Boolean, nullable=False, default=False)
    otp_expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    verified_at = Column(DateTime(timezone=True))
    logged_out_at = Column(DateTime(timezone=True))


class Product(Base):
    __tablename__ = "products"

    product_id = Column(BigInteger, primary_key=True)
    barcode = Column(String(100), nullable=False, unique=True)
    product_name = Column(String(200), nullable=False)
    category = Column(String(100))
    price = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), nullable=False, default=0)
    gst_percent = Column(Numeric(5, 2), nullable=False, default=0)
    weight = Column(Numeric(10, 3), nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    image_url = Column(Text)
    description = Column(Text)
    manufacture_date = Column(Date)
    expiry_date = Column(Date)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CartItem(Base):
    __tablename__ = "cart_items"

    cart_item_id = Column(BigInteger, primary_key=True)
    cart_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    basket_id = Column(BigInteger, ForeignKey("baskets.basket_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), nullable=False, default=0)
    weight = Column(Numeric(10, 3), nullable=False, default=0)


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    basket_id = Column(BigInteger, ForeignKey("baskets.basket_id", ondelete="RESTRICT"), nullable=False)
    cart_id = Column(UUID(as_uuid=True))
    items = Column(JSONB, nullable=False, default=list)
    total_amount = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0)
    gst_amount = Column(Numeric(12, 2), nullable=False, default=0)
    final_amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(30), nullable=False, default="UPI")
    payment_status = Column(String(30), nullable=False, default="pending")
    payment_reference = Column(String(200))
    transaction_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EventLog(Base):
    __tablename__ = "events_log"

    event_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id", ondelete="SET NULL"))
    basket_id = Column(BigInteger, ForeignKey("baskets.basket_id", ondelete="SET NULL"))
    event_type = Column(String(50), nullable=False)
    event_description = Column(Text, nullable=False)
    event_metadata = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    