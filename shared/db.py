import datetime
import json

import asyncpg

from . import config

_pool: asyncpg.Pool | None = None


async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(config.DATABASE_URL, min_size=1, max_size=5)
    return _pool


def pool() -> asyncpg.Pool:
    assert _pool is not None, "call init_pool() first"
    return _pool


async def get_user_by_telegram_id(telegram_id: int):
    return await pool().fetchrow(
        "select * from users where telegram_id = $1", telegram_id
    )


async def get_user_by_id(user_id):
    return await pool().fetchrow("select * from users where id = $1", user_id)


async def create_user(telegram_id: int, username: str | None, full_name: str | None,
                       referrer_telegram_id: int | None):
    referrer_id = None
    if referrer_telegram_id and referrer_telegram_id != telegram_id:
        referrer_row = await pool().fetchrow(
            "select id from users where telegram_id = $1", referrer_telegram_id
        )
        if referrer_row:
            referrer_id = referrer_row["id"]

    try:
        return await pool().fetchrow(
            """
            insert into users (telegram_id, telegram_username, full_name, referrer_id)
            values ($1, $2, $3, $4)
            returning *
            """,
            telegram_id, username, full_name, referrer_id,
        )
    except asyncpg.exceptions.RaiseError as e:
        # referrer already has max direct referrals (enforce_max_direct_referrals trigger) -> register without referrer
        if "زیرمجموعه مستقیم" in str(e):
            return await pool().fetchrow(
                """
                insert into users (telegram_id, telegram_username, full_name, referrer_id)
                values ($1, $2, $3, null)
                returning *
                """,
                telegram_id, username, full_name,
            )
        raise


async def mark_onboarding_seen(telegram_id: int):
    await pool().execute(
        "update users set onboarding_seen = true where telegram_id = $1", telegram_id
    )


async def touch_user(telegram_id: int, username: str | None, full_name: str | None):
    await pool().execute(
        """
        update users set telegram_username = $2, full_name = $3, updated_at = now()
        where telegram_id = $1
        """,
        telegram_id, username, full_name,
    )


async def verify_phone(telegram_id: int, phone_number: str):
    await pool().execute(
        """
        update users set phone_number = $2, phone_verified = true, phone_verified_at = now()
        where telegram_id = $1
        """,
        telegram_id, phone_number,
    )


async def get_active_packages():
    return await pool().fetch(
        "select * from packages where is_active order by volume_gb"
    )


async def can_purchase_key_panel(user_id, gift_balance_gb) -> bool:
    """پنل کلید فقط برای کاربرانی باز است که حجم هدیه دارند ولی سرویس فعالی ندارند —
    برای کاربران تازه‌وارد (بدون حجم هدیه) یا کسانی که از قبل سرویس فعال دارند قفل است."""
    if float(gift_balance_gb or 0) <= 0:
        return False
    panels = await get_panels_for_user(user_id)
    return len(panels) == 0


async def get_agent_pricing_for_customer(customer_user_id) -> dict:
    """اگر مشتری به‌طور دائمی به نماینده‌ای متصل باشد که قیمت‌گذاری سفارشی فعال دارد،
    دیکشنری package_id -> قیمت اختصاصی آن نماینده را برمی‌گرداند (بخش لینک اختصاصی نماینده)."""
    binding = await pool().fetchrow(
        "select agent_id from customer_agent_binding where customer_user_id = $1", customer_user_id
    )
    if binding is None:
        return {}
    agent = await pool().fetchrow(
        "select custom_pricing_enabled from agency_tiers where user_id = $1", binding["agent_id"]
    )
    if agent is None or not agent["custom_pricing_enabled"]:
        return {}
    rows = await pool().fetch(
        "select package_id, retail_price_toman from agent_plan_pricing where agent_id = $1", binding["agent_id"]
    )
    return {r["package_id"]: float(r["retail_price_toman"]) for r in rows}


def _apply_agent_pricing(packages, pricing: dict):
    if not pricing:
        return list(packages)
    result = []
    for p in packages:
        d = dict(p)
        if d["id"] in pricing:
            d["retail_price_toman"] = pricing[d["id"]]
        result.append(d)
    return result


async def get_purchasable_packages(user_id, gift_balance_gb):
    packages = await get_active_packages()
    if not await can_purchase_key_panel(user_id, gift_balance_gb):
        packages = [p for p in packages if not p["is_key_panel"]]

    trial_used = await pool().fetchval("select trial_used_at from users where id = $1", user_id)
    if trial_used is not None:
        packages = [p for p in packages if p["trial_hours"] is None]

    pricing = await get_agent_pricing_for_customer(user_id)
    return _apply_agent_pricing(packages, pricing)


async def get_packages_all():
    return await pool().fetch("select * from packages order by volume_gb")


async def get_package(package_id: int):
    return await pool().fetchrow("select * from packages where id = $1", package_id)


async def update_package_price(package_id: int, new_price_toman: int):
    return await pool().fetchrow(
        "update packages set retail_price_toman = $2 where id = $1 returning *",
        package_id, new_price_toman,
    )


async def update_package_badge(package_id: int, badge: str | None):
    return await pool().fetchrow(
        "update packages set badge = $2 where id = $1 returning *",
        package_id, badge,
    )


async def get_agency_tier_config():
    return await pool().fetch("select * from agency_tier_config order by activation_fee_toman")


async def update_agency_tier_config(
    tier: str, activation_fee_toman: int, purchase_rate_toman_per_gb: int, min_wallet_balance_toman: int
):
    return await pool().fetchrow(
        """
        update agency_tier_config
        set activation_fee_toman = $2, purchase_rate_toman_per_gb = $3,
            min_wallet_balance_toman = $4, updated_at = now()
        where tier = $1
        returning *
        """,
        tier, activation_fee_toman, purchase_rate_toman_per_gb, min_wallet_balance_toman,
    )


async def get_agency_tier_config_by_tier(tier: str):
    return await pool().fetchrow("select * from agency_tier_config where tier = $1", tier)


async def get_agent_info(user_id):
    return await pool().fetchrow("select * from agency_tiers where user_id = $1", user_id)


async def create_agency_activation_request(user_id, tier: str, activation_fee_toman, upline_agent_id, is_upgrade: bool):
    return await pool().fetchrow(
        """
        insert into agency_activation_requests
            (user_id, tier, activation_fee_toman, upline_agent_id, is_upgrade)
        values ($1, $2, $3, $4, $5)
        returning *
        """,
        user_id, tier, activation_fee_toman, upline_agent_id, is_upgrade,
    )


async def get_agency_activation_request(request_id):
    return await pool().fetchrow("select * from agency_activation_requests where id = $1", request_id)


