from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional


MIN_PASSWORD_LENGTH = 8


class UserBase(BaseModel):
    user_name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    # bcrypt silently truncates beyond 72 bytes, so cap the input there.
    passwd: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=72)
    confirm_passwd: str

    @field_validator('passwd')
    @classmethod
    def password_is_strong(cls, v: str) -> str:
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain a lowercase letter')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain an uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain a digit')
        return v

    @field_validator('confirm_passwd')
    @classmethod
    def passwords_match(cls, v, info):
        if 'passwd' in info.data and v != info.data['passwd']:
            raise ValueError('Passwords do not match')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    passwd: str


class User(UserBase):
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class CartBase(BaseModel):
    cart_name: str
    cart_description: Optional[str] = None
    is_shared: bool = False


class CartCreate(CartBase):
    shared_with: list[int] = []


class CartUpdate(BaseModel):
    """Fields left out are not changed. `shared_with` is the full list of other
    members: anyone not in it is removed (the owner always stays)."""
    cart_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    cart_description: Optional[str] = None
    shared_with: Optional[list[int]] = None

    @field_validator('cart_name')
    @classmethod
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('Cart name cannot be blank')
        return v.strip() if v is not None else v


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


class Product(ProductBase):
    product_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CartItemBase(BaseModel):
    product_id: int
    quantity: int = 1


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
    sender_id: Optional[int] = None


class Message(MessageBase):
    message_id: int
    cart_id: int
    sender_id: Optional[int] = None
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=99)


class OrderLine(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class CheckoutReceipt(BaseModel):
    order_number: str
    cart_id: int
    cart_name: str
    placed_at: datetime
    items: list[OrderLine]
    total: Decimal
    # Pending items are not bought; they stay in the cart for approval.
    items_left_pending: int


class AskRequest(BaseModel):
    cart_id: int
    message: str = Field(min_length=1, max_length=2000)


class ResMessage(BaseModel):
    message_id: int
    cart_id: int
    sender_id: Optional[int] = None
    sender_type: str
    sender_name: Optional[str] = None
    message_content: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
