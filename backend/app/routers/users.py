from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from crud.crud import get_all_users
from database import get_db
from models.models import User as UserModel
from schemas.schemas import User
from security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[User])
def list_users(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Directory used to pick people to share a cart with. Requires sign-in."""
    return get_all_users(db)
