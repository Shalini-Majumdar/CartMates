from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.schemas import Cart, CartCreate, User
from crud.crud import get_user_carts_with_totals, calculate_cart_total, create_cart, delete_cart, get_cart_users

router = APIRouter(prefix="/carts", tags=["carts"])


@router.get("/{user_id}", response_model=List[Cart])
def get_carts(user_id: int, db: Session = Depends(get_db)):
    carts = get_user_carts_with_totals(db, user_id=user_id)
    return carts


@router.post("/{user_id}", response_model=Cart)
def create_new_cart(cart: CartCreate, user_id: int, db: Session = Depends(get_db)):
    new_cart = create_cart(db=db, cart=cart, user_id=user_id)
    new_cart.total = calculate_cart_total(db, new_cart.cart_id)
    return new_cart


@router.delete("/{cart_id}")
def delete_cart_by_id(cart_id: int, db: Session = Depends(get_db)):
    success = delete_cart(db, cart_id=cart_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found"
        )
    return {"message": "Cart deleted successfully"}


@router.get("/{cart_id}/users", response_model=List[User])
def get_users_by_cart(cart_id: int, db: Session = Depends(get_db)):
    users = get_cart_users(db, cart_id=cart_id)
    return users