from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import optimize, stores, products, candidates, users
from app.db import connect_db, close_db

app = FastAPI(
    title="CartWise API",
    description="Smart shopping optimizer - price intelligence + route optimization",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await connect_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


app.include_router(optimize.router, prefix="/api", tags=["Optimize"])
app.include_router(stores.router, prefix="/api", tags=["Stores"])
app.include_router(products.router, prefix="/api", tags=["Products"])
app.include_router(candidates.router, prefix="/api", tags=["Candidates"])
app.include_router(users.router, prefix="/api", tags=["Users"])


@app.get("/")
def root():
    return {"message": "CartWise API v2 is running", "docs": "/docs"}