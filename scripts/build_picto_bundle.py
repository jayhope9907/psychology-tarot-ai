"""Generate static/picto-catalog.bundle.json from picto_vocabulary (single source of truth)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.picto_vocabulary import picto_offline_bundle  # noqa: E402


def main() -> None:
    out = ROOT / "static" / "picto-catalog.bundle.json"
    bundle = picto_offline_bundle()
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(bundle.get('items', []))} items)")


if __name__ == "__main__":
    main()
