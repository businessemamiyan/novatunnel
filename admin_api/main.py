import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from shared import db
from routers import (
    services, receipts, packages, broadcast, admins, stats, activity_log, me, customer, agency_config,
    support, wallet_topup, purchases, referral_config, users, payment_cards, agency, accounting,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield


app = FastAPI(lifespan=lifespan, title="NovaTunnel Admin API")


@app.middleware("http")
async def cache_control(request, call_next):
    """WebView تلگرام index.html را به‌شدت کش می‌کند و باعث دیدن نسخه قدیمی Mini App می‌شود؛
    فایل‌های hash-دار /assets/ برای همیشه قابل کش‌اند ولی index.html هرگز نباید کش شود."""
    response = await call_next(request)
    if request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif not request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


app.include_router(me.router, prefix="/api/me", tags=["me"])
app.include_router(customer.router, prefix="/api/my", tags=["customer"])
app.include_router(services.router, prefix="/api/services", tags=["services"])
app.include_router(receipts.router, prefix="/api/receipts", tags=["receipts"])
app.include_router(packages.router, prefix="/api/packages", tags=["packages"])
app.include_router(broadcast.router, prefix="/api/broadcast", tags=["broadcast"])
app.include_router(admins.router, prefix="/api/admins", tags=["admins"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(activity_log.router, prefix="/api/activity-log", tags=["activity-log"])
app.include_router(agency_config.router, prefix="/api/agency-config", tags=["agency-config"])
app.include_router(support.router, prefix="/api/support", tags=["support"])
app.include_router(wallet_topup.router, prefix="/api/wallet-topup", tags=["wallet-topup"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["purchases"])
app.include_router(referral_config.router, prefix="/api/referral-config", tags=["referral-config"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(payment_cards.router, prefix="/api/payment-cards", tags=["payment-cards"])
app.include_router(agency.router, prefix="/api/agency", tags=["agency"])
app.include_router(accounting.router, prefix="/api/accounting", tags=["accounting"])

_landing_dir = os.path.join(os.path.dirname(__file__), "landing_static")
if os.path.isdir(_landing_dir):
    app.mount("/landing", StaticFiles(directory=_landing_dir, html=True), name="landing")

_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
