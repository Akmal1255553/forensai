"""OSINT-подсказки: хеш, метаданные, ссылки на обратный поиск."""
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


def _exif_lines(path: Path) -> list[str]:
    lines: list[str] = []
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return ["EXIF: отсутствует"]
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, str(tag_id))
                val = str(value).strip()
                if len(val) > 120:
                    val = val[:120] + "…"
                lines.append(f"{tag}: {val}")
    except Exception as exc:
        lines.append(f"EXIF: ошибка чтения ({exc})")
    return lines[:20]


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
        "checks": [],
        "reverse_search": [],
        "metadata_lines": [],
        "recommendations": [],
    }

    if content_type == "image" and file_path and file_path.exists():
        out["file_hash_sha256"] = _sha256(file_path)
        out["metadata_lines"] = _exif_lines(file_path)
        w, h = metrics.get("width"), metrics.get("height")
        if w and h:
            out["checks"].append(f"Разрешение: {w}×{h} ({metrics.get('megapixels', '?')} MP)")
        if metrics.get("camera_model"):
            out["checks"].append(f"Камера (EXIF): {metrics['camera_model']}")
        elif metrics.get("exif_present") is False:
            out["checks"].append("EXIF отсутствует — возможна пересылка или экспорт из генератора")
        if metrics.get("format"):
            out["checks"].append(f"Формат: {metrics['format']}")

        out["reverse_search"] = [
            {
                "name": "Google Lens",
                "url": "https://lens.google.com/",
                "hint": "Загрузите изображение для поиска копий в сети",
            },
            {
                "name": "Yandex Images",
                "url": "https://yandex.ru/images/",
                "hint": "Обратный поиск по картинке",
            },
            {
                "name": "TinEye",
                "url": "https://tineye.com/",
                "hint": "Поиск ранних публикаций и дубликатов",
            },
        ]
        out["recommendations"] = [
            "Сверьте хеш файла с оригиналом источника, если он известен.",
            "Проверьте дату первой публикации через обратный поиск.",
            "Сопоставите EXIF с заявленным устройством и местом съёмки.",
        ]
    elif content_type == "video" and file_path and file_path.exists():
        out["file_hash_sha256"] = _sha256(file_path)
        dur = metrics.get("duration_sec")
        fps = metrics.get("fps")
        if dur is not None:
            out["checks"].append(f"Длительность: {dur} с")
        if fps:
            out["checks"].append(f"FPS: {fps}")
        if metrics.get("has_audio") is not None:
            out["checks"].append(f"Аудио: {'да' if metrics.get('has_audio') else 'нет'}")
        out["recommendations"] = [
            "Извлеките ключевые кадры и проверьте их отдельно как изображения.",
            "Сравните синхронизацию губ и мигание при подозрении на deepfake.",
        ]
    elif content_type == "text":
        out["recommendations"] = [
            "Проверьте уникальные фрагменты в поисковике в кавычках.",
            "Сопоставьте стиль с другими публикациями автора.",
        ]
    else:
        out["recommendations"] = ["Загрузите файл для расширенного OSINT-анализа."]

    return out
