"""Локальная цифровая экспертиза изображений (без LLM)."""
from __future__ import annotations

import io
import math
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat
from PIL.ExifTags import TAGS

# Типичные выходы генераторов (SD, MJ, DALL·E, Flux)
AI_SQUARE_SIZES = {512, 768, 1024, 1536, 832, 896, 1216, 1344}
AI_COMMON_LONG_EDGE = {768, 1024, 1280, 1344, 1536, 1792, 2048}


@dataclass
class ImageForensicReport:
    ai_score: float
    category_scores: dict
    metrics: dict
    findings: list[dict] = field(default_factory=list)
    zones: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ai_score": round(self.ai_score, 1),
            "category_scores": self.category_scores,
            "metrics": self.metrics,
            "findings": self.findings,
            "zones": self.zones,
        }

    def summary_text(self) -> str:
        lines = [f"Локальный AI-score изображения: {self.ai_score:.1f}/100 (консервативный)"]
        if self.metrics.get("camera_detected"):
            lines.append("Камера в EXIF обнаружена — приоритет «реальное фото»")
        for k, v in self.metrics.items():
            lines.append(f"{k}: {v}")
        for f in self.findings[:8]:
            lines.append(f"[{f['severity']}] {f['category']}: {f['description']}")
        return "\n".join(lines)


def _read_exif_info(img: Image.Image) -> dict:
    info = {"present": False, "camera_detected": False, "camera_model": "", "software": ""}
    try:
        exif = img.getexif()
        if not exif:
            return info
        info["present"] = True
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            val = str(value)
            if tag in ("Make", "Model"):
                info["camera_detected"] = True
                info["camera_model"] += f" {val}".strip()
            if tag == "Software":
                info["software"] = val.lower()
        ai_sw = ["midjourney", "stable diffusion", "dall", "firefly", "leonardo", "comfyui", "novelai"]
        if any(s in info["software"] for s in ai_sw):
            info["ai_software"] = True
    except Exception:
        pass
    return info


