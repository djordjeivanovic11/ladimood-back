from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base 
import datetime
from sqlalchemy import Enum as SqlEnum  # Import SQLAlchemy's Enum as SqlEnum
from enum import Enum as PyEnum  # Import Python's Enum as PyEnum

Base = declarative_base()

# USEFUL ENUMS #
class Size(str, PyEnum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"

class OrderStatus(str, PyEnum):  # Define your OrderStatus Enum using Python's Enum
    CREATED = "CREATED"
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

# USER DETAILS #
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    role = relationship("Role")
    address = relationship("Address", back_populates="user")
    orders = relationship("Order", back_populates="user")
    cart = relationship("Cart", back_populates="user", uselist=False)
    sales_records = relationship("SalesRecord", back_populates="user")
    wishlist = relationship("Wishlist", back_populates="user", uselist=False)

class Address(Base):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True, index=True, unique=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    street_address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=False)
    country = Column(String, nullable=False)

    user = relationship("User", back_populates="address")

# PRODUCT DETAILS #
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)

    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)  
    category_id = Column(Integer, ForeignKey("categories.id"))
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    category = relationship("Category", back_populates="products")

# CART FUNCTIONALITY #
class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart")

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey("cart.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    color = Column(String, nullable=False)  # New field for storing color
    size = Column(SqlEnum(Size), nullable=False)  # New field for storing size

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

# ORDERING FUNCTIONALITY #
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(SqlEnum(OrderStatus), default=OrderStatus.CREATED)  # Use SqlAlchemy Enum here with values passed
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    sales_records = relationship("SalesRecord", back_populates="order")

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    color = Column(String, nullable=False)
    size = Column(SqlEnum(Size), nullable=False)
    price = Column(Float, nullable=False)  

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

# WISHLIST FUNCTIONALITY #
class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="wishlist")
    items = relationship("WishlistItem", back_populates="wishlist")

class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wishlist_id = Column(Integer, ForeignKey("wishlist.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    color = Column(String, nullable=False)  # New field for storing color
    size = Column(SqlEnum(Size), nullable=False)  # New field for storing size

    wishlist = relationship("Wishlist", back_populates="items")
    product = relationship("Product")

# RECORD OF ALL SALES BY CUSTOMERS #
class SalesRecord(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    order_id = Column(Integer, ForeignKey("orders.id"))

    user = relationship("User", back_populates="sales_records")
    order = relationship("Order", back_populates="sales_records")

class NewsletterUser(Base):
    __tablename__ = "newsletter_users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
