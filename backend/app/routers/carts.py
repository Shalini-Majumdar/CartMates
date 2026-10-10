from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.crud import (
    calculate_cart_total,
    checkout_cart,
    create_cart,
    delete_cart,
    get_cart_users,
    get_user_carts_with_totals,
)
from database import get_db
from models.models import User as UserModel
from schemas.schemas import Cart, CartCreate, CheckoutReceipt, User
from security import ensure_cart_member, ensure_cart_owner, get_current_user

router = APIRouter(prefix="/carts", tags=["carts"])


@router.get("", response_model=List[Cart])
def get_carts(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """The signed-in user's carts. There is no way to ask for someone else's."""
    return get_user_carts_with_totals(db, user_id=current_user.user_id)


@router.post("", response_model=Cart, status_code=201)
def create_new_cart(
    cart: CartCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    new_cart = create_cart(db=db, cart=cart, user_id=current_user.user_id)
    new_cart.total = calculate_cart_total(db, new_cart.cart_id)
    new_cart.shared_usernames = [
        u.user_name for u in get_cart_users(db, new_cart.cart_id)
    ]
    return new_cart


@router.delete("/{cart_id}")
def delete_cart_by_id(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    # Only the creator may delete a cart others are sharing.
    ensure_cart_owner(db, cart_id, current_user)
    delete_cart(db, cart_id=cart_id)
    return {"message": "Cart deleted successfully"}


@router.get("/{cart_id}/users", response_model=List[User])
def get_users_by_cart(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    ensure_cart_member(db, cart_id, current_user)
    return get_cart_users(db, cart_id=cart_id)


@router.post("/{cart_id}/checkout", response_model=CheckoutReceipt)
def checkout(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Simulated checkout: buys the approved items and removes them from the cart.

    There is no payment gateway and no order history yet. Items still awaiting
    approval are left in the cart.
    """
    cart = ensure_cart_member(db, cart_id, current_user)
    cart_name = cart.cart_name
    lines, pending = checkout_cart(db, cart)
    if not lines:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There are no approved items in this cart to buy.",
        )

    placed_at = datetime.now(timezone.utc)
    return CheckoutReceipt(
        order_number=f"ORD-{placed_at:%Y%m%d}-{cart_id}{placed_at:%H%M%S}",
        cart_id=cart_id,
        cart_name=cart_name,
        placed_at=placed_at,
        items=lines,
        total=sum((line["line_total"] for line in lines), Decimal("0.00")),
        items_left_pending=pending,
    )
