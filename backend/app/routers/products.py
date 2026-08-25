from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.schemas import CartItem
from crud.crud import (
    get_cart_products, 
    increase_cart_item_quantity, 
    decrease_cart_item_quantity,
    approve_cart_item,
    disapprove_cart_item,
    calculate_cart_total
)

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{cart_id}", response_model=List[CartItem])
def get_products_by_cart(cart_id: int, db: Session = Depends(get_db)):
    products = get_cart_products(db, cart_id=cart_id)
    return products


@router.patch("/{cart_item_id}/increase")
def increase_quantity(cart_item_id: int, db: Session = Depends(get_db)):
    cart_item = increase_cart_item_quantity(db, cart_item_id=cart_item_id)
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    total = calculate_cart_total(db, cart_item.cart_id)
    
    return {
        "message": "Quantity increased",
        "new_quantity": cart_item.quantity,
        "cart_total": str(total)
    }


@router.patch("/{cart_item_id}/decrease")
def decrease_quantity(cart_item_id: int, db: Session = Depends(get_db)):
    cart_item = decrease_cart_item_quantity(db, cart_item_id=cart_item_id)
    
    if cart_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    total = calculate_cart_total(db, cart_item.cart_id)
    
    if hasattr(cart_item, "quantity"):
        return {
            "message": "Quantity decreased",
            "new_quantity": cart_item.quantity,
            "cart_total": str(total)
        }
    else:
        return {
            "message": "Item removed from cart",
            "cart_total": str(total)
        }


@router.patch("/{cart_item_id}/approve")
def approve_item(cart_item_id: int, db: Session = Depends(get_db)):
    cart_item = approve_cart_item(db, cart_item_id=cart_item_id)
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    return {"message": "Item approved"}


@router.delete("/{cart_item_id}/disapprove")
def disapprove_item(cart_item_id: int, db: Session = Depends(get_db)):
    success = disapprove_cart_item(db, cart_item_id=cart_item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    return {"message": "Item disapproved and removed from cart"}