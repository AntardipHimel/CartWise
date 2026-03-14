from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import optimize, stores, products

app = FastAPI(
    title="CartWise API",
    description="Smart shopping optimizer - price intelligence + route optimization",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(optimize.router, prefix="/api", tags=["Optimize"])
app.include_router(stores.router, prefix="/api", tags=["Stores"])
app.include_router(products.router, prefix="/api", tags=["Products"])


@app.get("/")
def root():
    return {"message": "CartWise API is running", "docs": "/docs"}
