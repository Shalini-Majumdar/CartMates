"""Cart line items.

Listing lives under the cart it belongs to (`/carts/{cart_id}/items`), and
mutations address the line itself (`/cart-items/{cart_item_id}`), so a path
never means two different things depending on the verb.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.crud import (
    add_product_to_cart,
    approve_cart_item,
    calculate_cart_total,
    decrease_cart_item_quantity,
    disapprove_cart_item,
    get_cart_items,
    increase_cart_item_quantity,
)
from database import get_db
from models.models import User as UserModel
from schemas.schemas import CartItem, CartItemAdd
from security import ensure_cart_item_access, ensure_cart_member, get_current_user

# Listing is nested under the cart.
cart_items_router = APIRouter(prefix="/carts", tags=["cart items"])

# Mutations address a single line by its own id.
router = APIRouter(prefix="/cart-items", tags=["cart items"])


@cart_items_router.get("/{cart_id}/items", response_model=List[CartItem])
def list_cart_items(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    ensure_cart_member(db, cart_id, current_user)
    return get_cart_items(db, cart_id=cart_id)


@cart_items_router.post("/{cart_id}/items", response_model=CartItem, status_code=201)
def add_cart_item(
    cart_id: int,
    item: CartItemAdd,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Add a product from the shop page. Adding one already there tops it up."""
    ensure_cart_member(db, cart_id, current_user)
    cart_item = add_product_to_cart(
        db,
        cart_id=cart_id,
        product_id=item.product_id,
        quantity=item.quantity,
        user_id=current_user.user_id,
    )
    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return cart_item


@router.patch("/{cart_item_id}/increase")
def increase_quantity(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    ensure_cart_item_access(db, cart_item_id, current_user)
    cart_item = increase_cart_item_quantity(db, cart_item_id=cart_item_id)

    return {
        "message": "Quantity increased",
        "new_quantity": cart_item.quantity,
        "cart_total": str(calculate_cart_total(db, cart_item.cart_id)),
    }


@router.patch("/{cart_item_id}/decrease")
def decrease_quantity(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    ensure_cart_item_access(db, cart_item_id, current_user)
    cart_id, new_quantity = decrease_cart_item_quantity(db, cart_item_id=cart_item_id)

    total = str(calculate_cart_total(db, cart_id))
    if new_quantity is None:
        return {"message": "Item removed from cart", "cart_total": total}
    return {
        "message": "Quantity decreased",
        "new_quantity": new_quantity,
        "cart_total": total,
    }


@router.patch("/{cart_item_id}/approve")
def approve_item(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    ensure_cart_item_access(db, cart_item_id, current_user)
    cart_item = approve_cart_item(db, cart_item_id=cart_item_id)

    return {
        "message": "Item approved",
        "cart_total": str(calculate_cart_total(db, cart_item.cart_id)),
    }


@router.delete("/{cart_item_id}")
def remove_item(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Reject an item, which removes it from the cart."""
    ensure_cart_item_access(db, cart_item_id, current_user)
    cart_id = disapprove_cart_item(db, cart_item_id=cart_item_id)

    return {
        "message": "Item removed from cart",
        "cart_total": str(calculate_cart_total(db, cart_id)),
    }
