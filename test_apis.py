"""Проверка API-ключей без вывода секретов."""
import asyncio
import json
import sys

from dotenv import load_dotenv

load_dotenv()

from config import GEMINI_API_KEY, GEMINI_MODEL, OPENAI_API_KEY, OPENAI_MODEL


def mask(key: str) -> str:
    if not key:
        return "(пусто)"
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


async def test_gemini() -> dict:
    if not GEMINI_API_KEY:
        return {"ok": False, "error": "GEMINI_API_KEY не задан"}
    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        resp = model.generate_content(
            'Ответь JSON: {"status":"ok","provider":"gemini"}'
        )
        return {"ok": True, "model": GEMINI_MODEL, "preview": resp.text[:120]}
    except Exception as exc:
        return {"ok": False, "model": GEMINI_MODEL, "error": str(exc)}


async def test_openai() -> dict:
    if not OPENAI_API_KEY:
        return {"ok": False, "error": "OPENAI_API_KEY не задан"}
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": 'Ответь JSON: {"status":"ok","provider":"openai"}'}],
            max_tokens=50,
        )
        text = resp.choices[0].message.content or ""
        return {"ok": True, "model": OPENAI_MODEL, "preview": text[:120]}
    except Exception as exc:
        return {"ok": False, "model": OPENAI_MODEL, "error": str(exc)}


async def test_forensic_text() -> dict:
    from analyzers.forensic_engine import analyze_content

    sample = (
        "Важно отметить, что в современном мире искусственный интеллект "
        "играет ключевую роль. В заключение следует подчеркнуть комплексный подход."
    )
    report = await analyze_content(
        filename="test.txt",
        mime="text/plain",
        file_path=None,
        raw_text=sample,
    )
    return {
        "ok": report.get("analysis_mode") in {"gemini", "openai"},
        "mode": report.get("analysis_mode"),
        "verdict": report.get("verdict_label"),
        "confidence": report.get("confidence"),
    }


async def main():
    print("=== Проверка .env ===")
    print(f"GEMINI_API_KEY: {mask(GEMINI_API_KEY)}")
    print(f"OPENAI_API_KEY: {mask(OPENAI_API_KEY)}")
    print(f"GEMINI_MODEL:   {GEMINI_MODEL}")
    print(f"OPENAI_MODEL:   {OPENAI_MODEL}")
    print()

    gemini = await test_gemini()
    openai = await test_openai()
    forensic = await test_forensic_text()

    print("=== Gemini ===")
    print(json.dumps(gemini, ensure_ascii=False, indent=2))
    print()
    print("=== OpenAI ===")
    print(json.dumps(openai, ensure_ascii=False, indent=2))
    print()
    print("=== Forensic (текст через LLM) ===")
    print(json.dumps(forensic, ensure_ascii=False, indent=2))

    ok = gemini.get("ok") or openai.get("ok")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
