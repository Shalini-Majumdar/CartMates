from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from models.models import User, Cart, CartUser, Product, CartItem, Message
from schemas.schemas import UserCreate, CartCreate, CartUpdate, MessageCreate
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
    return db_user


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
    member_ids = [user_id]
    for friend_id in cart.shared_with:
        if friend_id not in member_ids:
            member_ids.append(friend_id)

    existing_users = {
        u.user_id
        for u in db.query(User).filter(User.user_id.in_(member_ids)).all()
    }

    for member_id in member_ids:
        if member_id in existing_users:
            db.add(CartUser(user_id=member_id, cart_id=db_cart.cart_id))
    db.commit()

    return db_cart


def update_cart(db: Session, cart: Cart, changes: CartUpdate):
    """Apply an edit from the cart's owner. Returns the updated cart."""
    if changes.cart_name is not None:
        cart.cart_name = changes.cart_name.strip()
    if changes.cart_description is not None:
        cart.cart_description = changes.cart_description

    if changes.shared_with is not None:
        wanted = {cart.created_by} | {
            u.user_id
            for u in db.query(User).filter(User.user_id.in_(changes.shared_with)).all()
        }
        current = {
            row.user_id: row
            for row in db.query(CartUser).filter(CartUser.cart_id == cart.cart_id).all()
        }
        for user_id, row in current.items():
            if user_id not in wanted:
                db.delete(row)
        for user_id in wanted - current.keys():
            db.add(CartUser(user_id=user_id, cart_id=cart.cart_id))
        cart.is_shared = len(wanted) > 1

    db.commit()
    db.refresh(cart)
    return cart


def delete_cart(db: Session, cart_id: int):
    db_cart = db.query(Cart).filter(Cart.cart_id == cart_id).first()
    if not db_cart:
        return False

    # Cart.cart_users / cart_items / messages cascade delete-orphan, so the
    # children go with it.
    db.delete(db_cart)
    db.commit()
    return True


def get_cart_users(db: Session, cart_id: int):
    return db.query(User).join(CartUser).filter(CartUser.cart_id == cart_id).all()


def get_cart_items(db: Session, cart_id: int):
    """Cart lines with their product eager-loaded (the response embeds it)."""
    return (
        db.query(CartItem)
        .options(joinedload(CartItem.product))
        .filter(CartItem.cart_id == cart_id)
        .all()
    )


def increase_cart_item_quantity(db: Session, cart_item_id: int):
    cart_item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    if cart_item:
        cart_item.quantity += 1
        db.commit()
        db.refresh(cart_item)
        return cart_item
    return None


def decrease_cart_item_quantity(db: Session, cart_item_id: int):
    """Decrement an item, removing it at zero.

    Returns (cart_id, new_quantity). new_quantity is None when the row was
    deleted, so callers never have to introspect the returned object.
    """
    cart_item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    if cart_item is None:
        return None, None

    cart_id = cart_item.cart_id
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        db.commit()
        db.refresh(cart_item)
        return cart_id, cart_item.quantity

    db.delete(cart_item)
    db.commit()
    return cart_id, None



def approve_cart_item(db: Session, cart_item_id: int):
    cart_item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    if cart_item:
        cart_item.approved = True
        db.commit()
        db.refresh(cart_item)
        return cart_item
    return None


def disapprove_cart_item(db: Session, cart_item_id: int):
    """Remove an item from the cart. Returns its cart_id, or None if not found."""
    cart_item = db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    if cart_item:
        cart_id = cart_item.cart_id
        db.delete(cart_item)
        db.commit()
        return cart_id
    return None


def add_product_to_cart(db: Session, cart_id: int, product_id: int, quantity: int, user_id: int):
    """Add a product a member picked by hand, or top up its quantity.

    Returns the cart line, or None if the product does not exist. A person's own
    pick is approved straight away; only the assistant's suggestions wait for
    review.
    """
    if db.query(Product).filter(Product.product_id == product_id).first() is None:
        return None

    cart_item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        .first()
    )
    if cart_item:
        cart_item.quantity += quantity
        cart_item.approved = True
    else:
        cart_item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            added_by=user_id,
            quantity=quantity,
            approved=True,
        )
        db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def checkout_cart(db: Session, cart: Cart):
    """Simulated purchase: take the approved lines out of the cart.

    No payment is taken and no order is stored. Returns (lines, pending_count),
    where lines are the purchased CartItems with their products loaded; it is
    the caller's job to turn them into a receipt before they are expired.
    """
    items = get_cart_items(db, cart_id=cart.cart_id)
    purchased = [item for item in items if item.approved]
    pending = len(items) - len(purchased)

    lines = [
        {
            "product_id": item.product_id,
            "product_name": item.product.product_name,
            "quantity": item.quantity,
            "unit_price": item.product.price,
            "line_total": item.product.price * item.quantity,
        }
        for item in purchased
    ]
    for item in purchased:
        db.delete(item)
    db.commit()
    return lines, pending


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
