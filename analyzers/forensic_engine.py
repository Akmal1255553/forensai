import json
import mimetypes
import re
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS

from analyzers.gemini_client import generate_forensic_analysis
from analyzers.image_forensics import analyze_image
from analyzers.plagiarism import analyze_plagiarism
from analyzers.segment_analysis import analyze_segments, build_metrics, build_reasoning
from analyzers.text_heuristics import analyze_text_heuristics, heuristics_to_verdict
from analyzers.osint import build_osint
from analyzers.verdict_calibrator import calibrate_image_report, calibrate_video_report, verdict_from_scores
from analyzers.video_forensics import analyze_video
from config import GEMINI_API_KEY, GEMINI_MODEL, OPENAI_API_KEY, OPENAI_MODEL
from prompts import HEURISTICS_APPENDIX, IMAGE_PROMPT_EXTRA, SYSTEM_PROMPT, VIDEO_PROMPT_EXTRA

IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}
VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".html", ".xml", ".rtf"}


def detect_content_type(filename: str, mime: str | None, raw_text: str | None) -> str:
    if raw_text is not None:
        return "text"
    ext = Path(filename).suffix.lower()
    if mime in IMAGE_TYPES or ext in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}:
        return "image"
    if mime in VIDEO_TYPES or ext in {".mp4", ".webm", ".mov", ".avi", ".mkv"}:
        return "video"
    if mime and mime.startswith("text/"):
        return "text"
    if ext in TEXT_EXTENSIONS:
        return "text"
    return "unknown"


def extract_image_metadata(path: Path) -> list[dict]:
    return analyze_image(path).findings


def _parse_json_response(raw: str) -> dict:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


async def _analyze_with_gemini(
    content_type: str,
    heuristics_text: str,
    file_path: Path | None = None,
    text_content: str | None = None,
) -> dict:
    import asyncio

    return await asyncio.to_thread(
        generate_forensic_analysis,
        content_type,
        heuristics_text,
        file_path,
        text_content,
    )


def _compute_scores(ai_score: float, plagiarism_score: float, data: dict, local_ai: float, content_type: str = "text") -> dict:
    scores = data.get("scores") or {}
    llm_ai = scores.get("ai")
    if llm_ai is None:
        merged_ai = int(local_ai)
    elif content_type == "image":
        llm_val = int(llm_ai)
        merged_ai = int(local_ai * 0.25 + llm_val * 0.75)
        if llm_val >= 55:
            merged_ai = max(merged_ai, llm_val)
        if llm_val >= 70:
            merged_ai = max(merged_ai, llm_val - 5)
    elif content_type == "video":
        merged_ai = int(local_ai * 0.35 + int(llm_ai) * 0.65)
    else:
        merged_ai = int(local_ai * 0.45 + int(llm_ai) * 0.55)
    return {
        "ai": max(0, min(100, merged_ai)),
        "plagiarism": int(scores.get("plagiarism", plagiarism_score)),
        "authenticity": int(scores.get("authenticity") or max(0, 100 - merged_ai)),
    }


def _merge_zones(local_zones: list, llm_zones: list) -> list:
    merged = []
    seen = set()
    for z in (llm_zones or []) + (local_zones or []):
        key = (z.get("region"), z.get("index"))
        if key in seen:
            continue
        seen.add(key)
        merged.append({
            "index": z.get("index", len(merged) + 1),
            "region": z.get("region", "зона"),
            "ai_score": int(z.get("ai_score", 0)),
            "issues": z.get("issues") or ([z.get("description")] if z.get("description") else []),
            "severity": z.get("severity") or ("critical" if z.get("ai_score", 0) >= 65 else "moderate" if z.get("ai_score", 0) >= 40 else "minor"),
            "box": z.get("box"),
            "frame": z.get("frame"),
            "timestamp_sec": z.get("timestamp_sec"),
            "zone_type": z.get("zone_type", "llm"),
            "risk": z.get("risk"),
            "metrics_detail": z.get("metrics_detail"),
        })
    return sorted(merged, key=lambda x: -x["ai_score"])[:15]


