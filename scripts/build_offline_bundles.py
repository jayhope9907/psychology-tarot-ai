"""Build static offline bundles for picto, tarot, and counseling."""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.counsel_offline import counsel_offline_bundle  # noqa: E402
from app.services.picto_vocabulary import picto_offline_bundle  # noqa: E402
from app.services.tarot import list_deck_catalog  # noqa: E402

THREE_URL = "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"
THREE_OUT = ROOT / "static" / "js" / "vendor" / "three.min.js"


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {path}")


def ensure_three_js() -> None:
    THREE_OUT.parent.mkdir(parents=True, exist_ok=True)
    if THREE_OUT.exists() and THREE_OUT.stat().st_size > 100_000:
        print(f"Skip three.js (exists): {THREE_OUT}")
        return
    try:
        print(f"Downloading three.js -> {THREE_OUT}")
        with urllib.request.urlopen(THREE_URL, timeout=60) as resp:
            THREE_OUT.write_bytes(resp.read())
    except Exception as exc:
        print(f"Warning: three.js download skipped ({exc}). CDN fallback will be used online.")


def main() -> None:
    picto = ROOT / "static" / "picto-catalog.bundle.json"
    write_json(picto, picto_offline_bundle())
    print(f"  picto items: {len(picto_offline_bundle()['items'])}")

    tarot = ROOT / "static" / "tarot-deck.bundle.json"
    deck = list_deck_catalog()
    deck["bundle_version"] = 1
    write_json(tarot, deck)
    print(f"  tarot cards: {deck.get('total')}")

    counsel = ROOT / "static" / "counsel-offline.bundle.json"
    write_json(counsel, counsel_offline_bundle())
    print(f"  counsel rules: {len(counsel_offline_bundle()['rules'])}")

    ensure_three_js()


if __name__ == "__main__":
    main()
