"""Сравнение двух экспертных отчётов."""


def compare_reports(a: dict, b: dict, *, label_a: str = "Файл A", label_b: str = "Файл B") -> dict:
    sa, sb = a.get("scores") or {}, b.get("scores") or {}
    ai_a, ai_b = int(sa.get("ai", 0)), int(sb.get("ai", 0))
    pl_a, pl_b = int(sa.get("plagiarism", 0)), int(sb.get("plagiarism", 0))
    auth_a = int(sa.get("authenticity") or max(0, 100 - ai_a))
    auth_b = int(sb.get("authenticity") or max(0, 100 - ai_b))

    verdict_match = a.get("verdict") == b.get("verdict")
    ai_delta = abs(ai_a - ai_b)
    pl_delta = abs(pl_a - pl_b)

    riskier = label_a if ai_a >= ai_b else label_b
    safer = label_b if riskier == label_a else label_a

    lines = [
        f"«{label_a}»: {a.get('verdict_label', '—')} (AI {ai_a}, подлинность {auth_a})",
        f"«{label_b}»: {b.get('verdict_label', '—')} (AI {ai_b}, подлинность {auth_b})",
    ]
    if verdict_match:
        lines.append("Вердикты совпадают.")
    else:
        lines.append("Вердикты различаются — материалы относятся к разным классам риска.")
    lines.append(f"Разница AI-индекса: {ai_delta} п.п. · плагиат: {pl_delta} п.п.")
    if ai_delta >= 25:
        lines.append(f"Существенный разрыв: выше риск у «{riskier}», ниже у «{safer}».")
    elif ai_delta >= 10:
        lines.append("Умеренное расхождение — стоит сопоставить улики по каждому файлу.")

    return {
        "verdict_match": verdict_match,
        "ai_delta": ai_delta,
        "plagiarism_delta": pl_delta,
        "higher_ai_risk": riskier,
        "lower_ai_risk": safer,
        "file_a": {"label": label_a, "verdict": a.get("verdict"), "verdict_label": a.get("verdict_label"), "scores": sa},
        "file_b": {"label": label_b, "verdict": b.get("verdict"), "verdict_label": b.get("verdict_label"), "scores": sb},
        "summary": " ".join(lines),
    }