async def get_agency_activation_requests(status: str | None = None, limit: int = 50, offset: int = 0):
    if status:
        return await pool().fetch(
            """
            select r.*, u.telegram_id, u.telegram_username, u.full_name
            from agency_activation_requests r join users u on u.id = r.user_id
            where r.status = $1 order by r.created_at desc limit $2 offset $3
            """,
            status, limit, offset,
        )
    return await pool().fetch(
        """
        select r.*, u.telegram_id, u.telegram_username, u.full_name
        from agency_activation_requests r join users u on u.id = r.user_id
        order by r.created_at desc limit $1 offset $2
        """,
        limit, offset,
    )


async def update_agency_activation_receipt(request_id, file_id: str):
    await pool().execute(
        "update agency_activation_requests set receipt_file_id = $2 where id = $1", request_id, file_id
    )


async def reject_agency_activation_request(request_id):
    return await pool().fetchrow(
        "update agency_activation_requests set status = 'rejected' where id = $1 and status = 'pending' returning *",
        request_id,
    )


async def confirm_agency_activation_request(request_id):
    """رده نمایندگی را فعال/ارتقا می‌دهد — نرخ/سقف رده در لحظه فعال‌سازی snapshot می‌شود (بخش ۶.۱).
    tier='vip' استثنا است: یک افزونه روی رده فعلی نماینده است، نه جایگزین آن (بخش ۱۴.۱ گزارش جلسه) —
    رده و نرخ خرید حجم معمولی دست‌نخورده می‌ماند، فقط vip_unlocked=true می‌شود."""
    async with pool().acquire() as conn:
        async with conn.transaction():
            req = await conn.fetchrow(
                "update agency_activation_requests set status = 'confirmed', confirmed_at = now() "
                "where id = $1 and status = 'pending' returning *",
                request_id,
            )
            if req is None:
                return None

            tier_cfg = await conn.fetchrow(
                "select * from agency_tier_config where tier = $1", req["tier"]
            )
            existing = await conn.fetchrow(
                "select * from agency_tiers where user_id = $1", req["user_id"]
            )

            if req["tier"] == "vip":
                if existing is None:
                    raise ValueError("ابتدا باید یکی از رده‌های نمایندگی را فعال کرده باشید")
                new_min_wallet = max(
                    float(existing["min_wallet_balance_toman"]), float(tier_cfg["min_wallet_balance_toman"])
                )
                agent = await conn.fetchrow(
                    """
                    update agency_tiers
                    set vip_unlocked = true, vip_activated_at = now(), min_wallet_balance_toman = $2
                    where user_id = $1
                    returning *
                    """,
                    req["user_id"], new_min_wallet,
                )
                return agent

            if existing:
                agent = await conn.fetchrow(
                    """
                    update agency_tiers
                    set tier = $2, activation_fee_paid_toman = $3, purchase_rate_toman_per_gb = $4,
                        min_wallet_balance_toman = $5, last_upgraded_at = now()
                    where user_id = $1
                    returning *
                    """,
                    req["user_id"], req["tier"], req["activation_fee_toman"],
                    tier_cfg["purchase_rate_toman_per_gb"], tier_cfg["min_wallet_balance_toman"],
                )
            else:
                agent = await conn.fetchrow(
                    """
                    insert into agency_tiers
                        (user_id, tier, upline_agent_id, activation_fee_paid_toman,
                         purchase_rate_toman_per_gb, min_wallet_balance_toman)
                    values ($1, $2, $3, $4, $5, $6)
                    returning *
                    """,
                    req["user_id"], req["tier"], req["upline_agent_id"], req["activation_fee_toman"],
                    tier_cfg["purchase_rate_toman_per_gb"], tier_cfg["min_wallet_balance_toman"],
                )
            return agent


async def get_agent_customers(agent_id, limit: int = 100):
    return await pool().fetch(
        """
        select pu.*, u.telegram_id, u.telegram_username, u.full_name
        from purchases pu join users u on u.id = pu.user_id
        where pu.seller_type = 'agent' and pu.seller_agent_id = $1
        order by pu.purchased_at desc limit $2
        """,
        agent_id, limit,
    )


async def get_agency_downline(agent_id):
    return await pool().fetch("select * from get_agency_downline_ids($1) order by level", agent_id)


async def get_agency_upline(agent_id):
    return await pool().fetch("select * from get_agency_upline_ids($1)", agent_id)


async def recompute_agent_panel_active(user_id):
    """بعد از هر تغییر موجودی کیف‌پول یک کاربر، اگر نماینده است، وضعیت فعال/غیرفعال پنلش را دوباره محاسبه می‌کند (بخش ۶.۳)."""
    agent = await pool().fetchrow("select * from agency_tiers where user_id = $1", user_id)
    if agent is None:
        return
    user = await pool().fetchrow("select wallet_balance_toman from users where id = $1", user_id)
    is_active = float(user["wallet_balance_toman"]) >= float(agent["min_wallet_balance_toman"])
    if is_active != agent["is_panel_active"]:
        await pool().execute(
            "update agency_tiers set is_panel_active = $2 where user_id = $1", user_id, is_active
        )


async def get_agency_chain_awarded_last_50_days(agent_id) -> float:
    row = await pool().fetchrow(
        """
        select coalesce(sum(amount_gb), 0) as total from gift_ledger
        where user_id = $1 and entry_type = 'credit_agency_chain'
          and created_at >= now() - interval '50 days'
        """,
        agent_id,
    )
    return float(row["total"])


async def apply_agency_chain_reward(conn, selling_agent_id, volume_gb: float):
    """۱٪ حجم فروش هر نماینده به همه بالادست‌های زنجیره‌اش تعلق می‌گیرد (بخش ۶.۵)، با سقف ۳۰۰ گیگ/۵۰ روز."""
    upline_rows = await conn.fetch("select * from get_agency_upline_ids($1)", selling_agent_id)
    reward_percent = await get_system_setting("agency_chain_reward_percent")
    results = []
    for row in upline_rows:
        upline_id = row["upline_agent_id"]
        gross = volume_gb * reward_percent / 100
        awarded = await get_agency_chain_awarded_last_50_days(upline_id)
        room = max(300 - awarded, 0)
        amount = min(gross, room)
        if amount <= 0:
            continue
        await credit_gift_volume(
            conn, upline_id, "credit_agency_chain", None, None, selling_agent_id, gross, amount,
            note=f"پاداش ۱٪ زنجیره نمایندگی از فروش نماینده {selling_agent_id}",
        )
        results.append((upline_id, amount))
    return results


