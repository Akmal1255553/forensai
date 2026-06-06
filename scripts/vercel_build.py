"""Copy static assets to public/ for Vercel CDN serving."""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
PUBLIC = ROOT / "public"


def main() -> None:
    PUBLIC.mkdir(exist_ok=True)
    shutil.copy2(STATIC / "index.html", PUBLIC / "index.html")
    for name in ("css", "js"):
        src = STATIC / name
        if src.is_dir():
            shutil.copytree(src, PUBLIC / "static" / name, dirs_exist_ok=True)


if __name__ == "__main__":
    main()
