"""OSINT: хеш, метаданные, обратный поиск — компактная структура для UI."""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image
from PIL.ExifTags import TAGS


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _exif_summary(path: Path) -> tuple[str, list[str]]:
    """Статус EXIF и ключевые теги (только если есть данные)."""
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return "missing", []
            lines: list[str] = []
            camera = ""
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, str(tag_id))
                val = str(value).strip()
                if tag in ("Make", "Model"):
                    camera += f" {val}".strip()
                if tag in ("Make", "Model", "DateTime", "Software", "LensModel"):
                    if len(val) > 80:
                        val = val[:80] + "…"
                    lines.append(f"{tag}: {val}")
            status = "camera" if camera else "present"
            return status, lines[:6]
    except Exception:
        return "error", []


def build_osint(
    *,
    filename: str,
    content_type: str,
    file_path: Path | None,
    metrics: dict | None = None,
) -> dict:
    metrics = metrics or {}
    out: dict = {
        "filename": filename,
        "content_type": content_type,
        "compact": {},
        "reverse_search": [],
        "metadata_lines": [],
    }

    if content_type == "image" and file_path and file_path.exists():
        full_hash = _sha256(file_path)
        w, h = metrics.get("width"), metrics.get("height")
        exif_status, exif_lines = _exif_summary(file_path)
        if metrics.get("camera_detected") and metrics.get("camera_model"):
            exif_status = "camera"

        out["file_hash_sha256"] = full_hash
        out["compact"] = {
            "hash_short": full_hash[:16],
            "hash_full": full_hash,
            "resolution": f"{w}×{h}" if w and h else None,
            "megapixels": metrics.get("megapixels"),
            "exif_status": exif_status,
            "camera": metrics.get("camera_model") or None,
            "format": metrics.get("format"),
        }
        if exif_lines:
            out["metadata_lines"] = exif_lines

        out["reverse_search"] = [
            {"name": "Google Lens", "url": "https://lens.google.com/"},
            {"name": "Yandex", "url": "https://yandex.ru/images/"},
            {"name": "TinEye", "url": "https://tineye.com/"},
        ]

    elif content_type == "video" and file_path and file_path.exists():
        full_hash = _sha256(file_path)
        out["file_hash_sha256"] = full_hash
        out["compact"] = {
            "hash_short": full_hash[:16],
            "hash_full": full_hash,
            "duration_sec": metrics.get("duration_sec"),
            "fps": metrics.get("fps"),
            "has_audio": metrics.get("has_audio"),
        }

    return out
