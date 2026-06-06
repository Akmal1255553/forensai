import re

VERDICT_HUMAN_MARKERS = (
    "создано человеком",
    "human_created",
    "реальн",
    "не сгенерирован",
    "не является сгенерирован",
    "отсутствуют типичные визуальные признаки генерации",
    "низкая оценка ai",
    "низкий ai",
)
VERDICT_AI_MARKERS = (
    "сгенерировано ии",
    "ai_generated",
    "нейросет",
    "midjourney",
    "stable diffusion",
    "dall",
    "flux",
    "синтетическ",
)

from analyzers.plagiarism import analyze_plagiarism
from analyzers.text_heuristics import (
    AI_CLICHES_EN,
    AI_CLICHES_RU,
    AI_POLITENESS_RU,
    _find_cliches,
)


def analyze_segments(text: str) -> list[dict]:
    plagiarism = analyze_plagiarism(text)
    pl_map = {s["index"]: s for s in plagiarism.segments}

    pattern = re.compile(r"[^.!?…\n]+[.!?…]?|\n+", re.MULTILINE)
    segments = []
    idx = 0

    for match in pattern.finditer(text):
        chunk = match.group().strip()
        if len(chunk) < 8:
            continue
        idx += 1
        ai_score, ai_flags = _score_segment_ai(chunk)
        pl_data = pl_map.get(idx, {})
        pl_score = pl_data.get("plagiarism_score", 0)
        pl_flags = pl_data.get("plagiarism_flags", [])

        combined = max(ai_score, pl_score)
        risk = "high" if combined >= 60 else "medium" if combined >= 35 else "clean"

        segments.append({
            "index": idx,
            "start": match.start(),
            "end": match.end(),
            "text": chunk,
            "ai_score": round(ai_score, 1),
            "plagiarism_score": round(pl_score, 1),
            "combined_risk": risk,
            "ai_flags": ai_flags,
            "plagiarism_flags": pl_flags,
        })

    if not segments and text.strip():
        ai_score, ai_flags = _score_segment_ai(text.strip())
        segments.append({
            "index": 1, "start": 0, "end": len(text), "text": text.strip(),
            "ai_score": round(ai_score, 1), "plagiarism_score": 0,
            "combined_risk": "medium" if ai_score >= 35 else "clean",
            "ai_flags": ai_flags, "plagiarism_flags": [],
        })
    return segments


def _score_segment_ai(text: str) -> tuple[float, list[str]]:
    flags: list[str] = []
    score_parts: list[float] = []

    cliches = _find_cliches(text, AI_CLICHES_RU + AI_CLICHES_EN + AI_POLITENESS_RU)
    if cliches:
        score_parts.append(min(90, 35 + len(cliches) * 20))
        flags.extend(f"ИИ-клише: «{p}»" for p, _ in cliches)

    words = text.split()
    if 12 <= len(words) <= 22:
        score_parts.append(25)
        flags.append("Типичная длина предложения для ИИ (12–22 слова)")

    if re.match(r"^\s*(?:Важно|Следует|Таким|В заключение|Подводя|На сегодня)", text, re.I):
        score_parts.append(40)
        flags.append("Шаблонное вводное предложение")

    if text.count(",") >= 3 and len(words) > 15:
        score_parts.append(20)
        flags.append("Многочисленные вставные конструкции")

    formal = sum(1 for w in ["является", "представляет", "обеспечивает", "способствует"] if w in text.lower())
    if formal >= 2:
        score_parts.append(30)
        flags.append("Формальный канцелярский стиль")

    score = sum(score_parts) / len(score_parts) if score_parts else 5.0
    return min(95.0, max(5.0, score)), flags


def _safe_str(val) -> str:
    if val is None:
        return ""
    if isinstance(val, (dict, list)):
        return ""
    return str(val).strip()


def _is_error_text(text: str) -> bool:
    if not text:
        return True
    markers = ("429", "quota", "LLM недоступен", "Error code", "Traceback", "invalid", "FAILED")
    return any(m.lower() in text.lower() for m in markers)


def _extract_ai_mentions(text: str) -> list[int]:
    """Числа AI-индекса из текста LLM (например «AI 18/100»)."""
    found: list[int] = []
    for m in re.finditer(r"(?:ai|ии)[\s-]*(?:индекс|оценка|score)?[\s:]*(\d{1,3})", text, re.I):
        found.append(int(m.group(1)))
    for m in re.finditer(r"(\d{1,3})\s*/\s*100", text):
        found.append(int(m.group(1)))
    return found


