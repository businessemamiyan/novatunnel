from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shared import db
from auth import get_current_admin

router = APIRouter()


class ExpenseCreate(BaseModel):
    amount_toman: int
    description: str
    category: str | None = None


def _serialize_expense(e: dict):
    return {
        "id": str(e["id"]),
        "amount_toman": int(e["amount_toman"]),
        "description": e["description"],
        "category": e["category"],
        "created_at": e["created_at"].isoformat(),
    }


def _serialize_sales(row: dict):
    return {k: int(v) for k, v in row.items()}


@router.get("/sales-stats")
async def sales_stats(admin: dict = Depends(get_current_admin)):
    row = await db.get_sales_stats_by_scope(None)
    return _serialize_sales(dict(row))


@router.get("/other-revenue")
async def other_revenue(admin: dict = Depends(get_current_admin)):
    """پول واقعی دریافتی خارج از خرید بسته: هزینه فعال‌سازی/ارتقای نمایندگی و شارژ کیف‌پول."""
    activation = _serialize_sales(dict(await db.get_agency_activation_revenue_stats()))
    topup = _serialize_sales(dict(await db.get_wallet_topup_revenue_stats()))
    return {"agency_activation": activation, "wallet_topup": topup}


@router.get("/expenses")
async def list_expenses(admin: dict = Depends(get_current_admin)):
    rows = await db.get_expenses(None)
    return [_serialize_expense(dict(r)) for r in rows]


@router.post("/expenses")
async def add_expense(body: ExpenseCreate, admin: dict = Depends(get_current_admin)):
    if body.amount_toman <= 0:
        raise HTTPException(400, "مبلغ باید بزرگتر از صفر باشد")
    if not body.description.strip():
        raise HTTPException(400, "توضیح هزینه را وارد کنید")

    e = await db.create_expense(
        body.amount_toman, body.description.strip(), body.category, admin["telegram_id"], None
    )
    await db.log_admin_action(
        admin["telegram_id"], "expense_add", body.description.strip(), {"amount_toman": body.amount_toman}
    )
    return _serialize_expense(dict(e))


@router.delete("/expenses/{expense_id}")
async def remove_expense(expense_id: str, admin: dict = Depends(get_current_admin)):
    await db.delete_expense(expense_id, None)
    await db.log_admin_action(admin["telegram_id"], "expense_delete", f"expense {expense_id}")
    return {"ok": True}


@router.get("/summary")
async def summary(admin: dict = Depends(get_current_admin)):
    sales = await db.get_sales_stats_by_scope(None)
    activation = await db.get_agency_activation_revenue_stats()
    topup = await db.get_wallet_topup_revenue_stats()
    total_expenses = int(await db.get_expense_total(None))

    total_sales = int(sales["total_sales"])
    activation_total = int(activation["total"])
    topup_total = int(topup["total"])
    total_revenue = total_sales + activation_total + topup_total

    return {
        "total_sales": total_sales,
        "agency_activation_total": activation_total,
        "wallet_topup_total": topup_total,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": total_revenue - total_expenses,
    }