async def apply_agency_chain_reward_standalone(agent_id, volume_gb: float):
    async with pool().acquire() as conn:
        async with conn.transaction():
            return await apply_agency_chain_reward(conn, agent_id, volume_gb)


async def create_agent_resale(agent_id, customer_user_id, volume_gb: float, price_toman: int,
                               is_gift_resale: bool, service_label: str | None, is_vip_service: bool = False):
    """نماینده مستقیماً به مشتری خودش می‌فروشد — هزینه از کیف‌پول نماینده (یا از حجم هدیه‌اش در حالت is_gift_resale) کسر می‌شود."""
    async with pool().acquire() as conn:
        async with conn.transaction():
            agent = await conn.fetchrow(
                "select * from agency_tiers where user_id = $1 for update", agent_id
            )
            if agent is None or not agent["is_panel_active"]:
                raise ValueError("پنل نمایندگی شما فعال نیست")
            if is_vip_service and not agent["vip_unlocked"]:
                raise ValueError("ابتدا باید سرویس ویژه را برای پنل نمایندگی خود فعال کنید")

            if is_gift_resale:
                gift_row = await conn.fetchrow(
                    "select gift_balance_gb from users where id = $1 for update", agent_id
                )
                if float(gift_row["gift_balance_gb"]) < volume_gb:
                    raise ValueError("حجم هدیه کافی برای این فروش ندارید")
                new_gift_balance = float(gift_row["gift_balance_gb"]) - volume_gb
                await conn.execute(
                    """
                    insert into gift_ledger (user_id, entry_type, amount_gb, balance_after_gb, note)
                    values ($1, 'debit_consumption', $2, $3, $4)
                    """,
                    agent_id, -volume_gb, new_gift_balance, f"فروش حجم هدیه به مشتری (رایگان برای نماینده)",
                )
            else:
                min_per_gb = await get_system_setting("min_resale_price_toman_per_gb")
                floor_price = volume_gb * min_per_gb
                if price_toman < floor_price:
                    raise ValueError(f"قیمت فروش نباید کمتر از {floor_price:,.0f} تومان ({min_per_gb:g}ت/گیگ) باشد")
                rate = float(agent["purchase_rate_toman_per_gb"])
                if is_vip_service:
                    vip_cfg = await conn.fetchrow("select * from agency_tier_config where tier = 'vip'")
                    rate = float(vip_cfg["purchase_rate_toman_per_gb"])
                cost = volume_gb * rate
                wallet_row = await conn.fetchrow(
                    "select wallet_balance_toman from users where id = $1 for update", agent_id
                )
                if float(wallet_row["wallet_balance_toman"]) < cost:
                    raise ValueError(f"موجودی کیف‌پول شما برای خرید این حجم ({cost:,.0f} تومان) کافی نیست")
                new_balance = float(wallet_row["wallet_balance_toman"]) - cost
                await conn.execute(
                    """
                    insert into wallet_transactions (user_id, type, amount_toman, balance_after_toman, note)
                    values ($1, 'agency_resale_cost', $2, $3, $4)
                    """,
                    agent_id, -cost, new_balance, f"هزینه فروش {volume_gb:g} گیگ به مشتری",
                )

            purchase = await conn.fetchrow(
                """
                insert into purchases
                    (user_id, package_id, volume_gb, price_toman, payment_method, payment_status,
                     seller_type, seller_agent_id, is_gift_resale, service_label, is_vip_service, confirmed_at)
                values ($1, null, $2, $3, 'card_to_card', 'confirmed', 'agent', $4, $5, $6, $7, now())
                returning *
                """,
                customer_user_id, volume_gb, price_toman, agent_id, is_gift_resale, service_label, is_vip_service,
            )

            await apply_agency_chain_reward(conn, agent_id, volume_gb)

    await recompute_agent_panel_active(agent_id)
    return purchase


async def create_test_grant_purchase(user_id, volume_gb: float, service_label: str | None, is_vip_service: bool = False):
    """اعطای دستی سرویس تست/رایگان توسط ادمین — is_test=true یعنی در آمار فروش/حسابداری لحاظ نمی‌شود."""
    return await pool().fetchrow(
        """
        insert into purchases
            (user_id, package_id, volume_gb, price_toman, payment_method, payment_status,
             seller_type, service_label, is_vip_service, is_test, confirmed_at)
        values ($1, null, $2, 0, 'card_to_card', 'confirmed', 'owner', $3, $4, true, now())
        returning *
        """,
        user_id, volume_gb, service_label, is_vip_service,
    )


async def find_discount_code(code: str):
    return await pool().fetchrow(
        "select * from discount_codes where code = $1 and is_active", code.strip().upper()
    )


async def user_used_discount_code(code_id, user_id) -> bool:
    row = await pool().fetchrow(
        "select 1 from discount_code_redemptions where code_id = $1 and user_id = $2",
        code_id, user_id,
    )
    return row is not None


def compute_discount_amount(discount_row, price_toman: int) -> int:
    if discount_row["discount_type"] == "percent":
        amount = price_toman * float(discount_row["discount_value"]) / 100
    else:
        amount = float(discount_row["discount_value"])
    return min(int(amount), price_toman)


async def create_pending_purchase(user_id, package_id, volume_gb, price_toman,
                                   discount_code_id=None, discount_amount_toman=0,
                                   payment_method="card_to_card", service_label=None,
                                   renewed_panel_id=None, wallet_credit_used_toman=0,
                                   reward_credit_used_toman=0, seller_agent_id=None):
    seller_type = "agent" if seller_agent_id else "owner"
    return await pool().fetchrow(
        """
        insert into purchases
            (user_id, package_id, volume_gb, price_toman, payment_method,
             payment_status, discount_code_id, discount_amount_toman,
             service_label, renewed_panel_id, wallet_credit_used_toman, reward_credit_used_toman,
             seller_type, seller_agent_id)
        values ($1, $2, $3, $4, $5, 'pending', $6, $7, $8, $9, $10, $11, $12, $13)
        returning *
        """,
        user_id, package_id, volume_gb, price_toman, payment_method,
        discount_code_id, discount_amount_toman, service_label, renewed_panel_id,
        wallet_credit_used_toman, reward_credit_used_toman, seller_type, seller_agent_id,
    )


async def get_customer_agent_binding(customer_user_id):
    return await pool().fetchrow(
        "select * from customer_agent_binding where customer_user_id = $1", customer_user_id
    )


async def bind_customer_to_agent(customer_user_id, agent_id):
    """اتصال دائمی مشتری به نماینده — idempotent، اگه قبلاً متصل بوده تغییری نمی‌کند (بخش لینک اختصاصی نماینده)."""
    await pool().execute(
        """
        insert into customer_agent_binding (customer_user_id, agent_id)
        values ($1, $2)
        on conflict (customer_user_id) do nothing
        """,
        customer_user_id, agent_id,
    )


