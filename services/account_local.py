"""Local JSON account storage (dev / fallback without Supabase)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import DATA_DIR, FREE_ANALYSES_PER_MONTH, PRO_PRICE_USD, REFERRAL_DISCOUNT_PERCENT

ACCOUNTS_FILE = DATA_DIR / "accounts.json"

PLANS = {
    "free": {"analyses_limit": FREE_ANALYSES_PER_MONTH, "price_usd": 0},
    "pro": {"analyses_limit": 999_999, "price_usd": PRO_PRICE_USD},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _load() -> dict:
    DATA_DIR.mkdir(exist_ok=True)
    if not ACCOUNTS_FILE.exists():
        return {"users": {}}
    try:
        return json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"users": {}}


def _save(data: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    ACCOUNTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _referral_code(user_id: str) -> str:
    return user_id.replace("-", "")[:8].upper()


def get_or_create_user(user_id: str | None, referral_code: str | None = None) -> dict:
    data = _load()
    users = data.setdefault("users", {})

    if not user_id or user_id not in users:
        user_id = user_id or str(uuid.uuid4())
        users[user_id] = {
            "id": user_id,
            "created_at": _now_iso(),
            "plan": "free",
            "plan_expires_at": None,
            "usage": {},
            "bonus_analyses": 0,
            "discount_percent": 0,
            "referral_code": _referral_code(user_id),
            "referred_by": None,
            "referrals_verified": 0,
            "pending_referrals": [],
        }

    user = users[user_id]
    if referral_code and not user.get("referred_by"):
        ref = referral_code.strip().upper()
        for uid, u in users.items():
            if u.get("referral_code") == ref and uid != user_id:
                user["referred_by"] = uid
                users[uid].setdefault("pending_referrals", []).append(user_id)
                break

    _save(data)
    return _public_account(user)


def _usage_this_month(user: dict) -> int:
    return int(user.get("usage", {}).get(_month_key(), 0))


def _public_account(user: dict) -> dict:
    limit = PLANS[user.get("plan", "free")]["analyses_limit"]
    used = _usage_this_month(user)
    bonus = int(user.get("bonus_analyses", 0))
    effective_limit = limit + bonus if user.get("plan") == "free" else limit
    remaining = max(0, effective_limit - used) if user.get("plan") == "free" else 999_999

    price = PLANS["pro"]["price_usd"]
    discount = min(50, int(user.get("discount_percent", 0)))
    price_discounted = round(price * (1 - discount / 100), 2)

    return {
        "user_id": user["id"],
        "plan": user.get("plan", "free"),
        "referral_code": user.get("referral_code"),
        "discount_percent": discount,
        "referrals_verified": int(user.get("referrals_verified", 0)),
        "usage_this_month": used,
        "analyses_limit": effective_limit,
        "analyses_remaining": remaining,
        "pro_price_usd": price,
        "pro_price_discounted_usd": price_discounted,
        "plan_expires_at": user.get("plan_expires_at"),
    }


def get_account(user_id: str) -> dict | None:
    data = _load()
    user = data.get("users", {}).get(user_id)
    if not user:
        return None
    return _public_account(user)


def ensure_can_analyze(user_id: str) -> None:
    acc = get_account(user_id)
    if not acc:
        return
    if acc["plan"] == "pro":
        return
    if acc["analyses_remaining"] <= 0:
        raise PermissionError("analysis_limit_reached")


def record_analysis(user_id: str, count: int = 1) -> dict:
    data = _load()
    users = data.setdefault("users", {})
    user = users.get(user_id)
    if not user:
        get_or_create_user(user_id)
        data = _load()
        user = data["users"][user_id]

    mk = _month_key()
    prev = int(user.setdefault("usage", {}).get(mk, 0))
    user["usage"][mk] = prev + max(1, count)

    referred_by = user.get("referred_by")
    if referred_by and referred_by in users and prev == 0:
        _verify_referral(data, referred_by, user_id)

    _save(data)
    return _public_account(user)


def _verify_referral(data: dict, referrer_id: str, invitee_id: str) -> None:
    referrer = data["users"].get(referrer_id)
    if not referrer:
        return
    pending = referrer.get("pending_referrals") or []
    if invitee_id not in pending:
        return
    pending.remove(invitee_id)
    referrer["pending_referrals"] = pending
    referrer["referrals_verified"] = int(referrer.get("referrals_verified", 0)) + 1
    referrer["discount_percent"] = min(50, int(referrer.get("discount_percent", 0)) + REFERRAL_DISCOUNT_PERCENT)
    referrer["bonus_analyses"] = int(referrer.get("bonus_analyses", 0)) + 2

    invitee = data["users"].get(invitee_id)
    if invitee:
        invitee["discount_percent"] = min(50, int(invitee.get("discount_percent", 0)) + REFERRAL_DISCOUNT_PERCENT)


def upgrade_plan(user_id: str, plan: str = "pro") -> dict:
    if plan not in PLANS:
        raise ValueError("unknown_plan")
    data = _load()
    user = data.get("users", {}).get(user_id)
    if not user:
        raise ValueError("user_not_found")

    user["plan"] = plan
    if plan == "pro":
        user["plan_expires_at"] = None

    _save(data)
    return _public_account(user)


def register_referral_attempt(user_id: str, referral_code: str) -> dict:
    return get_or_create_user(user_id, referral_code)