def _finalize_report(
    data: dict,
    content_type: str,
    mode: str,
    *,
    ai_score: float = 50.0,
    plagiarism_score: float = 8.0,
    segments: list[dict] | None = None,
    heuristics: dict | None = None,
    plagiarism: dict | None = None,
    local_forensics: dict | None = None,
    file_path: Path | None = None,
    filename: str = "input",
) -> dict:
    verdict_map = {
        "ai_generated": "Сгенерировано ИИ",
        "human_created": "Создано человеком",
        "hybrid": "Гибрид/Редакция",
    }
    verdict = data.get("verdict", "hybrid")
    confidence = int(data.get("confidence", 50))
    evidence = data.get("evidence") or []
    segments = segments or []
    local_forensics = local_forensics or {}

    scores = _compute_scores(ai_score, plagiarism_score, data, local_forensics.get("ai_score", ai_score), content_type)
    category_scores = data.get("category_scores") or local_forensics.get("category_scores") or {}
    zones = _merge_zones(local_forensics.get("zones", []), data.get("zones", []))

    calibrated = dict(data)
    calibrated["scores"] = scores
    calibrated["evidence"] = evidence
    llm_scores = data.get("scores") or {}
    llm_ai = llm_scores.get("ai")
    llm_verdict = data.get("verdict")
    if content_type == "image":
        calibrated = calibrate_image_report(
            calibrated,
            local_forensics=local_forensics,
            evidence=evidence,
            scores=scores,
            llm_ai=int(llm_ai) if llm_ai is not None else None,
            llm_verdict=llm_verdict,
        )
    elif content_type == "video":
        calibrated = calibrate_video_report(
            calibrated,
            evidence=evidence,
            scores=scores,
            llm_ai=int(llm_ai) if llm_ai is not None else None,
            llm_verdict=llm_verdict,
        )

    scores = calibrated.get("scores", scores)
    final_ai = int(scores.get("ai", 50))
    if content_type in ("image", "video"):
        verdict, verdict_label, confidence = verdict_from_scores(final_ai)
    else:
        verdict = calibrated.get("verdict", data.get("verdict", "hybrid"))
        verdict_label = calibrated.get("verdict_label") or verdict_map.get(verdict, "Гибрид/Редакция")
        confidence = int(calibrated.get("confidence", data.get("confidence", 50)))

    local_metrics = dict(local_forensics.get("metrics") or {})
    local_metrics["analysis_engine"] = mode
    llm_metrics = data.get("metrics") or {}

    metrics = build_metrics(
        ai_score=scores["ai"],
        plagiarism_score=scores["plagiarism"],
        confidence=confidence,
        evidence=evidence,
        content_type=content_type,
        local_metrics=local_metrics,
        llm_metrics=llm_metrics,
        segments=segments,
        zones=zones,
    )

    reasoning = build_reasoning(
        verdict=verdict,
        verdict_label=verdict_label,
        confidence=confidence,
        ai_score=scores["ai"],
        plagiarism_score=scores["plagiarism"],
        evidence=evidence,
        segments=segments,
        analysis_mode=mode,
        content_type=content_type,
        metrics=metrics,
        category_scores=category_scores,
        zones=zones,
        llm_reasoning=data.get("reasoning"),
    )

    osint = build_osint(
        filename=filename,
        content_type=content_type,
        file_path=file_path if file_path and file_path.exists() else None,
        metrics=metrics,
    )

    return {
        "verdict": verdict,
        "verdict_label": verdict_label,
        "confidence": confidence,
        "content_type": content_type,
        "scores": scores,
        "category_scores": category_scores,
        "metrics": metrics,
        "zones": zones,
        "evidence": evidence,
        "reasoning": reasoning,
        "segments": segments,
        "analysis_mode": mode,
        "osint": osint,
        "frames": local_forensics.get("frames", []),
        **({"heuristics": heuristics} if heuristics else {}),
        **({"plagiarism": plagiarism} if plagiarism else {}),
        **({"forensics": local_forensics} if local_forensics else {}),
    }