async def get_agent_by_slug(slug: str):
    return await pool().fetchrow("select * from agency_tiers where agent_slug = $1", slug)


async def set_agent_slug(agent_id, slug: str):
    return await pool().fetchrow(
        "update agency_tiers set agent_slug = $2 where user_id = $1 returning *", agent_id, slug
    )


async def get_agent_plan_pricing(agent_id):
    return await pool().fetch(
        """
        select pkg.id as package_id, pkg.name, pkg.volume_gb, pkg.retail_price_toman as default_price_toman,
               app.retail_price_toman as agent_price_toman
        from packages pkg
        left join agent_plan_pricing app on app.package_id = pkg.id and app.agent_id = $1
        where pkg.is_active and not pkg.is_key_panel
        order by pkg.volume_gb
        """,
        agent_id,
    )


async def set_agent_plan_price(agent_id, package_id: int, price_toman: int):
    agent = await get_agent_info(agent_id)
    if agent is None or not agent["custom_pricing_enabled"]:
        raise ValueError("قیمت‌گذاری اختصاصی برای شما فعال نیست")

    package = await get_package(package_id)
    if package is None:
        raise ValueError("بسته پیدا نشد")

    # سقف فروش نماینده «آزاد» است (بخش ۷ سند قوانین) — فقط کف مطلق ۴۰۰۰ تومان/گیگ اعمال می‌شود،
    # نه یک سقف نسبی به هزینه خرید (آن نسخه قبلی برای رده‌های ارزان‌تر مثل برلیان محدوده غیرممکن می‌ساخت).
    wholesale_cost = float(package["volume_gb"]) * float(agent["purchase_rate_toman_per_gb"])
    floor_per_gb = await get_system_setting("min_resale_price_toman_per_gb")
    min_price = max(wholesale_cost, float(package["volume_gb"]) * floor_per_gb)

    if price_toman < min_price:
        raise ValueError(f"قیمت نباید کمتر از {min_price:,.0f} تومان (کف مجاز فروش) باشد")

    return await pool().fetchrow(
        """
        insert into agent_plan_pricing (agent_id, package_id, retail_price_toman)
        values ($1, $2, $3)
        on conflict (agent_id, package_id)
        do update set retail_price_toman = $3, updated_at = now()
        returning *
        """,
        agent_id, package_id, price_toman,
    )


async def set_purchase_gateway_authority(purchase_id, authority: str):
    await pool().execute(
        "update purchases set gateway_authority = $2, payment_method = 'zarinpal' where id = $1",
        purchase_id, authority,
    )


async def get_purchase_by_authority(authority: str):
    return await pool().fetchrow("select * from purchases where gateway_authority = $1", authority)


async def get_all_payment_cards(agent_id=None):
    """agent_id=None → کارت‌های مالک/ادمین؛ مقداردار → فقط کارت‌های همان نماینده."""
    return await pool().fetch(
        "select * from payment_cards where agent_id is not distinct from $1 order by id", agent_id
    )


async def create_payment_card(card_number: str, card_holder: str, agent_id=None):
    return await pool().fetchrow(
        "insert into payment_cards (card_number, card_holder, agent_id) values ($1, $2, $3) returning *",
        card_number, card_holder, agent_id,
    )


async def update_payment_card(card_id: int, card_number: str, card_holder: str, is_active: bool, agent_id=None):
    return await pool().fetchrow(
        """
        update payment_cards set card_number = $2, card_holder = $3, is_active = $4
        where id = $1 and agent_id is not distinct from $5
        returning *
        """,
        card_id, card_number, card_holder, is_active, agent_id,
    )


async def delete_payment_card(card_id: int, agent_id=None):
    await pool().execute(
        "delete from payment_cards where id = $1 and agent_id is not distinct from $2", card_id, agent_id
    )


async def get_random_payment_card(agent_id=None):
    return await pool().fetchrow(
        "select * from payment_cards where is_active and agent_id is not distinct from $1 order by random() limit 1",
        agent_id,
    )


async def create_wallet_topup_request(user_id, amount_toman):
    return await pool().fetchrow(
        "insert into wallet_topup_requests (user_id, amount_toman) values ($1, $2) returning *",
        user_id, amount_toman,
    )


async def get_wallet_topup(topup_id):
    return await pool().fetchrow("select * from wallet_topup_requests where id = $1", topup_id)


async def update_wallet_topup_receipt_file_id(topup_id, file_id: str):
    await pool().execute(
        "update wallet_topup_requests set receipt_file_id = $2 where id = $1", topup_id, file_id
    )


async def set_wallet_topup_gateway_authority(topup_id, authority: str):
    await pool().execute(
        "update wallet_topup_requests set gateway_authority = $2, payment_method = 'zarinpal' where id = $1",
        topup_id, authority,
    )


async def get_wallet_topup_by_authority(authority: str):
    return await pool().fetchrow("select * from wallet_topup_requests where gateway_authority = $1", authority)


async def get_wallet_topup_requests(status: str | None = None, limit: int = 50, offset: int = 0):
    if status:
        return await pool().fetch(
            """
            select t.*, u.telegram_id, u.telegram_username, u.full_name
            from wallet_topup_requests t join users u on u.id = t.user_id
            where t.status = $1 order by t.created_at desc limit $2 offset $3
            """,
            status, limit, offset,
        )
    return await pool().fetch(
        """
        select t.*, u.telegram_id, u.telegram_username, u.full_name
        from wallet_topup_requests t join users u on u.id = t.user_id
        order by t.created_at desc limit $1 offset $2
        """,
        limit, offset,
    )


async def get_wallet_topup_requests_for_user(user_id, limit: int = 20):
    return await pool().fetch(
        "select * from wallet_topup_requests where user_id = $1 order by created_at desc limit $2",
        user_id, limit,
    )


async def confirm_wallet_topup(topup_id):
    topup = await pool().fetchrow(
        "update wallet_topup_requests set status = 'confirmed', confirmed_at = now() "
        "where id = $1 and status = 'pending' returning *",
        topup_id,
    )
    if topup is None:
        return None
    await credit_wallet(
        topup["user_id"], "topup", topup["amount_toman"],
        note="شارژ کیف‌پول (کارت‌به‌کارت)",
    )
    return topup


async def reject_wallet_topup(topup_id):
    return await pool().fetchrow(
        "update wallet_topup_requests set status = 'rejected' where id = $1 and status = 'pending' returning *",
        topup_id,
    )


async def update_purchase_receipt_file_id(purchase_id, file_id: str):
    await pool().execute(
        "update purchases set receipt_file_id = $2 where id = $1", purchase_id, file_id
    )


