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

STRONG_CATEGORIES = {
    "анатомия", "anatomy", "пальц", "зуб", "уш", "глаз", "лиц", "портрет",
    "геометр", "geometry", "кракозябр", "текст на фоне", "текст",
    "deepfake", "синхрон", "биометр", "артефакт", "генератор", "синтет",
    "пластик", "кож", "волос", "по генератора", "midjourney", "stable", "dall",
    "визуальн", "ai-эстетик", "нереалист",
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
    if m.get("no_exif_synthetic_hint"):
        score += 12
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
    moderate = [e for e in evidence if e.get("severity") == "moderate"]
    strong = [e for e in evidence if _is_strong_evidence(e.get("category", ""), e.get("description", ""))]
    weak_only = bool(evidence) and all(
        _is_weak_evidence(e.get("category", ""), e.get("description", "")) for e in evidence
    )

    ai = int(scores.get("ai", 50))
    llm_ai_val = int(llm_ai) if llm_ai is not None else ai
    synth = _local_synthetic_score(local)

    camera_exif = metrics.get("camera_detected", False)
    llm_says_ai = llm_verdict == "ai_generated" or llm_ai_val >= 58
    llm_says_human = llm_verdict == "human_created" and llm_ai_val < 42

    # Повышаем AI при синтетических локальных сигналах или сильных уликах
    if synth >= 35 or len(strong) >= 1:
        ai = max(ai, synth, llm_ai_val, local_ai)
    if llm_says_ai:
        ai = max(ai, llm_ai_val, 52)
    if len(strong) >= 2 or len(critical) >= 2:
        ai = max(ai, 68)
    elif len(strong) >= 1 or len(critical) >= 1:
        ai = max(ai, 55)

    # Снижаем только при явных признаках реальной камеры + согласии LLM
    if camera_exif and llm_says_human and weak_only and not strong and synth < 25:
        ai = min(ai, max(12, llm_ai_val, int(local_ai)))
        ai = max(8, ai - 5)
    elif camera_exif and not strong and llm_ai_val < 38:
        ai = min(ai, max(llm_ai_val, int(local_ai * 0.5 + llm_ai_val * 0.5)))

    ai = max(0, min(100, ai))
    scores = {**scores, "ai": ai, "authenticity": max(0, 100 - ai)}

    verdict, label, confidence = verdict_from_scores(ai)
    # При множественных сильных уликах — не ниже hybrid/ai
    if len(strong) >= 2 or len(critical) >= 2:
        if ai < 65:
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
