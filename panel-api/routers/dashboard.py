from fastapi import APIRouter, Depends

from shared import db
from auth import get_current_admin

router = APIRouter()


@router.get("")
async def get_dashboard(admin: dict = Depends(get_current_admin)):
    accounts = await db.get_account_stats()
    volume = await db.get_volume_stats()
    sales = await db.get_sales_stats()
    trend = await db.get_daily_sales_trend(7)
    agents_total = await db.count_all_agents()
    pending_agency_requests = await db.count_pending_agency_activation_requests()
    pending_wallet_topups = await db.count_pending_wallet_topup_requests()

    return {
        "accounts": {
            "total": accounts["total"],
            "active": accounts["active"],
            "inactive": accounts["inactive"],
        },
        "volume": {
            "total_allocated_gb": float(volume["total_allocated_gb"]),
            "total_used_gb": float(volume["total_used_gb"]),
        },
        "sales": {
            "total_sales": int(sales["total_sales"]),
            "today_sales": int(sales["today_sales"]),
            "week_sales": int(sales["week_sales"]),
            "month_sales": int(sales["month_sales"]),
        },
        "trend": [
            {"day": str(t["day"]), "total": int(t["total"]), "count": t["cnt"]}
            for t in trend
        ],
        "agents": {
            "total": agents_total,
            "pending_activation_requests": pending_agency_requests,
        },
        "pending_wallet_topups": pending_wallet_topups,
    }