async def get_receipts(status: str | None = None, limit: int = 50, offset: int = 0):
    return await pool().fetch(
        """
        select pu.*, u.telegram_id, u.telegram_username, u.full_name,
               pkg.name as package_name
        from purchases pu
        join users u on u.id = pu.user_id
        left join packages pkg on pkg.id = pu.package_id
        where pu.payment_method = 'card_to_card'
          and ($1::text is null or pu.payment_status = $1)
        order by pu.purchased_at desc
        limit $2 offset $3
        """,
        status, limit, offset,
    )


async def get_all_panels(status: str | None = None, search: str | None = None,
                          limit: int = 50, offset: int = 0):
    return await pool().fetch(
        """
        select p.*, u.telegram_id, u.telegram_username, u.full_name
        from panels p
        join users u on u.id = p.user_id
        where (
            $1::text is null
            or ($1 = 'active' and p.is_active and (p.expires_at is null or p.expires_at > now()))
            or ($1 = 'inactive' and not (p.is_active and (p.expires_at is null or p.expires_at > now())))
        )
        and (
            $2::text is null
            or p.label ilike '%' || $2 || '%'
            or p.marzban_username ilike '%' || $2 || '%'
            or u.telegram_username ilike '%' || $2 || '%'
        )
        order by p.created_at desc
        limit $3 offset $4
        """,
        status, search, limit, offset,
    )


async def get_panels_for_user(user_id, active_only=True):
    if active_only:
        return await pool().fetch(
            "select * from panels where user_id = $1 and is_active order by created_at desc",
            user_id,
        )
    return await pool().fetch(
        "select * from panels where user_id = $1 order by created_at desc", user_id
    )


async def get_panel(panel_id):
    return await pool().fetchrow("select * from panels where id = $1", panel_id)


async def create_panel(user_id, purchase_id, marzban_username, label, traffic_limit_gb, expires_at,
                        auto_delete_at=None):
    return await pool().fetchrow(
        """
        insert into panels
            (user_id, purchase_id, marzban_username, label, protocol,
             traffic_limit_gb, expires_at, auto_delete_at)
        values ($1, $2, $3, $4, 'vless-reality', $5, $6, $7)
        returning *
        """,
        user_id, purchase_id, marzban_username, label, traffic_limit_gb, expires_at, auto_delete_at,
    )


async def mark_trial_used(user_id):
    await pool().execute("update users set trial_used_at = now() where id = $1", user_id)


async def get_expired_trial_panels():
    return await pool().fetch(
        "select * from panels where is_active and auto_delete_at is not null and auto_delete_at < now()"
    )


async def renew_panel(panel_id, add_traffic_gb, new_expires_at):
    await pool().execute(
        """
        update panels
        set traffic_limit_gb = traffic_limit_gb + $2,
            expires_at = $3,
            is_active = true,
            updated_at = now()
        where id = $1
        """,
        panel_id, add_traffic_gb, new_expires_at,
    )


async def deactivate_panel(panel_id):
    await pool().execute(
        "update panels set is_active = false, updated_at = now() where id = $1", panel_id
    )


async def is_admin(telegram_id: int) -> bool:
    row = await pool().fetchrow(
        "select 1 from bot_admins where telegram_id = $1 and is_active", telegram_id
    )
    return row is not None


async def add_admin(telegram_id: int, added_by: int):
    await pool().execute(
        """
        insert into bot_admins (telegram_id, added_by)
        values ($1, $2)
        on conflict (telegram_id) do update set is_active = true, added_by = excluded.added_by
        """,
        telegram_id, added_by,
    )


async def remove_admin(telegram_id: int):
    await pool().execute(
        "update bot_admins set is_active = false where telegram_id = $1", telegram_id
    )


async def count_active_admins() -> int:
    row = await pool().fetchrow("select count(*) as c from bot_admins where is_active")
    return row["c"]


async def list_admins():
    return await pool().fetch("select * from bot_admins where is_active order by added_at")


async def get_direct_referrals(user_id):
    return await pool().fetch(
        "select id, full_name, telegram_username, phone_verified, referrer_id "
        "from users where referrer_id = $1",
        user_id,
    )


async def get_referrals_for_users(user_ids: list):
    if not user_ids:
        return []
    return await pool().fetch(
        "select id, full_name, telegram_username, phone_verified, referrer_id "
        "from users where referrer_id = any($1::uuid[])",
        user_ids,
    )


async def get_all_active_admin_ids():
    rows = await pool().fetch("select telegram_id from bot_admins where is_active")
    return [r["telegram_id"] for r in rows]


async def get_all_user_telegram_ids():
    rows = await pool().fetch("select telegram_id from users")
    return [r["telegram_id"] for r in rows]


async def log_social_conversation(platform: str, external_user_id: str, external_username: str | None,
                                   incoming_message: str, action: str, reply_text: str | None = None,
                                   escalation_reason: str | None = None):
    await pool().execute(
        """
        insert into social_conversation_log
            (platform, external_user_id, external_username, incoming_message,
             action, reply_text, escalation_reason)
        values ($1, $2, $3, $4, $5, $6, $7)
        """,
        platform, external_user_id, external_username, incoming_message,
        action, reply_text, escalation_reason,
    )


async def get_recent_social_conversation(platform: str, external_user_id: str, limit: int = 15):
    """آخرین پیام‌های رد و بدل شده (به ترتیب زمانی) را برای ساخت context چندنوبتی برای مدل برمی‌گرداند."""
    rows = await pool().fetch(
        """
        select incoming_message, action, reply_text, escalation_reason, created_at
        from social_conversation_log
        where platform = $1 and external_user_id = $2
        order by created_at desc limit $3
        """,
        platform, external_user_id, limit,
    )
    return list(reversed(rows))


async def is_instagram_item_handled(item_id: str) -> bool:
    row = await pool().fetchrow(
        "select 1 from instagram_handled_items where item_id = $1", item_id
    )
    return row is not None


async def mark_instagram_item_handled(item_id: str, item_type: str):
    await pool().execute(
        """
        insert into instagram_handled_items (item_id, item_type)
        values ($1, $2)
        on conflict (item_id) do nothing
        """,
        item_id, item_type,
    )


async def create_generated_post(platform: str, content: str, image_url: str | None = None, topic: str | None = None):
    return await pool().fetchrow(
        """
        insert into generated_posts (platform, content, image_url, topic)
        values ($1, $2, $3, $4)
        returning *
        """,
        platform, content, image_url, topic,
    )


