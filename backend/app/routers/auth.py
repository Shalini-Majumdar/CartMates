from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.crud import create_user, get_user_by_email, verify_password
from database import get_db
from models.models import User as UserModel
from schemas.schemas import Token, User, UserCreate, UserLogin
from security import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    created = create_user(db=db, user=user)
    return Token(
        access_token=create_access_token(created.user_id),
        user=User.model_validate(created),
    )


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user_credentials.email)

    # Same message and roughly the same work either way, so the response does
    # not reveal whether an address is registered.
    if not db_user or not verify_password(user_credentials.passwd, db_user.passwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    return Token(
        access_token=create_access_token(db_user.user_id),
        user=User.model_validate(db_user),
    )


@router.get("/me", response_model=User)
def read_current_user(current_user: UserModel = Depends(get_current_user)):
    """Who the bearer token belongs to. Useful for validating a stored token."""
    return current_user
