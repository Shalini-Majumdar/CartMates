from sqlalchemy import Column, Integer, String, Text, Boolean, DECIMAL, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    passwd = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    created_carts = relationship("Cart", back_populates="creator")
    cart_users = relationship("CartUser", back_populates="user")
    cart_items = relationship("CartItem", back_populates="added_by_user")
    messages = relationship("Message", back_populates="sender")


class Cart(Base):
    __tablename__ = "carts"
    
    cart_id = Column(Integer, primary_key=True, index=True)
    cart_name = Column(String(255), nullable=False)
    cart_description = Column(Text)
    date_created = Column(TIMESTAMP, default=func.current_timestamp())
    is_shared = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    
    # Relationships
    creator = relationship("User", back_populates="created_carts")
    cart_users = relationship("CartUser", back_populates="cart")
    cart_items = relationship("CartItem", back_populates="cart")
    messages = relationship("Message", back_populates="cart")


class CartUser(Base):
    __tablename__ = "cart_users"
    
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.cart_id"), primary_key=True)
    
    # Relationships
    user = relationship("User", back_populates="cart_users")
    cart = relationship("Cart", back_populates="cart_users")


class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(255), nullable=False)
    product_description = Column(Text)
    image_url = Column(String(500))
    price = Column(DECIMAL(10, 2), nullable=False)
    category = Column(String(100))
    created_at = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    cart_items = relationship("CartItem", back_populates="product")


class CartItem(Base):
    __tablename__ = "cart_items"
    
    cart_item_id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.cart_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    added_by = Column(Integer, ForeignKey("users.user_id"))
    quantity = Column(Integer, default=1)
    approved = Column(Boolean, default=False)
    date_added = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    cart = relationship("Cart", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")
    added_by_user = relationship("User", back_populates="cart_items")


class Message(Base):
    __tablename__ = "messages"
    
    message_id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.cart_id"))
    sender_id = Column(Integer, ForeignKey("users.user_id"))
    sender_type = Column(String(50), default='assistant')
    message_content = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    cart = relationship("Cart", back_populates="messages")
    sender = relationship("User", back_populates="messages")