"""Стилометрический анализатор: burstiness, перплексия-прокси и пунктуационный отпечаток.

Профессиональные детекторы (GPTZero и аналоги) опираются на два устойчивых сигнала:
  • burstiness — «взрывной» ритм человеческого текста: люди чередуют короткие и длинные
    предложения, ИИ держит ровную длину;
  • perplexity — предсказуемость: ИИ выбирает наиболее вероятные продолжения, поэтому
    его текст «гладкий» и низкоэнтропийный.

Здесь оба сигнала аппроксимируются без внешней языковой модели, плюс отдельно
детектируются пунктуационные привычки современных LLM (длинное тире, «фигурные» кавычки,
шаблоны-антитезы вида «это не X, а Y»). Модуль самодостаточен и не зависит от других
анализаторов, чтобы его можно было переиспользовать.
"""
from __future__ import annotations

import math
import re
import statistics
from collections import Counter
from dataclasses import dataclass, field

RU_STOPWORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все",
    "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы", "за", "бы", "по",
    "только", "ее", "мне", "было", "вот", "от", "меня", "еще", "нет", "о", "из", "ему",
    "теперь", "когда", "даже", "ну", "вдруг", "ли", "если", "уже", "или", "быть", "был",
    "него", "до", "вас", "нибудь", "опять", "уж", "вам", "ведь", "там", "потом", "себя",
    "ничего", "ей", "может", "они", "тут", "где", "есть", "надо", "ней", "для", "мы",
    "это", "этот", "эта", "эти", "также", "чтобы", "при", "об", "более",
}

EN_STOPWORDS = {
    "the", "and", "a", "an", "of", "to", "in", "is", "are", "was", "were", "be", "been",
    "for", "on", "with", "as", "by", "at", "this", "that", "these", "those", "it", "its",
    "from", "or", "but", "not", "have", "has", "had", "i", "you", "he", "she", "we", "they",
    "his", "her", "their", "our", "your", "my", "me", "him", "them", "us", "which", "who",
    "what", "when", "where", "how", "all", "can", "will", "would", "could", "should", "may",
    "do", "does", "did", "so", "if", "than", "then", "there", "here", "about", "into", "more",
}

# Шаблоны-антитезы — характерный «голос» современных LLM.
ANTITHESIS_PATTERNS = [
    re.compile(r"\bне\s+просто\b[^.!?\n]{0,60}?[,]?\s*\b(?:а|но)\b", re.IGNORECASE),
    re.compile(r"\bне\s+только\b[^.!?\n]{0,60}?[,]?\s*\bно\s+и\b", re.IGNORECASE),
    re.compile(r"\bэто\s+не\b[^.!?\n]{0,50}?[,—-]\s*это\b", re.IGNORECASE),
    re.compile(r"\bдело\s+не\s+в\b[^.!?\n]{0,50}?[,—-]\s*а\s+в\b", re.IGNORECASE),
    re.compile(r"\bit'?s\s+not\s+(?:just|about|only)\b[^.!?\n]{0,60}?[,—-]\s*it'?s\b", re.IGNORECASE),
    re.compile(r"\bnot\s+only\b[^.!?\n]{0,60}?\bbut\s+also\b", re.IGNORECASE),
    re.compile(r"\bnot\s+just\b[^.!?\n]{0,60}?\bbut\b", re.IGNORECASE),
]


@dataclass
class LinguisticReport:
    ai_score: float
    findings: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    score_parts: list[float] = field(default_factory=list)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 10]


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def burstiness(sentence_lengths: list[int]) -> float | None:
    """Коэффициент «взрывности» (σ−μ)/(σ+μ). Высокий → человек, около 0/ниже → ИИ."""
    if len(sentence_lengths) < 5:
        return None
    mean = statistics.mean(sentence_lengths)
    stdev = statistics.pstdev(sentence_lengths)
    denom = stdev + mean
    if denom == 0:
        return 0.0
    return (stdev - mean) / denom


