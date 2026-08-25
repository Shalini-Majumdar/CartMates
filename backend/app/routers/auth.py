from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.schemas import UserCreate, UserLogin, User
from crud.crud import get_user_by_email, create_user, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=User)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return create_user(db=db, user=user)


@router.post("/login", response_model=User)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user_credentials.email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not verify_password(user_credentials.passwd, db_user.passwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    return db_user