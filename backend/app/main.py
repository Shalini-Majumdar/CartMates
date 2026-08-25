from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models.models import Base
from routers import auth, carts, products, messages, users

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shopping Cart API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],  # or explicitly ["POST", "GET", "OPTIONS"]
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(carts.router)
app.include_router(products.router)
app.include_router(messages.router)
app.include_router(users.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Shopping Cart API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}