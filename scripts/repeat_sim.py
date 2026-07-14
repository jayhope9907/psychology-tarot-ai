"""Multi-turn chat repetition simulator."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.chat_session import ChatSessionState, clear_sessions
from app.services.chat_stream import run_chat_turn


async def varied_stream(messages, max_tokens, client, assessment_response=None):
    user = messages[-1]["content"] if messages else ""
    if isinstance(user, list):
        user = " ".join(
            part.get("text", "") for part in user if isinstance(part, dict) and part.get("type") == "text"
        )
    snippet = (user or "")[:24]
    yield f"말씀하신 '{snippet}' 부분이 마음에 남아요. "
    yield "그때 몸이나 마음에서 가장 먼저 느껴진 반응은 무엇이었나요?"


async def run_scenario(name: str, client, stream_fn=None):
    clear_sessions()
    state = ChatSessionState(user_id=f"repeat-{name}")
    msgs = [
        "요즘 직장 때문에 많이 힘들어요",
        "상사한테 계속 깨져서 자신감이 떨어져요",
        "네 맞아요 그래서 출근하기가 무서워요",
        "주말에도 불안해서 쉬지를 못해요",
    ]
    rows = []
    prev = ""
    for m in msgs:
        text = ""
        meta = {}
        async for ev in run_chat_turn(state, m, client=client, stream_fn=stream_fn):
            if ev["event"] == "done":
                text = ev["data"].get("assistant_message", "")
                meta = ev["data"]
        dup = text.strip() == prev.strip() if prev else False
        rows.append(
            {
                "user": m,
                "bot": text,
                "phase": (meta.get("counseling_phase") or {}).get("phase"),
                "exact_dup_prev": dup,
            }
        )
        prev = text
    return {"scenario": name, "turns": rows}


async def main():
    results = []
    results.append(await run_scenario("no_api", client=None, stream_fn=None))
    results.append(await run_scenario("fake_llm", client=object(), stream_fn=varied_stream))
    out = ROOT / "_repeat_test.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    for block in results:
        print("===", block["scenario"], "===")
        for i, row in enumerate(block["turns"], 1):
            flag = " DUP" if row["exact_dup_prev"] else ""
            print(f"T{i} [{row['phase']}]{flag}")
            print("U:", row["user"])
            print("B:", row["bot"][:180])
            print()


if __name__ == "__main__":
    asyncio.run(main())