def _llm_reasoning_conflicts(verdict: str, ai_score: float, llm_reasoning: dict | str | None) -> bool:
    """LLM-текст противоречит финальному вердикту или индексу."""
    if not llm_reasoning:
        return False
    if isinstance(llm_reasoning, dict):
        blob = " ".join(_safe_str(llm_reasoning.get(k)) for k in ("summary", "ai_analysis", "conclusion"))
    else:
        blob = _safe_str(llm_reasoning)
    if not blob:
        return False
    low = blob.lower()
    final_ai = int(ai_score)

    if final_ai >= 42 and any(m in low for m in VERDICT_HUMAN_MARKERS):
        return True
    if final_ai < 42 and verdict == "ai_generated" and any(m in low for m in VERDICT_AI_MARKERS):
        return False
    if verdict in ("ai_generated", "hybrid") and "создано человеком" in low and final_ai >= 42:
        return True

    mentioned = _extract_ai_mentions(blob)
    if mentioned and final_ai >= 42:
        if max(mentioned) <= 35 and final_ai >= 50:
            return True
        if min(mentioned) >= 55 and final_ai <= 35:
            return True
    return False


def build_reasoning(
    *,
    verdict: str,
    verdict_label: str,
    confidence: int,
    ai_score: float,
    plagiarism_score: float,
    evidence: list[dict],
    segments: list[dict],
    analysis_mode: str,
    content_type: str = "text",
    metrics: dict | None = None,
    category_scores: dict | None = None,
    zones: list[dict] | None = None,
    llm_reasoning: str | dict | None = None,
) -> dict:
    metrics = metrics or {}
    category_scores = category_scores or {}
    zones = zones or []

    critical = sum(1 for e in evidence if e.get("severity") == "critical")
    moderate = sum(1 for e in evidence if e.get("severity") == "moderate")
    authenticity = int(metrics.get("authenticity") or max(0, 100 - int(ai_score)))

    built = {
        "summary": _build_summary(
            verdict_label, content_type, ai_score, plagiarism_score, confidence,
            critical, moderate, len(segments), len(zones), metrics, category_scores,
        ),
        "ai_analysis": _ai_paragraph(content_type, ai_score, segments, evidence, category_scores, zones),
        "plagiarism_analysis": _plagiarism_paragraph(content_type, plagiarism_score, segments, metrics),
        "conclusion": _conclusion(verdict, verdict_label, confidence, ai_score, plagiarism_score, authenticity),
    }

    use_llm = not _llm_reasoning_conflicts(verdict, ai_score, llm_reasoning)
    if use_llm and isinstance(llm_reasoning, dict):
        for key in ("ai_analysis", "plagiarism_analysis"):
            val = _safe_str(llm_reasoning.get(key))
            if val and not _is_error_text(val) and len(val) > 20:
                built[key] = val
        val = _safe_str(llm_reasoning.get("summary"))
        if val and not _is_error_text(val) and len(val) > 20 and not _llm_reasoning_conflicts(verdict, ai_score, {"summary": val}):
            built["summary"] = f"{built['summary']} {val}"[:1200]
    elif use_llm and isinstance(llm_reasoning, str) and len(llm_reasoning.strip()) > 40 and not _is_error_text(llm_reasoning):
        extra = llm_reasoning.strip()[:500]
        if not _llm_reasoning_conflicts(verdict, ai_score, extra):
            built["summary"] = f"{built['summary']} {extra}"[:1200]

    return built


def _build_summary(
    verdict_label: str,
    content_type: str,
    ai: float,
    pl: float,
    confidence: int,
    critical: int,
    moderate: int,
    seg_count: int,
    zone_count: int,
    metrics: dict,
    categories: dict,
) -> str:
    auth = max(0, 100 - int(ai))
    risk = "высокий" if ai >= 65 else "умеренный" if ai >= 42 else "низкий"
    parts = [
        f"Вердикт: {verdict_label}. AI-индекс {int(ai)}/100 ({risk} риск) · "
        f"подлинность {auth}/100 · плагиат {int(pl)}/100 · уверенность {confidence}%.",
        f"Улики: {critical} критических, {moderate} умеренных.",
    ]

    if content_type == "text":
        parts.append(f"Проанализировано {seg_count} предложений.")
    elif content_type == "image":
        mp = metrics.get("megapixels", "?")
        res = f"{metrics.get('width', '?')}×{metrics.get('height', '?')}"
        parts.append(f"Изображение {res} ({mp} MP), зон проверено: {zone_count or metrics.get('zones_analyzed', 9)}.")
        if categories:
            top = max(categories.items(), key=lambda x: x[1])
            parts.append(f"Макс. риск — категория «{top[0]}»: {top[1]}/100.")
    elif content_type == "video":
        dur = metrics.get("duration_sec", "?")
        frames = metrics.get("frames_analyzed", 0)
        fps = metrics.get("fps", "?")
        parts.append(f"Видео {dur}с · {fps} fps · кадров: {frames} · зон: {zone_count}.")
        sync = categories.get("sync")
        bio = categories.get("biometrics")
        if sync is not None:
            parts.append(f"Biometrics: {bio or '—'}/100 · Sync: {sync}/100.")

    mode = metrics.get("analysis_engine", "hybrid")
    parts.append(f"Движок: {mode}.")
    return " ".join(parts)


