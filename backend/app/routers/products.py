"""Product catalogue for the shop page: browse, filter and sort."""

from decimal import Decimal
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from models.models import Product as ProductModel
from models.models import User as UserModel
from schemas.schemas import Product
from security import get_current_user

router = APIRouter(prefix="/products", tags=["products"])

MAX_PAGE_SIZE = 200


class ProductSort(str, Enum):
    price_asc = "price_asc"
    price_desc = "price_desc"
    name = "name"
    newest = "newest"


_ORDERING = {
    ProductSort.price_asc: (ProductModel.price.asc(), ProductModel.product_id),
    ProductSort.price_desc: (ProductModel.price.desc(), ProductModel.product_id),
    ProductSort.name: (func.lower(ProductModel.product_name), ProductModel.product_id),
    ProductSort.newest: (ProductModel.created_at.desc(), ProductModel.product_id.desc()),
}


@router.get("", response_model=List[Product])
def list_products(
    search: Optional[str] = Query(None, max_length=100),
    category: Optional[str] = Query(None, max_length=100),
    min_price: Optional[Decimal] = Query(None, ge=0),
    max_price: Optional[Decimal] = Query(None, ge=0),
    sort: ProductSort = ProductSort.name,
    limit: int = Query(MAX_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    query = db.query(ProductModel)

    if search and search.strip():
        pattern = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(ProductModel.product_name).like(pattern),
                func.lower(ProductModel.product_description).like(pattern),
                func.lower(ProductModel.category).like(pattern),
            )
        )
    if category:
        query = query.filter(ProductModel.category == category)
    if min_price is not None:
        query = query.filter(ProductModel.price >= min_price)
    if max_price is not None:
        query = query.filter(ProductModel.price <= max_price)

    return query.order_by(*_ORDERING[sort]).limit(limit).all()


@router.get("/categories", response_model=List[str])
def list_categories(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    rows = (
        db.query(ProductModel.category)
        .filter(ProductModel.category.isnot(None))
        .distinct()
        .order_by(ProductModel.category)
        .all()
    )
    return [row[0] for row in rows if row[0]]