async def get_recent_post_topics(platform: str, limit: int = 5) -> list[str]:
    rows = await pool().fetch(
        """
        select topic from generated_posts
        where platform = $1 and topic is not null
        order by created_at desc limit $2
        """,
        platform, limit,
    )
    return [r["topic"] for r in rows]


async def mark_post_result(post_id, status: str, external_post_id: str | None = None,
                            error_message: str | None = None):
    await pool().execute(
        """
        update generated_posts
        set status = $2, external_post_id = $3, error_message = $4,
            posted_at = case when $2 = 'posted' then now() else posted_at end
        where id = $1
        """,
        post_id, status, external_post_id, error_message,
    )


async def log_admin_action(admin_telegram_id: int, action_type: str,
                            target_description: str | None = None, metadata: dict | None = None):
    await pool().execute(
        """
        insert into admin_activity_log (admin_telegram_id, action_type, target_description, metadata)
        values ($1, $2, $3, $4::jsonb)
        """,
        admin_telegram_id, action_type, target_description,
        json.dumps(metadata) if metadata is not None else None,
    )


async def get_activity_log(limit: int = 50, offset: int = 0):
    return await pool().fetch(
        "select * from admin_activity_log order by created_at desc limit $1 offset $2",
        limit, offset,
    )


async def get_account_stats():
    return await pool().fetchrow(
        """
        select
          count(*) as total,
          count(*) filter (where is_active and (expires_at is null or expires_at > now())) as active,
          count(*) filter (where not (is_active and (expires_at is null or expires_at > now()))) as inactive
        from panels
        """
    )


async def get_volume_stats():
    return await pool().fetchrow(
        """
        select
          coalesce(sum(traffic_limit_gb), 0) as total_allocated_gb,
          coalesce(sum(traffic_used_gb), 0) as total_used_gb
        from panels
        """
    )


async def get_sales_stats():
    return await pool().fetchrow(
        """
        select
          coalesce(sum(price_toman) filter (where payment_status = 'confirmed'), 0) as total_sales,
          coalesce(sum(price_toman) filter (
            where payment_status = 'confirmed'
              and (confirmed_at at time zone 'Asia/Tehran')::date = (now() at time zone 'Asia/Tehran')::date
          ), 0) as today_sales,
          coalesce(sum(price_toman) filter (
            where payment_status = 'confirmed'
              and confirmed_at >= now() - interval '7 days'
          ), 0) as week_sales,
          coalesce(sum(price_toman) filter (
            where payment_status = 'confirmed'
              and (confirmed_at at time zone 'Asia/Tehran') >= date_trunc('month', now() at time zone 'Asia/Tehran')
          ), 0) as month_sales
        from purchases
        """
    )


async def get_daily_sales_trend(days: int = 7):
    return await pool().fetch(
        """
        select
          (confirmed_at at time zone 'Asia/Tehran')::date as day,
          coalesce(sum(price_toman), 0) as total,
          count(*) as cnt
        from purchases
        where payment_status = 'confirmed'
          and confirmed_at >= now() - make_interval(days => $1)
        group by 1
        order by 1
        """,
        days,
    )


async def get_sales_stats_by_scope(seller_agent_id=None):
    """seller_agent_id=None → کل فروش کسب‌وکار (پنل حسابداری ادمین)؛ مقداردار → فقط فروش‌های همان نماینده."""
    return await pool().fetchrow(
        """
        select
          count(*) filter (where payment_status = 'confirmed') as total_count,
          coalesce(sum(price_toman) filter (where payment_status = 'confirmed'), 0) as total_sales,
          count(*) filter (
            where payment_status = 'confirmed'
              and (confirmed_at at time zone 'Asia/Tehran')::date = (now() at time zone 'Asia/Tehran')::date
          ) as today_count,
          coalesce(sum(price_toman) filter (
            where payment_status = 'confirmed'
              and (confirmed_at at time zone 'Asia/Tehran')::date = (now() at time zone 'Asia/Tehran')::date
          ), 0) as today_sales,
          count(*) filter (
            where payment_status = 'confirmed' and confirmed_at >= now() - interval '7 days'
          ) as week_count,
          coalesce(sum(price_toman) filter (
            where payment_status = 'confirmed' and confirmed_at >= now() - interval '7 days'
          ), 0) as week_sales,
          count(*) filter (
            where payment_status = 'confirmed'
              and (confirmed_at at time zone 'Asia/Tehran') >= date_trunc('month', now() at time zone 'Asia/Tehran')
          ) as month_count,
          coalesce(sum(price_toman) filter (
            where payment_status = 'confirmed'
              and (confirmed_at at time zone 'Asia/Tehran') >= date_trunc('month', now() at time zone 'Asia/Tehran')
          ), 0) as month_sales
        from purchases
        where ($1::uuid is null or seller_agent_id = $1) and not is_test
        """,
        seller_agent_id,
    )


async def get_wallet_cost_stats(user_id, tx_type: str):
    """جمع هزینه‌ی خرید (برداشت از کیف‌پول) یک کاربر برای یک نوع تراکنش مشخص — برای حسابداری نماینده (بخش خرید)."""
    return await pool().fetchrow(
        """
        select
          coalesce(sum(-amount_toman), 0) as total_cost,
          coalesce(sum(-amount_toman) filter (
            where (created_at at time zone 'Asia/Tehran')::date = (now() at time zone 'Asia/Tehran')::date
          ), 0) as today_cost,
          coalesce(sum(-amount_toman) filter (where created_at >= now() - interval '7 days'), 0) as week_cost,
          coalesce(sum(-amount_toman) filter (
            where (created_at at time zone 'Asia/Tehran') >= date_trunc('month', now() at time zone 'Asia/Tehran')
          ), 0) as month_cost
        from wallet_transactions
        where user_id = $1 and type = $2::wallet_tx_type
        """,
        user_id, tx_type,
    )


async def get_agency_activation_revenue_stats():
    """پول واقعی دریافتی بابت فعال‌سازی/ارتقای نمایندگی — طبق بخش ۶.۲ به کیف‌پول واریز نمی‌شود،
    پس فقط از همین جدول قابل ردیابی است؛ بدون این، در حسابداری ادمین اصلاً دیده نمی‌شد."""
    return await pool().fetchrow(
        """
        select
          coalesce(sum(activation_fee_toman), 0) as total,
          coalesce(sum(activation_fee_toman) filter (
            where (confirmed_at at time zone 'Asia/Tehran')::date = (now() at time zone 'Asia/Tehran')::date
          ), 0) as today,
          coalesce(sum(activation_fee_toman) filter (where confirmed_at >= now() - interval '7 days'), 0) as week,
          coalesce(sum(activation_fee_toman) filter (
            where (confirmed_at at time zone 'Asia/Tehran') >= date_trunc('month', now() at time zone 'Asia/Tehran')
          ), 0) as month
        from agency_activation_requests
        where status = 'confirmed'
        """
    )


