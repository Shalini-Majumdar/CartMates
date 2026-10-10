import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import auth, cart_items, carts, messages, products, users

logging.basicConfig(
    level=logging.DEBUG if settings.is_development else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# Schema is owned by Alembic (`alembic upgrade head`), not by create_all at
# import time: this database is shared, so changes need reviewable migrations.

app = FastAPI(title="Shopping Cart API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(carts.router)
app.include_router(cart_items.cart_items_router)
app.include_router(cart_items.router)
app.include_router(messages.router)
app.include_router(products.router)
app.include_router(users.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Shopping Cart API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