async def _analyze_with_openai(
    content_type: str,
    heuristics_text: str,
    file_path: Path | None = None,
    text_content: str | None = None,
) -> dict:
    import base64
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = SYSTEM_PROMPT + (IMAGE_PROMPT_EXTRA if content_type == "image" else "")
    if heuristics_text:
        prompt += "\n\n" + HEURISTICS_APPENDIX.format(heuristics=heuristics_text)

    user_content: list[dict] = []
    if content_type == "text" and text_content:
        user_content.append({"type": "text", "text": f"Проанализируй:\n\n{text_content}"})
    elif content_type == "image" and file_path:
        mime = mimetypes.guess_type(str(file_path))[0] or "image/jpeg"
        b64 = base64.b64encode(file_path.read_bytes()).decode()
        user_content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"}})
        user_content.append({"type": "text", "text": "Детальный анализ изображения. JSON с zones и metrics."})
    elif content_type == "video":
        raise ValueError("OpenAI: для видео используйте GEMINI_API_KEY")
    else:
        raise ValueError("Неподдерживаемый тип")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": user_content}],
        response_format={"type": "json_object"},
        max_tokens=4096,
    )
    return json.loads(response.choices[0].message.content)


def _build_text_context(text: str) -> tuple[str, dict, dict, list]:
    heuristics = analyze_text_heuristics(text)
    plagiarism = analyze_plagiarism(text)
    segments = analyze_segments(text)

    ctx = heuristics.summary_text()
    ctx += f"\n\nПлагиат: {plagiarism.score:.1f}/100 · Сегментов: {len(segments)}"
    for seg in segments:
        if seg["ai_score"] >= 40 or seg["plagiarism_score"] >= 40:
            ctx += f"\n  #{seg['index']} AI={seg['ai_score']} PL={seg['plagiarism_score']}: {seg['text'][:80]}"
    return ctx, heuristics.to_dict(), plagiarism.to_dict(), segments


def _build_heuristic_report(
    content_type: str,
    heuristics_report,
    *,
    extra_evidence: list[dict] | None = None,
    plagiarism_report=None,
    segments: list[dict] | None = None,
    local_forensics: dict | None = None,
    analysis_mode: str = "heuristics_only",
    error_note: str | None = None,
    file_path: Path | None = None,
    filename: str = "input",
) -> dict:
    verdict, label, confidence = heuristics_to_verdict(heuristics_report)
    if plagiarism_report:
        pl_score = plagiarism_report.score
    elif content_type in ("image", "video") and local_forensics:
        pl_score = max(8, local_forensics.get("ai_score", 30) * 0.35)
    else:
        pl_score = 8.0

    evidence = list(extra_evidence or [])
    for f in heuristics_report.findings:
        evidence.append({"category": f.category, "severity": f.severity, "description": f.description, "location": f.location})
    if plagiarism_report:
        for f in plagiarism_report.findings[:8]:
            evidence.append({"category": f"Плагиат: {f.category}", "severity": f.severity, "description": f.description, "location": f.location})

    ai_s = local_forensics.get("ai_score", heuristics_report.ai_score) if local_forensics else heuristics_report.ai_score

    if pl_score >= 55 and verdict == "human_created":
        verdict, label = "hybrid", "Гибрид/Редакция"

    data = {
        "verdict": verdict,
        "verdict_label": label,
        "confidence": confidence,
        "content_type": content_type,
        "evidence": evidence,
        "scores": {"ai": int(ai_s), "plagiarism": int(pl_score)},
        "category_scores": (local_forensics or {}).get("category_scores", {}),
        "zones": (local_forensics or {}).get("zones", []),
    }

    report = _finalize_report(
        data, content_type, analysis_mode,
        ai_score=ai_s, plagiarism_score=pl_score,
        segments=segments or [], heuristics=heuristics_report.to_dict(),
        plagiarism=plagiarism_report.to_dict() if plagiarism_report else None,
        local_forensics=local_forensics,
        file_path=file_path,
        filename=filename,
    )
    if error_note and not _is_llm_error_shown(report):
        short = error_note.split("Details:")[0].strip()[:80]
        report["reasoning"]["summary"] = (
            f"LLM недоступен ({short}). Локальная экспертиза: AI {int(ai_s)}/100, "
            f"улик {len(evidence)}, зон {len(report.get('zones', []))}."
        )
    return report


def _is_llm_error_shown(report: dict) -> bool:
    s = report.get("reasoning", {}).get("summary", "")
    return "429" in s or "quota" in s.lower()


