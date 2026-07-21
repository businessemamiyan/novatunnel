from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from shared import db
from routers import auth, dashboard, customers


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield


app = FastAPI(lifespan=lifespan, title="NovaTunnel Panel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])


@app.get("/health")
async def health():
    return {"ok": True}
