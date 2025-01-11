from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum
import datetime



# AUTHENTICATION SCHEMAS #
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Message(BaseModel):
    message: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr



# ENUMS #
class SizeEnum(str, Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"

class OrderStatusEnum(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# USER DETAILS #
class RoleBase(BaseModel):
    name: str

class Role(RoleBase):
    id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    role: Optional[Role] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class AddressBase(BaseModel):
    street_address: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str
    

class Address(AddressBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# PRODUCT RELATED SCHEMAS #
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    category_id: int

class Product(ProductBase):
    id: int
    category: Category
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


# CART AND ORDERING SCHEMAS #
class CartItem(BaseModel):
    id: int
    product: Product  
    quantity: int
    color: str  
    size: SizeEnum

    class Config:
        from_attributes = True

class Cart(BaseModel):
    id: int
    user_id: int
    items: List[CartItem]

    class Config:
        from_attributes = True

# Updated OrderItem schema
class OrderItem(BaseModel):
    id: Optional[int] = None
    product: Product  # Full Product object
    quantity: int
    color: str
    size: SizeEnum  # Enum type for internal use
    price: float

    class Config:
        orm_mode = True  # Use orm_mode instead of from_attributes


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str  # Flattened field for API response
    quantity: int
    color: str
    size: str  # String for API response
    price: float

    class Config:
        orm_mode = True  # Consistent with ORM models

class OrderResponse(BaseModel):
    id: int
    user_id: int
    plain_id: Optional[int] = None  # keep an optional plain_id if you need it
    user: Optional[User]  # Full user details from the existing User schema
    status: str
    total_price: float
    items: List[OrderItemResponse]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    address: Optional[dict]  # Fetched via user_id

    class Config:
        orm_mode = True


class Order(BaseModel):
    id: int
    user_id: int
    status: OrderStatusEnum
    total_price: float
    items: List[OrderItem]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_id: int  
    quantity: int
    color: str
    size: SizeEnum
    price: float 

class OrderCreate(BaseModel):
    status: OrderStatusEnum
    total_price: float
    items: List[OrderItemCreate]


# WISHLIST SCHEMA #
class WishlistItem(BaseModel):
    id: int
    product: Product
    color: str  
    size: SizeEnum  

    class Config:
        from_attributes = True

class Wishlist(BaseModel):
    id: int
    user_id: int
    items: List[WishlistItem]
    

    class Config:
        from_attributes = True


# SALES RECORD SCHEMAS #
class SalesRecordBase(BaseModel):
    user_id: int
    order_id: int


class SalesRecordCreate(SalesRecordBase):
    pass


class SalesRecord(SalesRecordBase):
    id: int
    user: Optional["User"] 
    order: Optional["Order"]

    class Config:
        orm_mode = True


class UpdateStatusRequest(BaseModel):
    status: OrderStatusEnum



# NEWSLETTER SCHEMAS #

class NewsletterUserSchema(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True


# REFERRAL SCHEMAS #
class Referral(BaseModel):
    name: str
    email: str

class ReferralRequest(BaseModel):
    referrals: List[Referral]