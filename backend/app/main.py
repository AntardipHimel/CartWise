from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import close_db, connect_db
from app.routes import candidates, optimize, products, stores, users


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(title="CartWise API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(stores.router, prefix="/api", tags=["stores"])
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(candidates.router, prefix="/api", tags=["candidates"])
app.include_router(optimize.router, prefix="/api", tags=["optimize"])


@app.get("/")
async def root():
    return {"message": "CartWise backend is running"}