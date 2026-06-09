"""Supabase persistence for profiles and report history."""
from __future__ import annotations

from datetime import datetime, timezone

from supabase import Client, create_client

from config import (
    FREE_ANALYSES_PER_MONTH,
    PRO_PRICE_USD,
    REFERRAL_DISCOUNT_PERCENT,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
)

PLANS = {
    "free": {"analyses_limit": FREE_ANALYSES_PER_MONTH, "price_usd": 0},
    "pro": {"analyses_limit": 999_999, "price_usd": PRO_PRICE_USD},
}

_client: Client | None = None


def _month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _referral_code(user_id: str) -> str:
    return user_id.replace("-", "")[:8].upper()


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("supabase_not_configured")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _client


def _public_account(row: dict) -> dict:
    plan = row.get("plan", "free")
    limit = PLANS[plan]["analyses_limit"]
    usage = row.get("usage") or {}
    used = int(usage.get(_month_key(), 0))
    bonus = int(row.get("bonus_analyses", 0))
    effective_limit = limit + bonus if plan == "free" else limit
    remaining = max(0, effective_limit - used) if plan == "free" else 999_999
    discount = min(50, int(row.get("discount_percent", 0)))
    price = PLANS["pro"]["price_usd"]

    return {
        "user_id": row["id"],
        "plan": plan,
        "referral_code": row.get("referral_code"),
        "discount_percent": discount,
        "referrals_verified": int(row.get("referrals_verified", 0)),
        "usage_this_month": used,
        "analyses_limit": effective_limit,
        "analyses_remaining": remaining,
        "pro_price_usd": price,
        "pro_price_discounted_usd": round(price * (1 - discount / 100), 2),
        "plan_expires_at": row.get("plan_expires_at"),
    }


def _fetch_profile(user_id: str) -> dict | None:
    res = get_client().table("profiles").select("*").eq("id", user_id).maybe_single().execute()
    return res.data


def _insert_profile(user_id: str) -> dict:
    row = {
        "id": user_id,
        "referral_code": _referral_code(user_id),
        "usage": {},
        "pending_referrals": [],
    }
    get_client().table("profiles").insert(row).execute()
    return _fetch_profile(user_id) or row


def _find_referrer_id(referral_code: str) -> str | None:
    res = (
        get_client()
        .table("profiles")
        .select("id")
        .eq("referral_code", referral_code.strip().upper())
        .maybe_single()
        .execute()
    )
    return res.data["id"] if res.data else None


def _apply_referral(user_id: str, referral_code: str) -> None:
    row = _fetch_profile(user_id)
    if not row or row.get("referred_by"):
        return

    referrer_id = _find_referrer_id(referral_code)
    if not referrer_id or referrer_id == user_id:
        return

    referrer = _fetch_profile(referrer_id)
    if not referrer:
        return

    pending = list(referrer.get("pending_referrals") or [])
    if user_id not in pending:
        pending.append(user_id)

    get_client().table("profiles").update({"referred_by": referrer_id}).eq("id", user_id).execute()
    get_client().table("profiles").update({"pending_referrals": pending}).eq("id", referrer_id).execute()


def get_or_create_user(user_id: str, referral_code: str | None = None) -> dict:
    row = _fetch_profile(user_id) or _insert_profile(user_id)
    if referral_code:
        _apply_referral(user_id, referral_code)
        row = _fetch_profile(user_id) or row
    return _public_account(row)


def get_account(user_id: str) -> dict | None:
    row = _fetch_profile(user_id)
    return _public_account(row) if row else None


def ensure_can_analyze(user_id: str) -> None:
    acc = get_account(user_id)
    if not acc:
        return
    if acc["plan"] == "pro":
        return
    if acc["analyses_remaining"] <= 0:
        raise PermissionError("analysis_limit_reached")


def _verify_referral(referrer_id: str, invitee_id: str) -> None:
    referrer = _fetch_profile(referrer_id)
    if not referrer:
        return
    pending = list(referrer.get("pending_referrals") or [])
    if invitee_id not in pending:
        return
    pending.remove(invitee_id)
    get_client().table("profiles").update(
        {
            "pending_referrals": pending,
            "referrals_verified": int(referrer.get("referrals_verified", 0)) + 1,
            "discount_percent": min(
                50, int(referrer.get("discount_percent", 0)) + REFERRAL_DISCOUNT_PERCENT
            ),
            "bonus_analyses": int(referrer.get("bonus_analyses", 0)) + 2,
        }
    ).eq("id", referrer_id).execute()

    invitee = _fetch_profile(invitee_id)
    if invitee:
        get_client().table("profiles").update(
            {
                "discount_percent": min(
                    50, int(invitee.get("discount_percent", 0)) + REFERRAL_DISCOUNT_PERCENT
                )
            }
        ).eq("id", invitee_id).execute()


def record_analysis(user_id: str, count: int = 1) -> dict:
    row = _fetch_profile(user_id)
    if not row:
        return get_or_create_user(user_id)

    usage = dict(row.get("usage") or {})
    mk = _month_key()
    prev = int(usage.get(mk, 0))
    usage[mk] = prev + max(1, count)

    get_client().table("profiles").update({"usage": usage}).eq("id", user_id).execute()

    if row.get("referred_by") and prev == 0:
        _verify_referral(row["referred_by"], user_id)

    return get_account(user_id) or _public_account(row)


def upgrade_plan(user_id: str, plan: str = "pro") -> dict:
    if plan not in PLANS:
        raise ValueError("unknown_plan")
    row = _fetch_profile(user_id)
    if not row:
        raise ValueError("user_not_found")

    updates = {"plan": plan}
    if plan == "pro":
        updates["plan_expires_at"] = None
    get_client().table("profiles").update(updates).eq("id", user_id).execute()
    return get_account(user_id) or _public_account({**row, **updates})


def register_referral_attempt(user_id: str, referral_code: str) -> dict:
    _apply_referral(user_id, referral_code)
    return get_or_create_user(user_id)


def list_history(user_id: str, limit: int = 30) -> list[dict]:
    res = (
        get_client()
        .table("report_history")
        .select("id, created_at, filename, verdict, verdict_label, ai_score, report_data")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    items = []
    for row in res.data or []:
        items.append(
            {
                "id": row["id"],
                "at": row["created_at"],
                "filename": row.get("filename"),
                "verdict": row.get("verdict"),
                "verdict_label": row.get("verdict_label"),
                "ai": row.get("ai_score"),
                "data": row.get("report_data"),
            }
        )
    return items


def save_history(user_id: str, entry: dict, limit: int = 30) -> None:
    report = entry.get("report") or {}
    get_client().table("report_history").insert(
        {
            "user_id": user_id,
            "filename": entry.get("filename"),
            "verdict": report.get("verdict"),
            "verdict_label": report.get("verdict_label"),
            "ai_score": (report.get("scores") or {}).get("ai"),
            "report_data": entry,
        }
    ).execute()

    res = (
        get_client()
        .table("report_history")
        .select("id")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    ids = [r["id"] for r in (res.data or [])]
    if len(ids) > limit:
        for old_id in ids[limit:]:
            get_client().table("report_history").delete().eq("id", old_id).execute()


def clear_history(user_id: str) -> None:
    get_client().table("report_history").delete().eq("user_id", user_id).execute()
