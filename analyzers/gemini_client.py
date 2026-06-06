"""Клиент Gemini без Files API (совместим с ключами AQ.* / AIza*)."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from PIL import Image

from config import GEMINI_API_KEY, GEMINI_MODEL
from prompts import HEURISTICS_APPENDIX, IMAGE_PROMPT_EXTRA, SYSTEM_PROMPT, VIDEO_PROMPT_EXTRA


def _get_model():
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    try:
        return genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={"response_mime_type": "application/json"},
        )
    except Exception:
        return genai.GenerativeModel(GEMINI_MODEL)


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


def _extract_video_frames(path: Path, max_frames: int = 6) -> list[Image.Image]:
    frames: list[Image.Image] = []
    try:
        import cv2

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return frames
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        indices = (
            [int(total * i / max(max_frames - 1, 1)) for i in range(max_frames)]
            if total > max_frames
            else list(range(min(max_frames, total)))
        )
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(rgb))
        cap.release()
    except Exception:
        pass
    return frames


def generate_forensic_analysis(
    content_type: str,
    heuristics_text: str,
    file_path: Path | None = None,
    text_content: str | None = None,
) -> dict:
    model = _get_model()

    prompt = SYSTEM_PROMPT
    if content_type == "image":
        prompt += IMAGE_PROMPT_EXTRA
    elif content_type == "video":
        prompt += VIDEO_PROMPT_EXTRA
    if heuristics_text:
        prompt += "\n\n" + HEURISTICS_APPENDIX.format(heuristics=heuristics_text)

    parts: list = [prompt]

    if content_type == "text" and text_content:
        parts.append(f"\n\n--- ТЕКСТ ---\n{text_content}")
    elif content_type == "image" and file_path:
        with Image.open(file_path) as img:
            parts.append(img.convert("RGB"))
        parts.append(
            "\nПроанализируй изображение на признаки AI-генерации (Midjourney, SD, DALL·E, Flux). "
            "Если картинка синтетическая — verdict ai_generated, scores.ai 70+. "
            "Верни JSON с zones, category_scores, metrics, evidence, reasoning с цифрами."
        )
    elif content_type == "video" and file_path:
        frames = _extract_video_frames(file_path, max_frames=6)
        if not frames:
            raise RuntimeError(
                "Не удалось извлечь кадры из видео. Установите opencv-python-headless или конвертируйте в MP4."
            )
        parts.append(f"\nВидео разбито на {len(frames)} ключевых кадров (inline, без upload):")
        for i, frame in enumerate(frames):
            parts.append(f"\n--- Кадр {i + 1}/{len(frames)} ---")
            parts.append(frame)
        parts.append(
            "\nПроанализируй видео по кадрам: deepfake, биометрия, sync. "
            "JSON с zones (с timestamp), category_scores, metrics."
        )
    else:
        raise ValueError(f"Неподдерживаемый тип: {content_type}")

    response = model.generate_content(parts)
    if not response.text:
        raise RuntimeError("Gemini вернул пустой ответ")
    return _parse_json_response(response.text)
