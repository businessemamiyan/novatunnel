import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import config
from shared import db
from routers import auth, dashboard, customers


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield


app = FastAPI(lifespan=lifespan, title="NovaTunnel Panel API")

if config.CORS_ORIGINS:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def cache_control(request, call_next):
    """اگر فرانت ساخته‌شده (admin-panel/dist) از همین سرویس سرو شود، index.html هرگز نباید کش شود
    (همان الگوی admin_api/main.py برای جلوگیری از دیدن نسخه قدیمی)."""
    response = await call_next(request)
    if request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif not request.url.path.startswith("/api") and not request.url.path.startswith("/health"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])


@app.get("/health")
async def health():
    return {"ok": True}


# اگر admin-panel/dist ساخته شده باشد (کنار همین ریپو)، همین سرویس آن را هم سرو می‌کند —
# یعنی روی سرور ایران فقط یک پردازه (panel-api) لازم است، بدون نیاز به nginx جداگانه.
# اگر nginx/سرویس جدا ترجیح داده شود، فقط کافی است این mount حذف یا دایرکتوری وجود نداشته باشد.
_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "admin-panel", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="admin-panel")
