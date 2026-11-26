"""Gom dữ liệu hạn mức Claude + Antigravity cho ve.py (chạy trên GitHub Actions)."""
import os, shutil, sys
from pathlib import Path


def main(ra: Path) -> None:
    ra.mkdir(parents=True, exist_ok=True)
    so = Path(os.environ.get("SO_DIR", "so"))
    for ten in ("claude.json", "antigravity.json"):
        if (so / ten).is_file():
            shutil.copy(so / ten, ra / ten)
            print("✓", ten)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "du-lieu"))
