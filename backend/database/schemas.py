from pydantic import BaseModel, EmailStr
from typing import Optional, List, Union
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

class OrderItem(BaseModel):
    id: Optional[int] = None
    product: Product 
    quantity: int
    color: str
    size: SizeEnum 
    price: float

    class Config:
        orm_mode = True 


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str  
    quantity: int
    color: str
    size: str 
    price: float
    product_image_url: Optional[str] = None

    class Config:
        orm_mode = True  

class OrderResponse(BaseModel):
    id: Union[int, str]
    user_id: int
    user: Optional[User] = None  
    status: str
    total_price: float
    items: List[OrderItemResponse]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    address: Optional[dict] = None  

    class Config:
        orm_mode = True

class PublicOrderResponse(BaseModel):
    id: str  
    user_id: int
    plain_id: Optional[int] = None  
    user: Optional[User] = None 
    status: str
    total_price: float
    items: List[OrderItemResponse]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    address: Optional[dict] = None  

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


# WISHLIST SCHEMAS #
class WishlistItemCreate(BaseModel):
    product_id: int
    color: str
    size: SizeEnum

class WishlistItemRead(BaseModel):
    id: int
    product: Product
    color: str
    size: SizeEnum

    class Config:
        from_attributes = True

class Wishlist(BaseModel):
    id: int
    user_id: int
    items: List[WishlistItemRead]
    

    class Config:
        from_attributes = True

class SalesRecordBase(BaseModel):
    user_id: int
    order_id: int

class SalesRecordCreate(SalesRecordBase):
    date_of_sale: datetime
    buyer_name: str
    price: float

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class SalesRecord(SalesRecordBase):
    id: int
    user: Optional["User"]
    order: Optional["Order"]
    date_of_sale: datetime
    buyer_name: str
    price: float

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True



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

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    phone: str
    message: str
    inquiry_type: str
