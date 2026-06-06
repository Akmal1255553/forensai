"""Локальная экспертиза видео: метаданные + ключевые кадры."""
from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from analyzers.image_forensics import analyze_image, statistics_mean


@dataclass
class VideoForensicReport:
    ai_score: float
    category_scores: dict
    metrics: dict
    findings: list[dict] = field(default_factory=list)
    zones: list[dict] = field(default_factory=list)
    frames: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ai_score": round(self.ai_score, 1),
            "category_scores": self.category_scores,
            "metrics": self.metrics,
            "findings": self.findings,
            "zones": self.zones,
            "frames": self.frames,
        }

    def summary_text(self) -> str:
        lines = [f"Локальный AI-score видео: {self.ai_score:.1f}/100"]
        for k, v in self.metrics.items():
            lines.append(f"{k}: {v}")
        for f in self.findings[:8]:
            lines.append(f"[{f['severity']}] {f['category']}: {f['description']}")
        return "\n".join(lines)


def analyze_video(path: Path, max_frames: int = 6) -> VideoForensicReport:
    findings: list[dict] = []
    metrics: dict = {"file_size_mb": round(path.stat().st_size / (1024 * 1024), 2)}
    frames_data: list[dict] = []
    frame_scores: list[float] = []
    all_zones: list[dict] = []

    probe = _ffprobe(path)
    if probe:
        metrics.update(probe)
        if probe.get("duration_sec"):
            findings.append({
                "category": "Метаданные видео",
                "severity": "minor",
                "description": (
                    f"Длительность {probe['duration_sec']}с, "
                    f"{probe.get('width', '?')}×{probe.get('height', '?')}, "
                    f"{probe.get('fps', '?')} fps, кодек {probe.get('codec', '?')}"
                ),
                "location": "Контейнер",
            })
        if not probe.get("has_audio") and probe.get("duration_sec", 0) > 3:
            findings.append({
                "category": "Аудиодорожка",
                "severity": "moderate",
                "description": "Нет аудио — затрудняет проверку синхрона губ (deepfake)",
                "location": "Аудио",
            })

    extracted = _extract_frames(path, max_frames)
    if not extracted:
        findings.append({
            "category": "Кадры",
            "severity": "minor",
            "description": "Не удалось извлечь кадры локально — анализ через LLM",
            "location": "",
        })
        ai_score = 45.0
    else:
        metrics["frames_analyzed"] = len(extracted)
        for i, frame_path in enumerate(extracted):
            try:
                img_report = analyze_image(frame_path)
                t_sec = metrics.get("duration_sec", 0)
                timestamp = round(t_sec * i / max(len(extracted) - 1, 1), 2) if t_sec else i

                frames_data.append({
                    "index": i + 1,
                    "timestamp_sec": timestamp,
                    "ai_score": img_report.ai_score,
                    "metrics": img_report.metrics,
                })
                frame_scores.append(img_report.ai_score)
                findings.extend({
                    **f,
                    "location": f"Кадр #{i + 1} ({timestamp}с) — {f.get('location', '')}",
                } for f in img_report.findings[:3])

                for z in img_report.zones:
                    if z["ai_score"] >= 50:
                        all_zones.append({
                            **z,
                            "frame": i + 1,
                            "timestamp_sec": timestamp,
                            "region": f"Кадр {i + 1} / {z['region']}",
                        })
            finally:
                frame_path.unlink(missing_ok=True)

        if len(frame_scores) >= 2:
            variance = sum((s - statistics_mean(frame_scores)) ** 2 for s in frame_scores) / len(frame_scores)
            metrics["frame_score_variance"] = round(variance, 2)
            if variance < 50:
                findings.append({
                    "category": "Стабильность кадров",
                    "severity": "moderate",
                    "description": "AI-индекс стабилен между кадрами — возможна генерация",
                    "location": "Временная ось",
                })

        ai_score = statistics_mean(frame_scores) if frame_scores else 45.0

    category_scores = {
        "anatomy": int(ai_score * 0.9),
        "lighting": int(ai_score * 0.75),
        "geometry": int(ai_score * 0.8),
        "artifacts": int(ai_score),
        "metadata": 25 if probe else 40,
        "biometrics": int(ai_score * 0.85),
        "sync": 30 if metrics.get("has_audio") else 55,
    }

    metrics["findings_count"] = len(findings)
    metrics["zones_flagged"] = len(all_zones)

    return VideoForensicReport(
        ai_score=max(10, min(92, ai_score)),
        category_scores=category_scores,
        metrics=metrics,
        findings=findings,
        zones=all_zones[:12],
        frames=frames_data,
    )


def _ffprobe(path: Path) -> dict | None:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_streams", "-show_format", str(path),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return None
        import json
        data = json.loads(result.stdout)
        video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
        audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
        fmt = data.get("format", {})
        fps = 0.0
        if video.get("r_frame_rate") and "/" in video["r_frame_rate"]:
            n, d = video["r_frame_rate"].split("/")
            fps = round(int(n) / max(int(d), 1), 2)
        duration = float(fmt.get("duration", 0) or 0)
        return {
            "duration_sec": round(duration, 2),
            "width": video.get("width"),
            "height": video.get("height"),
            "fps": fps,
            "codec": video.get("codec_name", "?"),
            "has_audio": audio is not None,
        }
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return None


def _extract_frames(path: Path, count: int) -> list[Path]:
    frames: list[Path] = []
    tmpdir = Path(tempfile.mkdtemp(prefix="forensai_"))

    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return _extract_frames_ffmpeg(path, count, tmpdir)

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        indices = [int(total * i / max(count - 1, 1)) for i in range(count)] if total > count else list(range(min(count, total)))

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                continue
            out = tmpdir / f"frame_{idx}.jpg"
            cv2.imwrite(str(out), frame)
            frames.append(out)
        cap.release()
        return frames
    except ImportError:
        return _extract_frames_ffmpeg(path, count, tmpdir)
    except Exception:
        return _extract_frames_ffmpeg(path, count, tmpdir)


def _extract_frames_ffmpeg(path: Path, count: int, tmpdir: Path) -> list[Path]:
    frames: list[Path] = []
    try:
        pattern = str(tmpdir / "frame_%03d.jpg")
        subprocess.run(
            [
                "ffmpeg", "-i", str(path), "-vf", f"select='not(mod(n\\,{max(1, 30 // count)}))'",
                "-frames:v", str(count), "-q:v", "2", pattern, "-y",
            ],
            capture_output=True,
            timeout=30,
        )
        frames = sorted(tmpdir.glob("frame_*.jpg"))[:count]
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return frames