async def analyze_content(
    *,
    filename: str,
    mime: str | None,
    file_path: Path | None,
    raw_text: str | None,
) -> dict:
    content_type = detect_content_type(filename, mime, raw_text)
    heuristics_text = ""
    extra_evidence: list[dict] = []
    heuristics = None
    plagiarism = None
    segments: list[dict] = []
    local_forensics: dict | None = None
    text = ""

    if content_type == "text":
        text = raw_text or (file_path.read_text(encoding="utf-8", errors="replace") if file_path else "")
        heuristics_text, _, _, segments = _build_text_context(text)
        heuristics = analyze_text_heuristics(text)
        plagiarism = analyze_plagiarism(text)
    elif content_type == "image" and file_path:
        img_report = analyze_image(file_path)
        local_forensics = img_report.to_dict()
        extra_evidence = img_report.findings
        heuristics_text = img_report.summary_text()
        heuristics = analyze_text_heuristics("")
        heuristics.ai_score = img_report.ai_score
    elif content_type == "video" and file_path:
        vid_report = analyze_video(file_path)
        local_forensics = vid_report.to_dict()
        extra_evidence = vid_report.findings
        heuristics_text = vid_report.summary_text()
        heuristics = analyze_text_heuristics("")
        heuristics.ai_score = vid_report.ai_score
    else:
        heuristics = analyze_text_heuristics("")
        heuristics.ai_score = 50.0

    has_llm = bool(GEMINI_API_KEY or OPENAI_API_KEY)
    needs_vision = content_type in {"image", "video"}

    if needs_vision and not GEMINI_API_KEY and not (OPENAI_API_KEY and content_type == "image"):
        report = _build_heuristic_report(
            content_type, heuristics, extra_evidence=extra_evidence,
            local_forensics=local_forensics, analysis_mode="forensics_local",
            file_path=file_path, filename=filename,
        )
        report["reasoning"]["summary"] = (
            f"Локальная экспертиза: AI {report['scores']['ai']}/100 · "
            f"зон {report['metrics'].get('zones_flagged', 0)} · "
            f"улик {report['metrics']['total_findings']}. Для LLM добавьте GEMINI_API_KEY."
        )
        return report

    if content_type == "text" and not has_llm:
        return _build_heuristic_report(
            content_type, heuristics, plagiarism_report=plagiarism, segments=segments,
            analysis_mode="heuristics_only", file_path=file_path, filename=filename,
        )

    try:
        if GEMINI_API_KEY:
            if content_type == "text" and not text:
                text = file_path.read_text(encoding="utf-8", errors="replace") if file_path else ""
            llm_data = await _analyze_with_gemini(content_type, heuristics_text, file_path, text or raw_text)
            mode = "gemini"
        elif OPENAI_API_KEY:
            if content_type == "text" and not text:
                text = file_path.read_text(encoding="utf-8", errors="replace") if file_path else ""
            llm_data = await _analyze_with_openai(content_type, heuristics_text, file_path, text or raw_text)
            mode = "openai"
        else:
            return _build_heuristic_report(
                content_type, heuristics, extra_evidence=extra_evidence,
                plagiarism_report=plagiarism, segments=segments, local_forensics=local_forensics,
                file_path=file_path, filename=filename,
            )

        if extra_evidence:
            llm_data["evidence"] = extra_evidence + (llm_data.get("evidence") or [])

        ai_s = local_forensics.get("ai_score", heuristics.ai_score) if local_forensics else heuristics.ai_score
        pl_s = plagiarism.score if plagiarism else max(8, ai_s * 0.2)

        return _finalize_report(
            llm_data, content_type, mode,
            ai_score=ai_s, plagiarism_score=pl_s,
            segments=segments,
            heuristics=heuristics.to_dict() if content_type == "text" else None,
            plagiarism=plagiarism.to_dict() if plagiarism else None,
            local_forensics=local_forensics,
            file_path=file_path,
            filename=filename,
        )
    except Exception as exc:
        return _build_heuristic_report(
            content_type, heuristics, extra_evidence=extra_evidence,
            plagiarism_report=plagiarism, segments=segments,
            local_forensics=local_forensics, analysis_mode="forensics_fallback",
            error_note=str(exc)[:200],
            file_path=file_path,
            filename=filename,
        )