def _ai_paragraph(content_type, ai_score, segments, evidence, categories, zones):
    critical = [e for e in evidence if e.get("severity") == "critical"]
    parts = [f"Индекс ИИ {int(ai_score)}/100 ({'высокий' if ai_score >= 60 else 'умеренный' if ai_score >= 35 else 'низкий'})."]

    if content_type in ("image", "video"):
        if categories:
            cats = ", ".join(f"{k}: {v}" for k, v in sorted(categories.items(), key=lambda x: -x[1])[:4])
            parts.append(f"Категории: {cats}.")
        if zones:
            hot = sorted(zones, key=lambda z: z.get("ai_score", 0), reverse=True)[:3]
            zones_txt = "; ".join(
                f"{z.get('region', 'зона')} ({z.get('ai_score', '?')}%)"
                for z in hot
            )
            parts.append(f"Проблемные зоны: {zones_txt}.")
    else:
        flagged = [s for s in segments if s.get("ai_score", 0) >= 35]
        if flagged:
            parts.append(f"Флагов в тексте: {len(flagged)} из {len(segments)}.")
        if critical:
            parts.append(f"Критических улик: {len(critical)}.")

    return " ".join(parts)


def _plagiarism_paragraph(content_type, plagiarism_score, segments, metrics):
    if content_type == "image":
        return (
            f"Индекс заимствования/монтажа: {int(plagiarism_score)}/100. "
            f"ELA variance: {metrics.get('ela_variance', '—')}, "
            f"EXIF: {'есть' if metrics.get('exif_present') else 'отсутствует'}."
        )
    if content_type == "video":
        return (
            f"Индекс монтажа/deepfake: {int(plagiarism_score)}/100. "
            f"Variance кадров: {metrics.get('frame_score_variance', '—')}, "
            f"аудио: {'да' if metrics.get('has_audio') else 'нет'}."
        )
    if plagiarism_score < 20:
        return f"Плагиат {int(plagiarism_score)}/100 — внутренних дубликатов не обнаружено."
    flagged = [s for s in segments if s.get("plagiarism_score", 0) >= 35]
    return f"Плагиат {int(plagiarism_score)}/100 — подозрительных предложений: {len(flagged)}."


def _conclusion(verdict, label, confidence, ai, pl, auth):
    return (
        f"Вердикт: {label} · уверенность {confidence}% · "
        f"AI {int(ai)} · плагиат {int(pl)} · authenticity {auth}."
    )


def build_metrics(
    *,
    ai_score: int,
    plagiarism_score: int,
    confidence: int,
    evidence: list[dict],
    content_type: str,
    local_metrics: dict | None = None,
    llm_metrics: dict | None = None,
    segments: list | None = None,
    zones: list | None = None,
) -> dict:
    local_metrics = local_metrics or {}
    llm_metrics = llm_metrics or {}
    critical = sum(1 for e in evidence if e.get("severity") == "critical")
    moderate = sum(1 for e in evidence if e.get("severity") == "moderate")
    minor = sum(1 for e in evidence if e.get("severity") == "minor")

    m = {
        "ai_index": ai_score,
        "plagiarism_index": plagiarism_score,
        "authenticity": max(0, 100 - int(ai_score)),
        "confidence": confidence,
        "critical_findings": critical or int(llm_metrics.get("critical_findings", 0)),
        "moderate_findings": moderate or int(llm_metrics.get("moderate_findings", 0)),
        "minor_findings": minor,
        "total_findings": len(evidence),
        "zones_flagged": len(zones or []) or int(llm_metrics.get("zones_flagged", 0)),
        "segments_analyzed": len(segments or []),
        "content_type": content_type,
    }
    for key in ("width", "height", "megapixels", "duration_sec", "fps", "frames_analyzed", "ela_variance", "exif_present", "has_audio"):
        if key in local_metrics:
            m[key] = local_metrics[key]
    m["processing_quality"] = int(llm_metrics.get("processing_quality") or min(95, 50 + critical * 5 + moderate * 2))
    return m
