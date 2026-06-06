import re
import statistics
from collections import Counter
from dataclasses import dataclass, field


AI_CLICHES_RU = [
    "важно отметить",
    "в заключение",
    "рассмотрим подробнее",
    "следует отметить",
    "не секрет, что",
    "в современном мире",
    "на сегодняшний день",
    "таким образом",
    "безусловно",
    "несомненно",
    "как известно",
    "стоит подчеркнуть",
    "в целом",
    "подводя итог",
    "в данном контексте",
    "играет ключевую роль",
    "открывает новые горизонты",
    "уникальная возможность",
    "комплексный подход",
    "динамично развивающийся",
]

AI_CLICHES_EN = [
    "it's important to note",
    "in conclusion",
    "delve into",
    "it's worth noting",
    "in today's world",
    " furthermore",
    "moreover",
    "comprehensive",
    "robust",
    "leverage",
    "utilize",
    "facilitate",
    "paradigm",
    "holistic",
    "seamless",
    "cutting-edge",
    "game-changer",
    "dive deep",
    "at the end of the day",
    "needless to say",
]

AI_POLITENESS_RU = [
    "пожалуйста",
    "буду рад",
    "буду рада",
    "рад помочь",
    "рада помочь",
    "надеюсь, это поможет",
    "если у вас есть вопросы",
]

STRUCTURE_MARKERS = [
    r"^\s*\d+[\.\)]\s",
    r"^\s*[-•*]\s",
    r"^\s*[А-ЯA-Z][а-яa-z]+:\s",
]


@dataclass
class HeuristicFinding:
    category: str
    severity: str
    description: str
    location: str = ""


@dataclass
class HeuristicReport:
    ai_score: float
    findings: list[HeuristicFinding] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ai_score": round(self.ai_score, 1),
            "findings": [
                {
                    "category": f.category,
                    "severity": f.severity,
                    "description": f.description,
                    "location": f.location,
                }
                for f in self.findings
            ],
            "stats": self.stats,
        }

    def summary_text(self) -> str:
        lines = [f"Эвристический AI-score: {self.ai_score:.1f}/100"]
        for key, value in self.stats.items():
            lines.append(f"{key}: {value}")
        for f in self.findings:
            lines.append(f"[{f.severity}] {f.category}: {f.description}")
        return "\n".join(lines)


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 10]


def _word_ngram_repetition(text: str, n: int = 3) -> float:
    words = re.findall(r"\w+", text.lower())
    if len(words) < n * 3:
        return 0.0
    ngrams = [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]
    counts = Counter(ngrams)
    repeated = sum(c - 1 for c in counts.values() if c > 1)
    return repeated / max(len(ngrams), 1)


def _find_cliches(text: str, phrases: list[str]) -> list[tuple[str, str]]:
    lower = text.lower()
    found = []
    for phrase in phrases:
        start = 0
        while True:
            idx = lower.find(phrase, start)
            if idx == -1:
                break
            snippet = text[max(0, idx - 20) : idx + len(phrase) + 30].replace("\n", " ")
            found.append((phrase, snippet.strip()))
            start = idx + len(phrase)
    return found


def _sentence_length_uniformity(sentences: list[str]) -> float:
    if len(sentences) < 4:
        return 0.0
    lengths = [len(s.split()) for s in sentences]
    mean_len = statistics.mean(lengths)
    if mean_len == 0:
        return 0.0
    stdev = statistics.stdev(lengths) if len(lengths) > 1 else 0
    cv = stdev / mean_len
    if cv < 0.25:
        return 0.8
    if cv < 0.35:
        return 0.5
    return 0.1


def _structure_perfection(text: str) -> float:
    lines = text.splitlines()
    if len(lines) < 5:
        return 0.0
    structured = 0
    for line in lines:
        for pattern in STRUCTURE_MARKERS:
            if re.match(pattern, line):
                structured += 1
                break
    ratio = structured / len(lines)
    if ratio > 0.6:
        return 0.85
    if ratio > 0.4:
        return 0.55
    return 0.1


