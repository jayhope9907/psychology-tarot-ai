"""클로버 노트형 케이스 노트 · 관찰일지 · 상담 녹음 전사 (라이선스·백데이팅)."""
from __future__ import annotations

import json
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Any, BinaryIO, Dict, List, Optional

from app.db.database import get_connection, init_db
from app.services.association_licensing import feature_enabled
from app.services.persistence import ensure_user
from app.services.psych_timeline import record_event

ENTRY_CASE_NOTE = "case_note"
ENTRY_OBSERVATION = "observation_journal"
ENTRY_TRANSCRIPT = "session_transcript"

DISCLAIMER_KO = (
    "AI가 생성한 수련·교육용 기록입니다. 공식 의무기록·진단·처방을 대체하지 않으며, "
    "슈퍼바이저 검토를 전제로 합니다."
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_day(value: Optional[str]) -> date:
    if not value:
        return date.today()
    return date.fromisoformat(str(value)[:10])


def entitlements_allow_assistant(entitlements: Optional[Dict[str, Any]]) -> bool:
    if not entitlements:
        return False
    return feature_enabled("case_note_assistant", entitlements)


def entitlements_allow_backdate(entitlements: Optional[Dict[str, Any]]) -> bool:
    if not entitlements:
        return False
    return feature_enabled("case_note_backdate", entitlements)


def resolve_event_at(
    requested: Optional[str],
    entitlements: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """백데이팅 허용 시에만 과거 event_at 적용."""
    now = _utc_now()
    if not requested:
        return {"event_at": now, "backdated": False}
    if not entitlements_allow_backdate(entitlements):
        return {
            "event_at": now,
            "backdated": False,
            "backdate_blocked": True,
            "message_ko": "현재 라이선스에서는 백데이팅이 제한되어 오늘 날짜로 저장됩니다.",
        }
    day = _parse_day(requested)
    today = date.today()
    if day > today:
        day = today
    # keep time component noon local-ish UTC
    event_at = datetime(day.year, day.month, day.day, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    return {
        "event_at": event_at,
        "backdated": day < today,
        "backdate_blocked": False,
    }


def transcribe_audio(
    file_obj: BinaryIO,
    *,
    filename: str = "session.webm",
    client: Any = None,
    language: str = "ko",
) -> Dict[str, Any]:
    """OpenAI Whisper 전사. 키 없으면 교육용 스텁."""
    raw_name = filename or "session.webm"
    if client and getattr(client, "api_key", None):
        try:
            # OpenAI SDK expects a file-like with name
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            # wrap name for SDK
            class _Named:
                def __init__(self, buf, name):
                    self._buf = buf
                    self.name = name

                def read(self, *a, **k):
                    return self._buf.read(*a, **k)

            named = _Named(file_obj, raw_name)
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=named,
                language=language,
            )
            text = (getattr(result, "text", None) or str(result) or "").strip()
            if text:
                return {
                    "transcript": text,
                    "engine": "whisper-1",
                    "language": language,
                    "fallback": False,
                }
        except Exception as exc:  # pragma: no cover - network/model
            stub_reason = str(exc)[:160]
        else:
            stub_reason = "empty_transcript"
    else:
        stub_reason = "no_api_key"

    stub = (
        "[교육용 샘플 전사] "
        "내담자: 요즘 회사에서 마음이 많이 지치고, 집에 와서도 긴장이 안 풀려요. "
        "상담자: 지치고 긴장이 남는 순간이 특히 언제인지 조금 더 말씀해 주실 수 있을까요? "
        "내담자: 회의 끝나고 혼자 남았을 때, 제가 실수한 것 같다는 생각이 계속 나요. "
        "상담자: 그 생각이 올라올 때 몸에서는 어떤 감각이 느껴지나요?"
    )
    return {
        "transcript": stub,
        "engine": "offline_stub",
        "language": language,
        "fallback": True,
        "fallback_reason": stub_reason,
        "filename": raw_name,
    }


def _fallback_notes(transcript: str, *, session_date: str) -> Dict[str, Any]:
    snippet = re.sub(r"\s+", " ", (transcript or "").strip())[:220]
    return {
        "case_note": {
            "title": f"케이스 노트 · {session_date}",
            "session_date": session_date,
            "chief_complaint": "내담자가 언급한 최근 스트레스·긴장 (AI 요약)",
            "presenting_issues": [
                "업무·관계 장면에서의 긴장",
                "자기 비판적 사고 가능성",
            ],
            "session_summary": snippet or "전사 내용이 짧아 요약을 최소화했습니다.",
            "interventions": ["반영·명료화", "안전·페이스 조절", "다음 회기 초점 합의"],
            "homework": "하루 한 번, 긴장이 남는 장면을 2문장으로 기록하기",
            "risk_flags": [],
            "supervisor_questions": [
                "이번 회기에서 가장 중요한 감정은 무엇이었을까?",
                "다음 회기에 우선 다룰 주제는?",
            ],
        },
        "observation_journal": {
            "title": f"관찰일지 · {session_date}",
            "affect": "긴장·지침이 섞인 톤",
            "behavior": "말로 상황을 설명하며 자기 점검을 시도함",
            "cognition": "실수·평가에 대한 걱정이 반복될 수 있음",
            "environment": "직장 맥락이 두드러짐",
            "clinician_reflection": "서두르지 않고 안전감을 우선하는 태도가 도움 됨",
            "next_focus": "신체 감각과 자기비판 생각의 연결 탐색",
        },
    }


def generate_notes_from_transcript(
    transcript: str,
    *,
    client: Any = None,
    entitlements: Optional[Dict[str, Any]] = None,
    session_date: Optional[str] = None,
    client_label: str = "내담자",
) -> Dict[str, Any]:
    day = (session_date or date.today().isoformat())[:10]
    discipline = (entitlements or {}).get("discipline_label") or "수련·교육"
    base = _fallback_notes(transcript, session_date=day)

    if not client or not getattr(client, "api_key", None):
        out = {
            **base,
            "engine": "template_fallback",
            "disclaimer_ko": DISCLAIMER_KO,
            "discipline_label": discipline,
        }
        return out

    system = (
        "당신은 상담·임상심리·정신보건 수련용 케이스 노트 AI 어시스턴트입니다. "
        "의료 진단·처방·의무기록을 대체하지 않습니다. "
        "한국어 JSON만 출력하세요. 키: case_note, observation_journal. "
        "case_note 키: title, session_date, chief_complaint, presenting_issues(list), "
        "session_summary, interventions(list), homework, risk_flags(list), supervisor_questions(list). "
        "observation_journal 키: title, affect, behavior, cognition, environment, "
        "clinician_reflection, next_focus. "
        f"렌즈: {discipline}. 내담자 표기: {client_label}."
    )
    user = (
        f"회기일: {day}\n"
        f"상담 전사문:\n{transcript[:8000]}\n\n"
        "위 전사로 케이스 노트와 관찰일지를 작성하세요."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_tokens=1100,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        parsed = json.loads(content)
        case_note = parsed.get("case_note") or base["case_note"]
        obs = parsed.get("observation_journal") or base["observation_journal"]
        if isinstance(case_note, dict):
            case_note.setdefault("session_date", day)
        return {
            "case_note": case_note,
            "observation_journal": obs,
            "engine": "gpt-4o-mini",
            "disclaimer_ko": DISCLAIMER_KO,
            "discipline_label": discipline,
        }
    except Exception:
        return {
            **base,
            "engine": "template_fallback",
            "disclaimer_ko": DISCLAIMER_KO,
            "discipline_label": discipline,
        }


def save_journal_entry(
    user_id: str,
    entry_type: str,
    content: Dict[str, Any],
    *,
    event_at: Optional[str] = None,
) -> Dict[str, Any]:
    init_db()
    ensure_user(user_id)
    when = event_at or _utc_now()
    payload = dict(content)
    payload["event_at"] = when
    payload["saved_at"] = _utc_now()
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO journal_entries (user_id, entry_type, content_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, entry_type, json.dumps(payload, ensure_ascii=False), when),
        )
        conn.commit()
        entry_id = int(cur.lastrowid or 0)
    finally:
        conn.close()

    record_event(
        user_id,
        entry_type,
        {
            "journal_id": entry_id,
            "title": payload.get("title") or entry_type,
            "entry_type": entry_type,
            "summary": (payload.get("session_summary") or payload.get("clinician_reflection") or "")[:240],
            "backdated": bool(payload.get("backdated")),
            "non_diagnostic": True,
        },
        event_at=when,
        source_id=f"journal:{entry_type}:{entry_id}",
    )
    return {"id": entry_id, "entry_type": entry_type, "event_at": when, "content": payload}


def list_journal_entries(user_id: str, *, entry_type: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    try:
        if entry_type:
            rows = conn.execute(
                """
                SELECT id, user_id, entry_type, content_json, created_at
                FROM journal_entries
                WHERE user_id = ? AND entry_type = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, entry_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, user_id, entry_type, content_json, created_at
                FROM journal_entries
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        out = []
        for row in rows:
            out.append(
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "entry_type": row["entry_type"],
                    "created_at": row["created_at"],
                    "content": json.loads(row["content_json"] or "{}"),
                }
            )
        return out
    finally:
        conn.close()


def process_clover_pipeline(
    *,
    user_id: str,
    transcript: str,
    entitlements: Optional[Dict[str, Any]],
    client: Any = None,
    backdate_to: Optional[str] = None,
    client_label: str = "내담자",
    save: bool = True,
) -> Dict[str, Any]:
    """전사 → 케이스 노트·관찰일지 생성 → (옵션) 백데이트 저장."""
    if not entitlements_allow_assistant(entitlements):
        return {
            "ok": False,
            "error": "license_required",
            "message_ko": "케이스 노트 AI 어시스턴트는 Association License가 필요합니다.",
        }

    timing = resolve_event_at(backdate_to, entitlements)
    session_date = str(timing["event_at"])[:10]
    notes = generate_notes_from_transcript(
        transcript,
        client=client,
        entitlements=entitlements,
        session_date=session_date,
        client_label=client_label,
    )

    saved: Dict[str, Any] = {}
    if save:
        transcript_entry = save_journal_entry(
            user_id,
            ENTRY_TRANSCRIPT,
            {
                "title": f"상담 전사 · {session_date}",
                "transcript": transcript,
                "backdated": timing.get("backdated"),
                "disclaimer_ko": DISCLAIMER_KO,
            },
            event_at=timing["event_at"],
        )
        case_payload = dict(notes.get("case_note") or {})
        case_payload["backdated"] = timing.get("backdated")
        case_payload["disclaimer_ko"] = DISCLAIMER_KO
        case_entry = save_journal_entry(
            user_id,
            ENTRY_CASE_NOTE,
            case_payload,
            event_at=timing["event_at"],
        )
        obs_payload = dict(notes.get("observation_journal") or {})
        obs_payload["backdated"] = timing.get("backdated")
        obs_payload["disclaimer_ko"] = DISCLAIMER_KO
        obs_entry = save_journal_entry(
            user_id,
            ENTRY_OBSERVATION,
            obs_payload,
            event_at=timing["event_at"],
        )
        saved = {
            "transcript": transcript_entry,
            "case_note": case_entry,
            "observation_journal": obs_entry,
        }

    return {
        "ok": True,
        "transcript": transcript,
        "notes": notes,
        "timing": timing,
        "saved": saved,
        "capabilities": {
            "case_note_assistant": True,
            "case_note_backdate": entitlements_allow_backdate(entitlements),
        },
        "disclaimer_ko": DISCLAIMER_KO,
    }


def seed_backdated_case_notes_for_demo(
    user_id: str,
    entitlements: Optional[Dict[str, Any]],
    *,
    backfill_days: int = 14,
    scripts: Optional[List[Dict[str, str]]] = None,
) -> List[Dict[str, Any]]:
    """라이선스 온보딩 시 관찰일지·케이스 노트 자동 백데이팅."""
    if not entitlements_allow_assistant(entitlements):
        return []
    defaults = scripts or [
        {
            "day_offset": 12,
            "transcript": (
                "내담자: 요즘 아침에 일어나기가 힘들고 일이 손에 안 잡혀요. "
                "상담자: 하루 중 가장 무거운 시간은 언제인가요? "
                "내담자: 오전에 회의 들어가기 전이요."
            ),
        },
        {
            "day_offset": 5,
            "transcript": (
                "내담자: 가족한테 서운한 말이 자꾸 나와요. "
                "상담자: 그 말이 나오기 직전에 어떤 감정이 있었나요? "
                "내담자: 무시당한 느낌이요."
            ),
        },
    ]
    created = []
    today = date.today()
    for item in defaults:
        offset = int(item.get("day_offset") or 7)
        offset = min(offset, max(1, backfill_days))
        day = (today - timedelta(days=offset)).isoformat()
        result = process_clover_pipeline(
            user_id=user_id,
            transcript=item["transcript"],
            entitlements=entitlements,
            client=None,
            backdate_to=day,
            save=True,
        )
        if result.get("ok"):
            created.append({"day": day, "saved": result.get("saved")})
    return created
