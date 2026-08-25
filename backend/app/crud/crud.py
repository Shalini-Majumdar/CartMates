from sqlalchemy.orm import Session
from sqlalchemy import func
from models.models import User, Cart, CartUser, Product, CartItem, Message
from schemas.schemas import UserCreate, CartCreate, ProductCreate, CartItemCreate, MessageCreate, CartItemResponse
import bcrypt
from decimal import Decimal


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_all_users(db: Session):
    return db.query(User).all()

def create_user(db: Session, user: UserCreate):
    hashed_password = bcrypt.hashpw(user.passwd.encode('utf-8'), bcrypt.gensalt())
    db_user = User(
        user_name=user.user_name,
        email=user.email,
        passwd=hashed_password.decode('utf-8')
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return User.model_validate(db_user)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def calculate_cart_total(db: Session, cart_id: int) -> Decimal:
    """Calculate the total price of approved items in a cart"""
    total = db.query(func.sum(CartItem.quantity * Product.price))\
              .join(Product, CartItem.product_id == Product.product_id)\
              .filter(CartItem.cart_id == cart_id)\
              .filter(CartItem.approved == True)\
              .scalar()
    
    return total or Decimal('0.00')


def get_user_carts_with_totals(db: Session, user_id: int):
    """Get user carts with calculated totals"""
    carts = db.query(Cart).join(CartUser).filter(CartUser.user_id == user_id).all()
    
    # Calculate total for each cart
    for cart in carts:
        users_in_cart = db.query(User).join(CartUser).filter(CartUser.cart_id == cart.cart_id).all()
        user_names = [user.user_name for user in users_in_cart]

        cart.total = calculate_cart_total(db, cart.cart_id)

        cart.shared_usernames = user_names

    return carts


def create_cart(db: Session, cart: CartCreate, user_id: int):
    db_cart = Cart(
        cart_name=cart.cart_name,
        cart_description=cart.cart_description,
        is_shared=cart.is_shared,
        created_by=user_id
    )
    db.add(db_cart)
    db.commit()
    db.refresh(db_cart)
    
    # Add creator to cart_users
    cart_user = CartUser(user_id=user_id, cart_id=db_cart.cart_id)
    db.add(cart_user)
    db.commit()
    
    return db_cart


def delete_cart(db: Session, cart_id: int):
    cart_users = db.query(CartUser).filter(CartUser.cart_id == cart_id).all()
    for cart_user in cart_users:
        db.delete(cart_user)
    db_cart = db.query(Cart).filter(Cart.cart_id == cart_id).first()
    if db_cart:
        db.delete(db_cart)
        db.commit()
        return True
    return False


def get_cart_users(db: Session, cart_id: int):
    return db.query(User).join(CartUser).filter(CartUser.cart_id == cart_id).all()


def get_cart_products(db: Session, cart_id: int):
    return db.query(CartItem).filter(CartItem.cart_id == cart_id).all()


def get_cart_item(db: Session, cart_item_id: int):
    return db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()


def increase_cart_item_quantity(db: Session, cart_item_id: int):
    cart_item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    if cart_item:
        cart_item.quantity += 1
        db.commit()
        db.refresh(cart_item)
        return cart_item
    return None


def decrease_cart_item_quantity(db: Session, cart_item_id: int):
    cart_item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    if cart_item:
        cart_id = cart_item.cart_id
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            db.commit()
            db.refresh(cart_item)
            return cart_item
        else:
            db.delete(cart_item)
            db.commit()
            # Return a dummy object with the cart_id
            class DeletedItem:
                def __init__(self, cart_id):
                    self.cart_id = cart_id
            return DeletedItem(cart_id)
    return None



def approve_cart_item(db: Session, cart_item_id: int):
    cart_item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    if cart_item:
        cart_item.approved = True
        db.commit()
        db.refresh(cart_item)
        return cart_item
    return None


def disapprove_cart_item(db: Session, cart_item_id: int):
    cart_item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    if cart_item:
        db.delete(cart_item)
        db.commit()
        return True
    return False


def create_message(db: Session, message: MessageCreate):
    db_message = Message(
        cart_id=message.cart_id,
        sender_id=message.sender_id,
        sender_type=message.sender_type,
        message_content=message.message_content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def add_items_to_cart(db: Session, cart_id: int, user_id: int, items: list[CartItemResponse]) -> list[str]:
    """Add items to cart and return list of success/error messages"""
    results = []
    
    for item in items:
        try:
            # Check if product exists
            product = db.query(Product).filter(Product.product_id == item.product_id).first()
            if not product:
                results.append(f"Product with ID {item.product_id} not found")
                continue
            
            # Check if item already exists in cart
            existing_item = db.query(CartItem).filter(
                CartItem.cart_id == cart_id,
                CartItem.product_id == item.product_id,
                CartItem.added_by == user_id
            ).first()
            
            if existing_item:
                # Update quantity of existing item
                existing_item.quantity += item.quantity
                db.commit()
                results.append(f"Updated {product.product_name} quantity to {existing_item.quantity}")
            else:
                # Create new cart item
                cart_item = CartItem(
                    cart_id=cart_id,
                    product_id=item.product_id,
                    added_by=user_id,
                    quantity=item.quantity,
                    approved=False  # Items need approval by default
                )
                db.add(cart_item)
                db.commit()
                results.append(f"Added {item.quantity}x {product.product_name} to cart")
                
        except Exception as e:
            results.append(f"Error adding product {item.product_id}: {str(e)}")
            db.rollback()
    
    return results