async def get_wallet_topup_revenue_stats():
    """پول واقعی دریافتی بابت شارژ کیف‌پول (کارت‌به‌کارت/آنلاین) — قبلاً در هیچ‌کجای حسابداری ادمین لحاظ نمی‌شد."""
    return await pool().fetchrow(
        """
        select
          coalesce(sum(amount_toman), 0) as total,
          coalesce(sum(amount_toman) filter (
            where (confirmed_at at time zone 'Asia/Tehran')::date = (now() at time zone 'Asia/Tehran')::date
          ), 0) as today,
          coalesce(sum(amount_toman) filter (where confirmed_at >= now() - interval '7 days'), 0) as week,
          coalesce(sum(amount_toman) filter (
            where (confirmed_at at time zone 'Asia/Tehran') >= date_trunc('month', now() at time zone 'Asia/Tehran')
          ), 0) as month
        from wallet_topup_requests
        where status = 'confirmed'
        """
    )


async def create_expense(amount_toman, description: str, category: str | None,
                          created_by_telegram_id: int, agent_id=None):
    return await pool().fetchrow(
        """
        insert into expenses (agent_id, amount_toman, description, category, created_by_telegram_id)
        values ($1, $2, $3, $4, $5)
        returning *
        """,
        agent_id, amount_toman, description, category, created_by_telegram_id,
    )


async def get_expenses(agent_id=None, limit: int = 100, offset: int = 0):
    return await pool().fetch(
        """
        select * from expenses
        where agent_id is not distinct from $1
        order by created_at desc limit $2 offset $3
        """,
        agent_id, limit, offset,
    )


async def get_expense_total(agent_id=None):
    row = await pool().fetchrow(
        "select coalesce(sum(amount_toman), 0) as total from expenses where agent_id is not distinct from $1",
        agent_id,
    )
    return row["total"]


async def delete_expense(expense_id, agent_id=None):
    await pool().execute(
        "delete from expenses where id = $1 and agent_id is not distinct from $2",
        expense_id, agent_id,
    )


async def get_all_active_panels_for_sync():
    return await pool().fetch("select id, marzban_username from panels where is_active")


async def update_panel_usage(panel_id, used_gb: float):
    await pool().execute(
        "update panels set traffic_used_gb = $2 where id = $1", panel_id, used_gb
    )


async def get_panels_needing_expiry_warning():
    return await pool().fetch(
        """
        select p.*, u.telegram_id
        from panels p
        join users u on u.id = p.user_id
        where p.is_active
          and p.expiry_warned_at is null
          and p.expires_at is not null
          and p.expires_at <= now() + interval '24 hours'
          and p.expires_at > now()
        """
    )


async def mark_expiry_warned(panel_id):
    await pool().execute(
        "update panels set expiry_warned_at = now() where id = $1", panel_id
    )


async def get_purchases_for_user(user_id, limit=20):
    return await pool().fetch(
        """
        select p.*, pkg.name as package_name
        from purchases p
        left join packages pkg on pkg.id = p.package_id
        where p.user_id = $1
        order by p.purchased_at desc
        limit $2
        """,
        user_id, limit,
    )


async def get_purchase(purchase_id):
    return await pool().fetchrow("select * from purchases where id = $1", purchase_id)


async def confirm_purchase(purchase_id):
    async with pool().acquire() as conn:
        async with conn.transaction():
            purchase = await conn.fetchrow(
                """
                update purchases
                set payment_status = 'confirmed', confirmed_at = now()
                where id = $1 and payment_status = 'pending'
                returning *
                """,
                purchase_id,
            )
            if purchase is None:
                return None
            if purchase["discount_code_id"]:
                await conn.execute(
                    """
                    insert into discount_code_redemptions
                        (code_id, user_id, purchase_id, discount_amount_toman)
                    values ($1, $2, $3, $4)
                    on conflict (code_id, user_id) do nothing
                    """,
                    purchase["discount_code_id"], purchase["user_id"], purchase["id"],
                    purchase["discount_amount_toman"],
                )
            return purchase


async def reject_purchase(purchase_id):
    return await pool().fetchrow(
        """
        update purchases set payment_status = 'failed'
        where id = $1 and payment_status = 'pending'
        returning *
        """,
        purchase_id,
    )


async def get_referral_ancestors(user_id):
    return await pool().fetch(
        "select * from get_referral_ancestors($1)", user_id
    )


async def get_all_users_admin(search: str | None = None, limit: int = 50, offset: int = 0):
    if search:
        pattern = f"%{search}%"
        return await pool().fetch(
            """
            select * from users
            where telegram_username ilike $1 or full_name ilike $1 or phone_number ilike $1
               or telegram_id::text ilike $1
            order by created_at desc limit $2 offset $3
            """,
            pattern, limit, offset,
        )
    return await pool().fetch("select * from users order by created_at desc limit $1 offset $2", limit, offset)


async def count_all_users(search: str | None = None) -> int:
    if search:
        pattern = f"%{search}%"
        row = await pool().fetchrow(
            """
            select count(*) as c from users
            where telegram_username ilike $1 or full_name ilike $1 or phone_number ilike $1
               or telegram_id::text ilike $1
            """,
            pattern,
        )
    else:
        row = await pool().fetchrow("select count(*) as c from users")
    return row["c"]


async def get_all_users_for_export():
    return await pool().fetch("select * from users order by created_at desc")


async def get_referral_level_config() -> dict:
    """همیشه fresh می‌خواند (بدون کش) — چون ربات/پنل ادمین/اتوماسیون پردازه‌های جدا هستند
    و کش داخل‌پردازه‌ای باعث می‌شد تغییر ادمین در یک سرویس، تا ری‌استارت در بقیه اعمال نشود."""
    rows = await pool().fetch("select * from referral_level_config")
    return {
        r["level"]: {
            "reward_percent": float(r["reward_percent"]),
            "monthly_cap_gb": float(r["monthly_cap_gb"]),
        }
        for r in rows
    }


async def get_referral_level_config_list():
    return await pool().fetch("select * from referral_level_config order by level")


async def update_referral_level_config(level: int, max_direct_children: int, reward_percent, monthly_cap_gb):
    return await pool().fetchrow(
        """
        update referral_level_config
        set max_direct_children = $2, reward_percent = $3, monthly_cap_gb = $4
        where level = $1
        returning *
        """,
        level, max_direct_children, reward_percent, monthly_cap_gb,
    )


