from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.schemas import User
from crud.crud import get_all_users

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[User])
def get_carts(db: Session = Depends(get_db)):
    users = get_all_users(db)
    return users