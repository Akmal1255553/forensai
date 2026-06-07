import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from analyzers.compare import compare_reports
from analyzers.forensic_engine import analyze_content
from config import (
    FREE_ANALYSES_PER_MONTH,
    GEMINI_API_KEY,
    MAX_TEXT_CHARS,
    MAX_UPLOAD_MB,
    OPENAI_API_KEY,
    PRO_PRICE_USD,
    REFERRAL_DISCOUNT_PERCENT,
    STATIC_DIR,
    UPLOAD_DIR,
)
from services.account_store import (
    ensure_can_analyze,
    get_account,
    get_or_create_user,
    record_analysis,
    register_referral_attempt,
    upgrade_plan,
)

app = FastAPI(title="AI Forensic Expert", version="1.0.0")
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
async def status():
    return {
        "gemini_configured": bool(GEMINI_API_KEY),
        "openai_configured": bool(OPENAI_API_KEY),
        "max_upload_mb": MAX_UPLOAD_MB,
        "free_analyses_per_month": FREE_ANALYSES_PER_MONTH,
        "pro_price_usd": PRO_PRICE_USD,
        "referral_discount_percent": REFERRAL_DISCOUNT_PERCENT,
        "modes": {
            "text": "heuristics" if not (GEMINI_API_KEY or OPENAI_API_KEY) else "heuristics+llm",
            "image": "metadata_only" if not (GEMINI_API_KEY or OPENAI_API_KEY) else "llm",
            "video": "unavailable" if not GEMINI_API_KEY else "llm",
        },
    }


class AccountInitBody(BaseModel):
    referral_code: str | None = None


class UpgradeBody(BaseModel):
    plan: str = "pro"


class ReferralBody(BaseModel):
    referral_code: str


def _user_id_header(x_user_id: str | None = Header(None, alias="X-User-Id")) -> str | None:
    return (x_user_id or "").strip() or None


def _check_quota(user_id: str | None) -> str:
    uid = get_or_create_user(user_id)["user_id"]
    try:
        ensure_can_analyze(uid)
    except PermissionError:
        raise HTTPException(402, "analysis_limit_reached")
    return uid


@app.get("/api/account")
async def account_me(x_user_id: str | None = Header(None, alias="X-User-Id")):
    acc = get_or_create_user(_user_id_header(x_user_id))
    return {"ok": True, "account": acc}


@app.post("/api/account/init")
async def account_init(
    body: AccountInitBody | None = None,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    code = body.referral_code if body else None
    acc = get_or_create_user(_user_id_header(x_user_id), code)
    return {"ok": True, "account": acc}


@app.post("/api/account/referral")
async def account_referral(
    body: ReferralBody,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    uid = _user_id_header(x_user_id)
    if not uid:
        raise HTTPException(400, "user_id_required")
    acc = register_referral_attempt(uid, body.referral_code)
    return {"ok": True, "account": acc, "message": "referral_applied"}


@app.post("/api/subscription/upgrade")
async def subscription_upgrade(
    body: UpgradeBody,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    uid = _user_id_header(x_user_id)
    if not uid:
        raise HTTPException(400, "user_id_required")
    get_or_create_user(uid)
    if body.plan != "pro":
        raise HTTPException(400, "invalid_plan")
    acc = upgrade_plan(uid, "pro")
    return {"ok": True, "account": acc, "message": "subscription_activated"}


async def _save_upload(upload: UploadFile) -> tuple[Path, str, str | None]:
    filename = upload.filename or "file.bin"
    mime = upload.content_type
    ext = Path(filename).suffix or ".bin"
    saved_path = UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    size = 0
    max_bytes = MAX_UPLOAD_MB * 1024 * 1024
    with saved_path.open("wb") as out:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                saved_path.unlink(missing_ok=True)
                raise HTTPException(400, f"Файл «{filename}» больше {MAX_UPLOAD_MB} МБ")
            out.write(chunk)
    return saved_path, filename, mime


@app.post("/api/analyze")
async def analyze(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    if not file and not (text and text.strip()):
        raise HTTPException(400, "Загрузите файл или вставьте текст")

    if text and len(text) > MAX_TEXT_CHARS:
        raise HTTPException(400, f"Текст превышает лимит {MAX_TEXT_CHARS} символов")

    saved_path: Path | None = None
    filename = "input.txt"
    mime: str | None = "text/plain"
    raw_text = text.strip() if text else None

    if file and file.filename:
        saved_path, filename, mime = await _save_upload(file)
        if raw_text is None and mime and mime.startswith("text/"):
            raw_text = saved_path.read_text(encoding="utf-8", errors="replace")

    uid = _check_quota(_user_id_header(x_user_id))

    try:
        report = await analyze_content(
            filename=filename,
            mime=mime,
            file_path=saved_path,
            raw_text=raw_text,
        )
        account = record_analysis(uid)
        return {"ok": True, "filename": filename, "report": report, "account": account}
    finally:
        if saved_path and saved_path.exists():
            saved_path.unlink(missing_ok=True)


@app.post("/api/compare")
async def compare(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    uid = _check_quota(_user_id_header(x_user_id))
    path_a: Path | None = None
    path_b: Path | None = None
    try:
        path_a, name_a, mime_a = await _save_upload(file_a)
        path_b, name_b, mime_b = await _save_upload(file_b)
        report_a = await analyze_content(filename=name_a, mime=mime_a, file_path=path_a, raw_text=None)
        report_b = await analyze_content(filename=name_b, mime=mime_b, file_path=path_b, raw_text=None)
        comparison = compare_reports(report_a, report_b, label_a=name_a, label_b=name_b)
        account = record_analysis(uid, count=2)
        return {
            "ok": True,
            "comparison": comparison,
            "report_a": report_a,
            "report_b": report_b,
            "filename_a": name_a,
            "filename_b": name_b,
            "account": account,
        }
    finally:
        for p in (path_a, path_b):
            if p and p.exists():
                p.unlink(missing_ok=True)