async def get_system_setting(key: str) -> float:
    row = await pool().fetchrow("select value from system_settings where key = $1", key)
    return float(row["value"])


def _month_start(now: datetime.datetime) -> datetime.datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def get_gb_awarded_this_month(user_id, level: int | None = None) -> float:
    month_start = _month_start(datetime.datetime.now(datetime.timezone.utc))
    if level is not None:
        row = await pool().fetchrow(
            """
            select coalesce(sum(amount_gb), 0) as total
            from gift_ledger
            where user_id = $1 and level = $2 and entry_type = $3
              and created_at >= $4
            """,
            user_id, level, f"credit_level_{level}", month_start,
        )
    else:
        row = await pool().fetchrow(
            """
            select coalesce(sum(amount_gb), 0) as total
            from gift_ledger
            where user_id = $1
              and entry_type in ('credit_level_1', 'credit_level_2', 'credit_level_3')
              and created_at >= $2
            """,
            user_id, month_start,
        )
    return float(row["total"])


async def credit_gift_volume(conn, user_id, entry_type, level, source_purchase_id,
                             source_user_id, gross_calculated_gb, amount_gb, note=None):
    row = await conn.fetchrow(
        "select gift_balance_gb from users where id = $1 for update", user_id
    )
    new_balance = float(row["gift_balance_gb"]) + amount_gb
    await conn.execute(
        """
        insert into gift_ledger
            (user_id, entry_type, level, source_purchase_id, source_user_id,
             gross_calculated_gb, amount_gb, balance_after_gb, note)
        values ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        user_id, entry_type, level, source_purchase_id, source_user_id,
        gross_calculated_gb, amount_gb, new_balance, note,
    )


async def convert_gift_to_reward_credit(conn, user_id) -> float:
    """کل حجم هدیه انباشته را به نرخ ثابت به «اعتبار پاداش» (فقط قابل مصرف در خرید بسته حجم) تبدیل می‌کند.
    فقط لحظه تایید خرید پنل کلید فراخوانی می‌شود (همان «باز شدن قفل مصرف» طبق سند قوانین کسب‌وکار).
    برای هم‌خوانی با gift_ledger، مصرف حجم هدیه به‌جای update مستقیم، از طریق یک ردیف debit_consumption ثبت می‌شود
    (تریگر sync_gift_balance خودش ستون gift_balance_gb را صفر می‌کند)."""
    row = await conn.fetchrow(
        "select gift_balance_gb from users where id = $1 for update", user_id
    )
    gift_gb = float(row["gift_balance_gb"])
    if gift_gb <= 0:
        return 0.0

    credit_toman = gift_gb * config.GIFT_GB_TO_REWARD_CREDIT_TOMAN
    await conn.execute(
        """
        insert into gift_ledger (user_id, entry_type, amount_gb, balance_after_gb, note)
        values ($1, 'debit_consumption', $2, 0, $3)
        """,
        user_id, -gift_gb, f"تبدیل حجم هدیه به اعتبار پاداش ({credit_toman:,.0f} تومان) با خرید پنل کلید",
    )
    await conn.execute(
        "update users set reward_credit_toman = reward_credit_toman + $2 where id = $1",
        user_id, credit_toman,
    )
    return credit_toman


async def admin_grant_gift_volume(user_id, amount_gb: float, admin_telegram_id: int, note: str | None = None):
    """اعطای دستی حجم هدیه توسط ادمین به یک کاربر انتخابی (مستقل از سیستم پاداش چندسطحی)."""
    async with pool().acquire() as conn:
        async with conn.transaction():
            await credit_gift_volume(
                conn, user_id, "admin_grant", None, None, None, amount_gb, amount_gb,
                note=note or f"اعطای دستی توسط ادمین {admin_telegram_id}",
            )


async def convert_gift_to_reward_credit_standalone(user_id) -> float:
    async with pool().acquire() as conn:
        async with conn.transaction():
            return await convert_gift_to_reward_credit(conn, user_id)


async def debit_reward_credit(user_id, amount_toman):
    async with pool().acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "select reward_credit_toman from users where id = $1 for update", user_id
            )
            new_balance = float(row["reward_credit_toman"]) - float(amount_toman)
            await conn.execute(
                "update users set reward_credit_toman = $2 where id = $1", user_id, new_balance,
            )


async def credit_wallet(user_id, tx_type: str, amount_toman, note: str | None = None,
                         reference_purchase_id=None, payment_method: str | None = None):
    """مثبت برای شارژ (هدیه/بازگشت وجه)، منفی برای برداشت — balance_after باید توسط فراخوان محاسبه شود."""
    async with pool().acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "select wallet_balance_toman from users where id = $1 for update", user_id
            )
            new_balance = float(row["wallet_balance_toman"]) + float(amount_toman)
            await conn.execute(
                """
                insert into wallet_transactions
                    (user_id, type, amount_toman, balance_after_toman, reference_purchase_id, payment_method, note)
                values ($1, $2, $3, $4, $5, $6, $7)
                """,
                user_id, tx_type, amount_toman, new_balance, reference_purchase_id, payment_method, note,
            )
    await recompute_agent_panel_active(user_id)


async def apply_referral_rewards(purchase):
    """قوانین بخش ۴ و ۸ سند: پاداش سطحی فقط برای بالادست‌های احراز هویت‌شده با موبایل،
    با اعمال سقف سطح و سقف کلی ماهانه مشتری عادی، بدون rollover."""
    ancestors = await get_referral_ancestors(purchase["user_id"])
    if not ancestors:
        return []

    level_config = await get_referral_level_config()
    customer_monthly_cap_gb = await get_system_setting("customer_monthly_cap_gb")
    volume_gb = float(purchase["volume_gb"])

    results = []
    async with pool().acquire() as conn:
        async with conn.transaction():
            for row in ancestors:
                if not row["phone_verified"]:
                    continue
                level = row["level"]
                ancestor_id = row["ancestor_id"]
                cfg = level_config[level]

                gross = volume_gb * cfg["reward_percent"] / 100

                awarded_level = await get_gb_awarded_this_month(ancestor_id, level)
                room_level = max(cfg["monthly_cap_gb"] - awarded_level, 0)

                awarded_total = await get_gb_awarded_this_month(ancestor_id)
                room_total = max(customer_monthly_cap_gb - awarded_total, 0)

                amount = min(gross, room_level, room_total)
                if amount <= 0:
                    continue

                await credit_gift_volume(
                    conn, ancestor_id, f"credit_level_{level}", level,
                    purchase["id"], purchase["user_id"], gross, amount,
                    note=f"پاداش سطح {level} از خرید کاربر {purchase['user_id']}",
                )
                results.append((ancestor_id, level, amount))
    return results
