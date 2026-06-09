"""Account, subscription, and referral storage (Supabase or local JSON)."""
from __future__ import annotations

from config import SUPABASE_ENABLED

if SUPABASE_ENABLED:
    from services import supabase_db as _store
else:
    from services import account_local as _store

get_or_create_user = _store.get_or_create_user
get_account = _store.get_account
ensure_can_analyze = _store.ensure_can_analyze
record_analysis = _store.record_analysis
upgrade_plan = _store.upgrade_plan
register_referral_attempt = _store.register_referral_attempt
