from fastapi import FastAPI
from app.routers import search, home
from app.auth import auth_router
from app.wishlist import wishlist_router

app = FastAPI(title="Comparador de Precios de Videojuegos")
app.include_router(search.router)
app.include_router(auth_router)
app.include_router(wishlist_router)
app.include_router(home.router)