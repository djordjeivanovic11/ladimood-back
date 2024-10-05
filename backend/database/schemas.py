from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum
import datetime

                                        # AUTHENTICATION SCHEMAS #
#---------------------------------------------------------------------------------------------#

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
# Updated CartItem schema
class CartItem(BaseModel):
    id: int
    product: Product  # Assuming Product is already defined in your schemas
    quantity: int
    color: str  # New field for color
    size: SizeEnum  # New field for size

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
    product: Product  
    quantity: int
    color: str
    size: SizeEnum
    price: float 

    class Config:
        from_attributes = True

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    color: str
    size: str
    price: float 

    class Config:
        orm_mode = True

class OrderResponse(BaseModel):
    id: str  
    user_id: int
    status: str
    total_price: float
    items: List[OrderItemResponse]  
    created_at: datetime.datetime
    updated_at: datetime.datetime

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
    product: Product  # Assuming Product is already defined in your schemas
    color: str  # New field for color
    size: SizeEnum  # New field for size

    class Config:
        from_attributes = True

class Wishlist(BaseModel):
    id: int
    user_id: int
    items: List[WishlistItem]
    

    class Config:
        from_attributes = True


# SALES RECORD SCHEMAS #
class SalesRecord(BaseModel):
    id: int
    user: User
    orders: List[Order]

    class Config:
        from_attributes = True

class NewsletterUserSchema(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True


class Referral(BaseModel):
    name: str
    email: str

class ReferralRequest(BaseModel):
    referrals: List[Referral]