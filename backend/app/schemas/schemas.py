from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional


class UserBase(BaseModel):
    user_name: str
    email: str


class UserCreate(UserBase):
    passwd: str
    confirm_passwd: str

    @field_validator('confirm_passwd')
    @classmethod
    def passwords_match(cls, v, info):
        if 'passwd' in info.data and v != info.data['passwd']:
            raise ValueError('Passwords do not match')
        return v


class UserLogin(BaseModel):
    email: str
    passwd: str


class User(UserBase):
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)


class CartBase(BaseModel):
    cart_name: str
    cart_description: Optional[str] = None
    is_shared: bool = False


class CartCreate(CartBase):
    pass


class Cart(CartBase):
    cart_id: int
    date_created: datetime
    created_by: int
    total: Decimal = Decimal('0.00')
    shared_usernames: list[str] = []
    
    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    product_name: str
    product_description: Optional[str] = None
    image_url: Optional[str] = None
    price: Decimal
    category: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    product_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CartItemBase(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemCreate(CartItemBase):
    cart_id: int
    added_by: int


class CartItem(CartItemBase):
    cart_item_id: int
    cart_id: int
    added_by: int
    approved: bool
    date_added: datetime
    product: Product
    
    model_config = ConfigDict(from_attributes=True)


class MessageBase(BaseModel):
    message_content: str
    sender_type: str = 'user'


class MessageCreate(MessageBase):
    cart_id: int
    sender_id: int


class Message(MessageBase):
    message_id: int
    cart_id: int
    sender_id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CartItemUpdate(BaseModel):
    quantity: int


class AskRequest(BaseModel):
    user_id: int
    cart_id: int
    message: str


class CartItemResponse(BaseModel):
    product_id: int
    quantity: int

class LLMResponse(BaseModel):
    items: list[CartItemResponse]

class ParsedResponse(BaseModel):
    message: str
    items: list[CartItemResponse]
    error: Optional[str] = None

class ResMessage(BaseModel):
    message_id: int
    cart_id: int
    sender_id: int
    sender_type: str
    sender_name: Optional[str] = None
    message_content: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