def analyze_image(path: Path) -> ImageForensicReport:
    findings: list[dict] = []
    signal_scores: list[float] = []
    category_parts: dict[str, list[float]] = {
        "anatomy": [], "lighting": [], "geometry": [], "artifacts": [], "metadata": [],
    }
    metrics: dict = {}

    with Image.open(path) as img:
        w, h = img.size
        rgb = img.convert("RGB")
        metrics.update({
            "width": w, "height": h,
            "megapixels": round(w * h / 1_000_000, 2),
            "aspect_ratio": round(w / h, 3) if h else 0,
            "format": img.format or Path(path).suffix.lstrip(".").upper(),
            "mode": img.mode,
        })

        exif_info = _read_exif_info(img)
        metrics["exif_present"] = exif_info["present"]
        metrics["camera_detected"] = exif_info["camera_detected"]
        if exif_info.get("camera_model"):
            metrics["camera_model"] = exif_info["camera_model"]

        if exif_info.get("ai_software"):
            signal_scores.extend([75, 80])
            category_parts["metadata"].append(85)
            findings.append({
                "category": "ПО генератора",
                "severity": "critical",
                "description": f"EXIF Software указывает на ИИ: {exif_info['software'][:80]}",
                "location": "EXIF",
            })
        elif exif_info["camera_detected"]:
            findings.append({
                "category": "Метаданные камеры",
                "severity": "minor",
                "description": f"Обнаружена камера: {exif_info['camera_model']}",
                "location": "EXIF",
            })
        elif not exif_info["present"]:
            category_parts["metadata"].append(6)
            metrics["no_exif_synthetic_hint"] = True
            findings.append({
                "category": "Метаданные",
                "severity": "minor",
                "description": "EXIF отсутствует (нормально для мессенджеров и соцсетей)",
                "location": "EXIF",
            })

        if max(w, h) in AI_COMMON_LONG_EDGE or (w == h and w in AI_SQUARE_SIZES):
            metrics["ai_resolution_hint"] = True
        if w == h and w in AI_SQUARE_SIZES:
            category_parts["geometry"].append(35)
            signal_scores.append(30)
            findings.append({
                "category": "Геометрия",
                "severity": "moderate",
                "description": f"Квадрат {w}px — возможен выход SD/Midjourney",
                "location": "Кадр",
            })

        ela = _error_level_analysis(rgb)
        metrics.update({"ela_mean": ela["mean"], "ela_max": ela["max"], "ela_variance": ela["variance"]})
        if ela["variance"] < 15 and ela["max"] < 30:
            category_parts["artifacts"].append(18)
            findings.append({
                "category": "ELA",
                "severity": "minor",
                "description": f"Очень низкая ELA ({ela['variance']:.1f}) — слабый сигнал, не доказательство",
                "location": "Весь кадр",
            })

        noise = _noise_uniformity(rgb)
        metrics["noise_uniformity"] = round(noise, 2)
        if noise > 0.93:
            category_parts["artifacts"].append(28)
            metrics["uniform_noise_suspect"] = True
            signal_scores.append(28)
            findings.append({
                "category": "Артефакты",
                "severity": "moderate",
                "description": "Подозрительно однородный шум по кадру (типично для AI-апскейла)",
                "location": "Весь кадр",
            })

        sharp = _sharpness_map(rgb)
        metrics["sharpness_mean"] = sharp["mean"]
        metrics["sharpness_variance"] = sharp["variance"]
        if sharp["variance"] < 120 and sharp["mean"] < 18:
            metrics["synthetic_smoothness"] = True
            category_parts["artifacts"].append(32)
            signal_scores.append(35)
            findings.append({
                "category": "Визуальная синтетика",
                "severity": "moderate",
                "description": "Чрезмерно гладкие текстуры и низкая вариативность резкости (признак AI-рендера)",
                "location": "Весь кадр",
            })

        entropy = _color_entropy(rgb)
        metrics["color_entropy"] = round(entropy, 3)

        zones = _analyze_grid_zones(rgb, w, h)
        hot_zones = [z for z in zones if z["ai_score"] >= 55]
        for z in hot_zones[:4]:
            findings.append({
                "category": f"Зона: {z['region']}",
                "severity": "moderate" if z["ai_score"] < 70 else "critical",
                "description": "; ".join(z["issues"]),
                "location": z["region"],
            })
            signal_scores.append(z["ai_score"] * 0.5)

    category_scores = {k: int(min(85, statistics_mean(v) if v else 8)) for k, v in category_parts.items()}

    if signal_scores:
        ai_score = statistics_mean(signal_scores)
    else:
        ai_score = 12.0

    if metrics.get("camera_detected") and not metrics.get("synthetic_smoothness"):
        ai_score = max(5, ai_score - 15)
    elif metrics.get("camera_detected"):
        ai_score = max(8, ai_score - 8)

    if metrics.get("synthetic_smoothness") or metrics.get("uniform_noise_suspect"):
        ai_score = max(ai_score, 42)
    if metrics.get("no_exif_synthetic_hint") and (metrics.get("synthetic_smoothness") or len(hot_zones) >= 2):
        ai_score = max(ai_score, 48)

    ai_score = max(5.0, min(78.0, ai_score))

    metrics["zones_analyzed"] = len(zones)
    metrics["zones_flagged"] = len(hot_zones)
    metrics["zones_high_risk"] = sum(1 for z in zones if z.get("risk") == "high")
    metrics["findings_count"] = len(findings)
    metrics["critical_findings"] = sum(1 for f in findings if f["severity"] == "critical")

    return ImageForensicReport(
        ai_score=ai_score,
        category_scores=category_scores,
        metrics=metrics,
        findings=findings,
        zones=zones,
    )


def statistics_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _error_level_analysis(img: Image.Image) -> dict:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")
    diff = ImageChops.difference(img, recompressed)
    stat = ImageStat.Stat(diff)
    mean = sum(stat.mean) / len(stat.mean)
    vals = [sum(p) / 3 for p in diff.getdata()]
    variance = sum((v - mean) ** 2 for v in vals) / max(len(vals), 1)
    return {"mean": round(mean, 2), "max": max(vals) if vals else 0, "variance": round(variance, 2)}


def _noise_uniformity(img: Image.Image) -> float:
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    return 1.0 - min(1.0, stat.stddev[0] / (stat.mean[0] or 1))


