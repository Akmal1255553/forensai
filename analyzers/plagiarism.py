import re
from dataclasses import dataclass, field


def _split_sentences_with_offsets(text: str) -> list[dict]:
    pattern = re.compile(r"[^.!?…\n]+[.!?…]?|\n+", re.MULTILINE)
    segments = []
    for match in pattern.finditer(text):
        chunk = match.group().strip()
        if len(chunk) < 8:
            continue
        segments.append(
            {
                "start": match.start(),
                "end": match.end(),
                "text": chunk,
            }
        )
    if not segments and text.strip():
        segments.append({"start": 0, "end": len(text), "text": text.strip()})
    return segments


def _shingles(words: list[str], n: int = 5) -> set[str]:
    if len(words) < n:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _normalize_words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


@dataclass
class PlagiarismFinding:
    category: str
    severity: str
    description: str
    location: str = ""


@dataclass
class PlagiarismReport:
    score: float
    findings: list[PlagiarismFinding] = field(default_factory=list)
    segments: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "findings": [
                {
                    "category": f.category,
                    "severity": f.severity,
                    "description": f.description,
                    "location": f.location,
                }
                for f in self.findings
            ],
            "segments": self.segments,
            "stats": self.stats,
        }


def analyze_plagiarism(text: str) -> PlagiarismReport:
    findings: list[PlagiarismFinding] = []
    score_parts: list[float] = []
    segments_raw = _split_sentences_with_offsets(text)

    normalized = [(_normalize_words(s["text"]), i) for i, s in enumerate(segments_raw)]
    duplicate_pairs: list[tuple[int, int, float]] = []

    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            words_i, words_j = normalized[i][0], normalized[j][0]
            if len(words_i) < 4 or len(words_j) < 4:
                continue
            if words_i == words_j:
                duplicate_pairs.append((i, j, 1.0))
                continue
            sim = _jaccard(_shingles(words_i), _shingles(words_j))
            if sim >= 0.72:
                duplicate_pairs.append((i, j, sim))

    flagged: dict[int, list[str]] = {i: [] for i in range(len(segments_raw))}
    for i, j, sim in duplicate_pairs:
        flagged[i].append(f"Дубликат предложения #{j + 1} ({sim * 100:.0f}%)")
        flagged[j].append(f"Дубликат предложения #{i + 1} ({sim * 100:.0f}%)")

    if duplicate_pairs:
        score_parts.append(min(95, 40 + len(duplicate_pairs) * 12))
        for i, j, sim in duplicate_pairs[:6]:
            findings.append(
                PlagiarismFinding(
                    category="Повтор текста",
                    severity="critical" if sim >= 0.95 else "moderate",
                    description=f"Предложения #{i + 1} и #{j + 1} совпадают на {sim * 100:.0f}%",
                    location=f"«{segments_raw[i]['text'][:80]}…»",
                )
            )

    all_words = _normalize_words(text)
    word_counts: dict[str, int] = {}
    for w in all_words:
        if len(w) > 5:
            word_counts[w] = word_counts.get(w, 0) + 1

    overused = [(w, c) for w, c in word_counts.items() if c >= 5]
    if overused:
        score_parts.append(min(60, len(overused) * 8))
        findings.append(
            PlagiarismFinding(
                category="Шаблонная лексика",
                severity="minor",
                description=f"Перегруженные слова: {', '.join(w for w, _ in overused[:5])}",
            )
        )

    long_phrase_hits = 0
    words = all_words
    for n in (6, 8, 10):
        if len(words) < n * 2:
            continue
        phrases: dict[str, int] = {}
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i : i + n])
            phrases[phrase] = phrases.get(phrase, 0) + 1
        repeats = [p for p, c in phrases.items() if c > 1]
        if repeats:
            long_phrase_hits += len(repeats)
            for phrase in repeats[:3]:
                findings.append(
                    PlagiarismFinding(
                        category="Повтор фразы",
                        severity="moderate",
                        description=f"Фраза из {n} слов встречается несколько раз",
                        location=f"«{phrase[:70]}…»",
                    )
                )

    if long_phrase_hits:
        score_parts.append(min(80, 25 + long_phrase_hits * 10))

    segment_results = []
    for idx, seg in enumerate(segments_raw):
        pl_score = 0.0
        flags = flagged.get(idx, [])
        if flags:
            pl_score = min(95, 55 + len(flags) * 15)
        segment_results.append(
            {
                "index": idx + 1,
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "plagiarism_score": round(pl_score, 1),
                "plagiarism_flags": flags,
            }
        )

    score = statistics_mean(score_parts) if score_parts else 8.0
    score = max(5.0, min(95.0, score))

    return PlagiarismReport(
        score=score,
        findings=findings,
        segments=segment_results,
        stats={
            "предложений": len(segments_raw),
            "дубликатов": len(duplicate_pairs),
            "повторов_фраз": long_phrase_hits,
        },
    )


def statistics_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