def _lexical_diversity(text: str) -> float:
    words = re.findall(r"\w+", text.lower())
    if len(words) < 50:
        return 0.0
    unique_ratio = len(set(words)) / len(words)
    if unique_ratio < 0.45:
        return 0.7
    if unique_ratio < 0.55:
        return 0.4
    return 0.1


def analyze_text_heuristics(text: str) -> HeuristicReport:
    findings: list[HeuristicFinding] = []
    score_parts: list[float] = []

    sentences = _split_sentences(text)
    word_count = len(re.findall(r"\w+", text))

    ru_cliches = _find_cliches(text, AI_CLICHES_RU)
    en_cliches = _find_cliches(text, AI_CLICHES_EN)
    all_cliches = ru_cliches + en_cliches

    if all_cliches:
        cliché_score = min(1.0, len(all_cliches) * 0.15)
        score_parts.append(cliché_score * 100)
        for phrase, snippet in all_cliches[:8]:
            findings.append(
                HeuristicFinding(
                    category="Стилистические маркеры ИИ",
                    severity="moderate" if len(all_cliches) < 3 else "critical",
                    description=f"Обнаружена клише-фраза «{phrase}»",
                    location=f"«...{snippet}...»",
                )
            )

    politeness = _find_cliches(text, AI_POLITENESS_RU)
    if len(politeness) >= 2:
        score_parts.append(35)
        findings.append(
            HeuristicFinding(
                category="Избыточная вежливость",
                severity="moderate",
                description=f"Найдено {len(politeness)} вежливых штампов, типичных для ИИ-ассистентов",
            )
        )

    uniformity = _sentence_length_uniformity(sentences)
    if uniformity > 0.4:
        score_parts.append(uniformity * 100)
        avg = statistics.mean(len(s.split()) for s in sentences) if sentences else 0
        findings.append(
            HeuristicFinding(
                category="Одинаковая длина предложений",
                severity="moderate" if uniformity < 0.7 else "critical",
                description=f"Предложения однородной длины (~{avg:.0f} слов), низкая вариативность",
            )
        )

    structure = _structure_perfection(text)
    if structure > 0.4:
        score_parts.append(structure * 100)
        findings.append(
            HeuristicFinding(
                category="Стерильная структура",
                severity="moderate",
                description="Документ чрезмерно структурирован: нумерация, списки, шаблонные заголовки",
            )
        )

    repetition = _word_ngram_repetition(text)
    if repetition > 0.08:
        score_parts.append(min(100, repetition * 400))
        findings.append(
            HeuristicFinding(
                category="Повторение мыслей",
                severity="moderate",
                description="Повторяющиеся словосочетания — возможная «вода» или перефразирование",
            )
        )

    diversity_penalty = _lexical_diversity(text)
    if diversity_penalty > 0.35:
        score_parts.append(diversity_penalty * 100)
        findings.append(
            HeuristicFinding(
                category="Низкое лексическое разнообразие",
                severity="minor",
                description="Ограниченный словарный запас относительно объёма текста",
            )
        )

    ai_score = statistics.mean(score_parts) if score_parts else 15.0
    ai_score = max(5.0, min(95.0, ai_score))

    stats = {
        "слов": word_count,
        "предложений": len(sentences),
        "клише": len(all_cliches),
        "средняя_длина_предложения": round(
            statistics.mean(len(s.split()) for s in sentences) if sentences else 0, 1
        ),
    }

    return HeuristicReport(ai_score=ai_score, findings=findings, stats=stats)


def heuristics_to_verdict(report: HeuristicReport) -> tuple[str, str, int]:
    score = report.ai_score
    if score >= 65:
        return "ai_generated", "Сгенерировано ИИ", int(score)
    if score >= 40:
        return "hybrid", "Гибрид/Редакция", int(score)
    return "human_created", "Создано человеком", int(100 - score)
