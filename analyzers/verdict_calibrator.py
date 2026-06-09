"""Калибровка вердикта: баланс ложных «ИИ» на реальных фото и пропусков на AI-генерации."""

VERDICT_LABELS = {
    "ai_generated": "Сгенерировано ИИ",
    "human_created": "Создано человеком",
    "hybrid": "Подозрение на ИИ",
}


def verdict_from_scores(ai: int) -> tuple[str, str, int]:
    """Единый источник правды: вердикт и уверенность только из финального AI-индекса."""
    ai = max(0, min(100, int(ai)))
    if ai >= 65:
        return "ai_generated", VERDICT_LABELS["ai_generated"], max(58, min(95, ai))
    if ai >= 42:
        return "hybrid", VERDICT_LABELS["hybrid"], max(50, min(82, ai))
    return "human_created", VERDICT_LABELS["human_created"], max(62, min(92, 100 - ai))


WEAK_CATEGORIES = {
    "метаданные", "exif", "разрешение", "ela", "шум", "резкость", "цвет",
    "metadata", "resolution", "noise", "sharpness", "зона:",
}

# Только конкретные визуальные дефекты — не общие категории «анатомия/геометрия» от LLM.
STRONG_CATEGORIES = {
    "пальц", "зуб", "кракозябр", "текст на фоне",
    "deepfake", "генератор", "по генератора", "midjourney", "stable diffusion", "dall",
    "6 пальц", "лишн", "слияние", "артефакт генерац",
}


def _is_weak_evidence(category: str, description: str) -> bool:
    text = f"{category} {description}".lower()
    if _is_strong_evidence(category, description):
        return False
    return any(w in text for w in WEAK_CATEGORIES)


def _is_strong_evidence(category: str, description: str) -> bool:
    text = f"{category} {description}".lower()
    return any(s in text for s in STRONG_CATEGORIES)


def _local_synthetic_score(local: dict) -> int:
    """Оценка синтетичности по локальным метрикам (0–100)."""
    m = local.get("metrics") or {}
    score = 0
    if m.get("synthetic_smoothness"):
        score += 22
    if m.get("uniform_noise_suspect"):
        score += 18
    if m.get("no_exif_synthetic_hint") and (m.get("synthetic_smoothness") or m.get("uniform_noise_suspect")):
        score += 6
    if m.get("ai_resolution_hint"):
        score += 15
    zones_flagged = int(m.get("zones_flagged") or 0)
    if zones_flagged >= 3:
        score += min(25, zones_flagged * 6)
    elif zones_flagged >= 1:
        score += 8
    hot = int(m.get("zones_high_risk") or 0)
    score += min(20, hot * 10)
    return min(85, score)


def _looks_like_real_photo(metrics: dict, local_ai: float, synth: int) -> bool:
    """Селфи/фото из мессенджера: низкий локальный score, нет синтетики."""
    if local_ai > 32 or synth >= 32:
        return False
    if metrics.get("synthetic_smoothness") or metrics.get("uniform_noise_suspect"):
        return False
    return True


def _has_concrete_ai_evidence(evidence: list[dict]) -> bool:
    """Критические улики с конкретным дефектом, а не общие оценки категорий."""
    for e in evidence:
        if e.get("severity") != "critical":
            continue
        if _is_strong_evidence(e.get("category", ""), e.get("description", "")):
            return True
        desc = (e.get("description") or "").lower()
        if any(w in desc for w in ("пальц", "зуб", "кракозябр", "midjourney", "dall", "stable diffusion", "flux")):
            return True
    return False


def calibrate_image_report(
    data: dict,
    *,
    local_forensics: dict | None,
    evidence: list[dict],
    scores: dict,
    llm_ai: int | None = None,
    llm_verdict: str | None = None,
) -> dict:
    local = local_forensics or {}
    metrics = local.get("metrics") or {}
    local_ai = float(local.get("ai_score") or 0)

    critical = [e for e in evidence if e.get("severity") == "critical"]
    strong = [e for e in evidence if _is_strong_evidence(e.get("category", ""), e.get("description", ""))]
    weak_only = bool(evidence) and all(
        _is_weak_evidence(e.get("category", ""), e.get("description", "")) for e in evidence
    )

    ai = int(scores.get("ai", 50))
    llm_ai_val = int(llm_ai) if llm_ai is not None else ai
    synth = _local_synthetic_score(local)
    concrete_ai = _has_concrete_ai_evidence(evidence)
    real_photo = _looks_like_real_photo(metrics, local_ai, synth)

    camera_exif = metrics.get("camera_detected", False)
    llm_says_human = llm_verdict == "human_created" and llm_ai_val < 45

    # Повышаем только при подтверждённых сигналах (локальных или конкретных уликах)
    if synth >= 40 or concrete_ai:
        ai = max(ai, synth, local_ai)
    if llm_ai_val >= 72 and synth >= 25:
        ai = max(ai, llm_ai_val - 8)
    if len(strong) >= 2 or (len(strong) >= 1 and concrete_ai):
        ai = max(ai, 62)
    elif concrete_ai and len(critical) >= 1:
        ai = max(ai, 58)

    # Реальное фото: локальная экспертиза не видит синтетику — не доверяем завышению LLM
    if real_photo and not concrete_ai:
        ai = min(ai, int(local_ai * 0.55 + llm_ai_val * 0.45))
        ai = min(ai, 38)
        if weak_only or llm_says_human:
            ai = min(ai, max(12, int(local_ai + 5)))

    if camera_exif and not strong and not concrete_ai:
        ai = min(ai, max(int(local_ai), llm_ai_val - 10, 15))

    ai = max(0, min(100, ai))
    scores = {**scores, "ai": ai, "authenticity": max(0, 100 - ai)}

    verdict, label, confidence = verdict_from_scores(ai)
    if (len(strong) >= 2 or concrete_ai) and ai < 65 and synth >= 45:
        ai = max(ai, 65)
        scores = {**scores, "ai": ai, "authenticity": max(0, 100 - ai)}
        verdict, label, confidence = verdict_from_scores(ai)

    return {
        **data,
        "verdict": verdict,
        "verdict_label": label,
        "confidence": confidence,
        "scores": scores,
    }


def calibrate_video_report(
    data: dict,
    evidence: list[dict],
    scores: dict,
    llm_ai: int | None = None,
    llm_verdict: str | None = None,
) -> dict:
    strong = [e for e in evidence if _is_strong_evidence(e.get("category", ""), e.get("description", ""))]
    ai = int(scores.get("ai", 50))
    llm_ai_val = int(llm_ai) if llm_ai is not None else ai

    if llm_verdict == "ai_generated" or llm_ai_val >= 58 or len(strong) >= 1:
        ai = max(ai, llm_ai_val, 55)

    if not strong and ai < 45 and llm_verdict == "human_created":
        ai = min(ai, 40)
        scores = {**scores, "ai": ai, "authenticity": max(60, 100 - ai)}

    verdict, label, confidence = verdict_from_scores(ai)
    return {
        **data,
        "verdict": verdict,
        "verdict_label": label,
        "confidence": confidence,
        "scores": {**scores, "ai": ai, "authenticity": max(0, 100 - ai)},
    }