def perplexity_proxy(words: list[str]) -> float | None:
    """Нормированная энтропия биграмм (0..1). Низкая → предсказуемо/«гладко» (ИИ)."""
    if len(words) < 40:
        return None
    bigrams = list(zip(words, words[1:]))
    counts = Counter(bigrams)
    total = len(bigrams)
    entropy = -sum((c / total) * math.log2(c / total) for c in counts.values())
    max_entropy = math.log2(total) if total > 1 else 1.0
    return entropy / max_entropy if max_entropy else 1.0


def _function_word_ratio(words: list[str]) -> float:
    if not words:
        return 0.0
    stop = RU_STOPWORDS | EN_STOPWORDS
    hits = sum(1 for w in words if w in stop)
    return hits / len(words)


def analyze_linguistics(text: str) -> LinguisticReport:
    findings: list[dict] = []
    score_parts: list[float] = []
    stats: dict = {}

    sentences = _sentences(text)
    words = _words(text)
    lengths = [len(s.split()) for s in sentences]

    # 1) Burstiness — ритмический отпечаток. По формуле (σ−μ)/(σ+μ) значение почти всегда
    # отрицательно; у живого текста ритм «рваный» (≈ −0.2…−0.45), у ИИ ровный (< −0.55).
    b = burstiness(lengths)
    if b is not None and len(lengths) >= 6:
        stats["burstiness"] = round(b, 3)
        if b <= -0.55:
            sev = "critical" if b <= -0.68 else "moderate"
            contribution = 70 if b <= -0.68 else 52
            score_parts.append(contribution)
            findings.append({
                "category": "Стилометрия: ритм",
                "severity": sev,
                "description": (
                    f"Низкая «взрывность» текста (burstiness {b:.2f}): предложения держат "
                    f"ровную длину, что характерно для генеративных моделей."
                ),
            })
    elif b is not None:
        stats["burstiness"] = round(b, 3)

    # 2) Perplexity-прокси — предсказуемость словосочетаний.
    pp = perplexity_proxy(words)
    if pp is not None:
        stats["perplexity_proxy"] = round(pp * 100, 1)
        if pp < 0.82:
            score_parts.append(min(85, (0.82 - pp) * 320 + 30))
            findings.append({
                "category": "Стилометрия: перплексия",
                "severity": "moderate",
                "description": (
                    f"Низкая перплексия (индекс {pp * 100:.0f}/100): словосочетания "
                    f"предсказуемы и однотипны — типичный признак ИИ-генерации."
                ),
            })

    # 3) Шаблоны-антитезы — «фирменный» приём LLM.
    antithesis_hits = []
    for pattern in ANTITHESIS_PATTERNS:
        for m in pattern.finditer(text):
            antithesis_hits.append(m.group(0).strip())
    if antithesis_hits:
        stats["антитез"] = len(antithesis_hits)
        score_parts.append(min(88, 45 + len(antithesis_hits) * 18))
        for snippet in antithesis_hits[:4]:
            findings.append({
                "category": "Стилометрия: шаблон-антитеза",
                "severity": "moderate" if len(antithesis_hits) < 2 else "critical",
                "description": "Конструкция-антитеза, типичная для ИИ-ассистентов",
                "location": f"«{snippet[:80]}»",
            })

    # 4) Пунктуационный отпечаток: длинное тире и «фигурные» кавычки без опечаток.
    char_count = max(len(text), 1)
    em_dash = text.count("—")
    em_dash_per_1k = em_dash / char_count * 1000
    curly_quotes = len(re.findall(r"[“”«»„]", text))
    stats["длинных_тире"] = em_dash
    if em_dash >= 3 and em_dash_per_1k >= 2.5 and len(sentences) >= 4:
        score_parts.append(min(55, 25 + em_dash_per_1k * 4))
        findings.append({
            "category": "Стилометрия: пунктуация",
            "severity": "minor",
            "description": (
                f"Повышенная плотность длинного тире (—) — {em_dash_per_1k:.1f} на 1000 знаков; "
                f"редкая привычка живого набора, частая у LLM."
            ),
        })
    if curly_quotes:
        stats["типографских_кавычек"] = curly_quotes

    stats["доля_служебных_слов"] = round(_function_word_ratio(words) * 100, 1)

    ai_score = statistics.mean(score_parts) if score_parts else 0.0
    return LinguisticReport(
        ai_score=round(ai_score, 1),
        findings=findings,
        stats=stats,
        score_parts=score_parts,
    )