def _sharpness_map(img: Image.Image) -> dict:
    gray = img.convert("L")
    laplacian = gray.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(laplacian)
    return {"mean": round(stat.mean[0], 2), "variance": round(stat.var[0], 2)}


def _color_entropy(img: Image.Image) -> float:
    hist = img.convert("RGB").histogram()
    total = sum(hist)
    if not total:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in hist if c > 0)


def _analyze_grid_zones(img: Image.Image, w: int, h: int) -> list[dict]:
    regions = [
        "верх-лево", "верх-центр", "верх-право",
        "центр-лево", "центр", "центр-право",
        "низ-лево", "низ-центр", "низ-право",
    ]
    cols, rows = 3, 3
    cw, rh = max(w // cols, 1), max(h // rows, 1)
    raw: list[dict] = []

    for ri in range(rows):
        for ci in range(cols):
            idx = ri * cols + ci
            box = (ci * cw, ri * rh, (ci + 1) * cw if ci < 2 else w, (ri + 1) * rh if ri < 2 else h)
            crop = img.crop(box)
            ela = _error_level_analysis(crop)
            noise = _noise_uniformity(crop)
            sharp = _sharpness_map(crop)
            entropy = _color_entropy(crop)
            edge_mean = ImageStat.Stat(crop.convert("L").filter(ImageFilter.FIND_EDGES)).mean[0]
            raw.append({
                "index": idx + 1, "region": regions[idx],
                "box": {"x": box[0], "y": box[1], "w": box[2] - box[0], "h": box[3] - box[1]},
                "ela_var": ela["variance"], "noise": noise,
                "sharp_var": sharp["variance"], "entropy": entropy, "edge_mean": edge_mean,
            })

    avg_ela = statistics_mean([z["ela_var"] for z in raw]) or 1
    avg_noise = statistics_mean([z["noise"] for z in raw])
    avg_sharp = statistics_mean([z["sharp_var"] for z in raw]) or 1
    avg_entropy = statistics_mean([z["entropy"] for z in raw])
    avg_edge = statistics_mean([z["edge_mean"] for z in raw]) or 1

    zones = []
    for z in raw:
        score_parts: list[float] = []
        issues: list[str] = []

        ela_ratio = z["ela_var"] / max(avg_ela, 0.01)
        if ela_ratio < 0.2:
            score_parts.append(min(35, int((0.2 - ela_ratio) * 80)))
            issues.append(f"ELA ниже ср. ({z['ela_var']:.0f}/{avg_ela:.0f})")
        elif ela_ratio > 3.0:
            score_parts.append(min(40, int((ela_ratio - 3.0) * 20)))
            issues.append("ELA-пик — возможная вставка")

        if z["noise"] - avg_noise > 0.12:
            score_parts.append(min(30, int((z["noise"] - avg_noise) * 150)))

        sharp_ratio = z["sharp_var"] / max(avg_sharp, 0.01)
        if sharp_ratio < 0.25:
            score_parts.append(min(25, int((0.25 - sharp_ratio) * 50)))

        edge_ratio = z["edge_mean"] / max(avg_edge, 0.01)
        if edge_ratio > 2.2:
            score_parts.append(min(35, int((edge_ratio - 2.2) * 25)))
            issues.append("Резкие контуры")

        ai_score = round(sum(score_parts) / len(score_parts) if score_parts else max(3, min(15, abs(ela_ratio - 1) * 8)), 1)
        ai_score = max(3, min(75, ai_score))
        risk = "clean" if ai_score < 32 else "low" if ai_score < 48 else "medium" if ai_score < 62 else "high"

        zones.append({
            **z, "ai_score": ai_score, "risk": risk,
            "issues": issues if issues else ["В пределах нормы"],
            "metrics_detail": {
                "ela": round(z["ela_var"], 1), "noise": round(z["noise"] * 100),
                "sharpness": round(z["sharp_var"], 1), "entropy": round(z["entropy"], 2),
            },
            "zone_type": "grid",
            "severity": "critical" if ai_score >= 68 else "moderate" if ai_score >= 48 else "minor" if ai_score >= 32 else "clean",
        })
    return zones
