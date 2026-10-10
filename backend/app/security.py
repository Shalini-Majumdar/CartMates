"""Authentication and authorisation.

Two rules hold everywhere in this application:

1. The caller's identity comes from a signed token, never from a path
   parameter or request body. `get_current_user` is the only source of truth.
2. Anything scoped to a cart goes through `ensure_cart_member`, so belonging
   to the cart is checked before it is read or modified.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.models import Cart, CartItem, CartUser, User

ALGORITHM = "HS256"

_bearer = HTTPBearer(auto_error=False)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def create_access_token(user_id: int) -> str:
    """Issue a signed access token for a user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the caller from their bearer token.

    Every authenticated route depends on this. A route that does not depend on
    it is public by definition, so add it deliberately.
    """
    if credentials is None or not credentials.credentials:
        raise _CREDENTIALS_ERROR

    try:
        payload = jwt.decode(
            credentials.credentials, settings.secret_key, algorithms=[ALGORITHM]
        )
        subject = payload.get("sub")
        if subject is None:
            raise _CREDENTIALS_ERROR
        user_id = int(subject)
    except (jwt.PyJWTError, TypeError, ValueError):
        raise _CREDENTIALS_ERROR

    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        # Token was valid but the account is gone.
        raise _CREDENTIALS_ERROR
    return user


def ensure_cart_member(db: Session, cart_id: int, user: User) -> Cart:
    """Return the cart, or refuse if the caller is not one of its members.

    Missing carts and carts belonging to other people both yield 404, so this
    cannot be used to probe which cart ids exist.
    """
    cart = db.query(Cart).filter(Cart.cart_id == cart_id).first()
    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found"
        )

    membership = (
        db.query(CartUser)
        .filter(CartUser.cart_id == cart_id, CartUser.user_id == user.user_id)
        .first()
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found"
        )
    return cart


def ensure_cart_owner(db: Session, cart_id: int, user: User) -> Cart:
    """Like `ensure_cart_member`, but only the cart's creator passes."""
    cart = ensure_cart_member(db, cart_id, user)
    if cart.created_by != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the person who created this cart can do that",
        )
    return cart


def ensure_cart_item_access(db: Session, cart_item_id: int, user: User) -> CartItem:
    """Resolve a cart item and confirm the caller belongs to its cart."""
    item = (
        db.query(CartItem).filter(CartItem.cart_item_id == cart_item_id).first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found"
        )
    ensure_cart_member(db, item.cart_id, user)
    return item
