"""검사 전·중·후 레이어드 디렉팅 + 자기효능감 키우기 (교육·자기성찰용)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.assessments import ALL_INSTRUMENTS, INSTRUMENT_PROFILES
from app.assessments.user_voice import INSTRUMENT_USER_VOICE, user_instrument_title

DISCLAIMER = "진단·평가가 아니라, 스스로 알아차리고 작은 힘을 키우는 연습이에요."

LAYER_IDS = ("arrival", "orient", "progress", "complete", "efficacy")

LAYER_LABELS = {
    "arrival": "왜 보나요",
    "orient": "어떻게 답하나요",
    "progress": "함께 가는 중",
    "complete": "방금 살펴본 것",
    "efficacy": "작은 힘으로 키우기",
}

# 도메인군별 효능감 시드 (mastery 경험의 작은 버전)
_DOMAIN_EFFICACY: Dict[str, Dict[str, Any]] = {
    "mood": {
        "strength_prompt": "최근 며칠, 나를 조금이나마 버티게 해준 순간 하나",
        "seeds": (
            "오늘 물 한 잔·호흡 3번처럼 ‘내가 나를 챙긴’ 신호 하나 남기기",
            "힘든 감정을 한 단어로만 이름 붙여 보기",
            "5분만이라도 몸을 움직이거나 창밖을 보기",
        ),
    },
    "anxiety": {
        "strength_prompt": "불안해도 어쨌든 해낸 일 하나",
        "seeds": (
            "걱정 목록을 ‘지금 할 수 있는 것 / 내일’로 두 칸만 나누기",
            "몸이 긴장하면 발바닥·손바닥에 3초 의식 두기",
            "불안을 ‘신호가 왔다’고만 한 문장으로 적기",
        ),
    },
    "self": {
        "strength_prompt": "나는 이런 면에서 괜찮은 편이다 — 작은 근거 하나",
        "seeds": (
            "오늘 잘한 일·버틴 일을 한 줄로 적기",
            "자책 문장을 ‘그래도 …’로 한 번만 고쳐 보기",
            "거울이나 메모에 ‘지금도 배우고 있는 중’ 한 줄",
        ),
    },
    "sleep": {
        "strength_prompt": "잠이 완벽하지 않아도, 휴식에 도움 된 선택 하나",
        "seeds": (
            "취침 전 화면 10분만 줄여 보기",
            "침대에서 ‘오늘을 닫는’ 문장 하나 말하기",
            "낮에 햇빛·걷기를 짧은 루틴으로 넣기",
        ),
    },
    "relation": {
        "strength_prompt": "관계에서 내가 지켜 낸 경계·친절 하나",
        "seeds": (
            "거절·요청을 한 문장으로만 연습해 보기",
            "상대에게 고마웠던 점 하나를 구체적으로 떠올리기",
            "대화 후 ‘나는 이런 감정이었다’ 기록 한 줄",
        ),
    },
    "language": {
        "strength_prompt": "말·글로 나를 조금 더 분명히 한 경험 하나",
        "seeds": (
            "감정·필요를 한 문장으로만 써 보기",
            "말하지 못한 말을 메모·그림으로 남기기",
            "속마음 말투를 다정한 버전으로 한 번만 바꿔 보기",
        ),
    },
    "body": {
        "strength_prompt": "몸이 보내는 신호를 알아차린 순간 하나",
        "seeds": (
            "어깨·턱 긴장을 풀고 숨 네 번 쉬기",
            "몸 신호에 이름을 붙인 뒤 물·스트레칭 중 하나 하기",
            "‘몸이 쉴 권리’를 문구로 메모해 두기",
        ),
    },
    "default": {
        "strength_prompt": "이 주제를 살펴본 것만으로도 용기예요. 작은 근거 하나",
        "seeds": (
            "오늘 나를 돌본 행동·선택을 한 가지만 인정하기",
            "다음 24시간 ‘아주 작은 성공’ 하나를 미리 정하기",
            "힘들 때 쓸 문장: ‘지금은 한 걸음만’",
        ),
    },
}

_DOMAIN_BUCKET: Dict[str, str] = {
    "clinical_mood": "mood",
    "clinical_anxiety": "anxiety",
    "clinical_sleep": "sleep",
    "clinical_stress": "anxiety",
    "clinical_trauma": "mood",
    "clinical_dass": "mood",
    "wellbeing_self": "self",
    "wellbeing_positive": "self",
    "attachment": "relation",
    "language_psychology": "language",
    "anxiety_spectrum": "anxiety",
    "anger_hostility": "relation",
    "impulse_control": "self",
    "psychosis_spectrum": "mood",
}


def _bucket_for(instrument_id: str) -> str:
    profile = INSTRUMENT_PROFILES.get(instrument_id) or {}
    domain = str(profile.get("domain") or "")
    if domain in _DOMAIN_BUCKET:
        return _DOMAIN_BUCKET[domain]
    if "sleep" in domain or instrument_id in {"isi"}:
        return "sleep"
    if instrument_id in {"rses", "self_efficacy_gse", "mbti_preference"}:
        return "self"
    if instrument_id in {"attachment_ecr", "communication_assertiveness"}:
        return "relation"
    if instrument_id.startswith(("verbal_", "narrative_", "self_talk", "alexithymia", "metaphor_", "pragmatic_", "expressive_")):
        return "language"
    if instrument_id in {"somatic_probe", "phq15", "isi"}:
        return "body"
    if "anxiety" in domain or instrument_id in {"gad7", "panic_probe", "social_anxiety_probe", "phobia_specific"}:
        return "anxiety"
    if instrument_id in {"phq9", "pcl5", "dass_depression"}:
        return "mood"
    return "default"


def _progress_line(item_index: int, total_items: int) -> str:
    if total_items <= 1:
        return "한 가지만 보면 돼요. 천천히요."
    ratio = item_index / max(total_items - 1, 1)
    if item_index <= 0:
        return "첫 문항이에요. 느낌에 가까운 쪽만 골라도 충분해요."
    if ratio < 0.45:
        return f"{item_index + 1}/{total_items} — 잘 오고 있어요. 정답은 없고, 지금 감각이면 됩니다."
    if ratio < 0.85:
        return f"{item_index + 1}/{total_items} — 절반을 넘었어요. 피곤하면 넘어가도 괜찮아요."
    return f"{item_index + 1}/{total_items} — 거의 다 왔어요. 마지막도 편하게요."


def _complete_line(instrument_id: str, score: Optional[Dict[str, Any]]) -> str:
    title = user_instrument_title(instrument_id) or instrument_id
    hint = (score or {}).get("severity_hint")
    if hint in {"low", "minimal", "healthy", "moderate", "mild", "minimal_elevated"}:
        soft = {
            "low": "스스로에게 꽤 엄격했을 수 있어요. 그래도 여기까지 살펴본 건 이미 돌봄이에요.",
            "minimal": "지금 신호가 비교적 가벼운 편으로 보여요. 작은 리듬을 지키는 연습이 좋아요.",
            "healthy": "스스로를 비교적 따뜻하게 보는 힘이 느껴져요. 그 힘을 조금 더 키워 볼까요.",
            "moderate": "중간쯤의 무게가 느껴질 수 있어요. 한 번에 고치지 않아도 됩니다.",
            "mild": "살짝 무거운 느낌이 있을 수 있어요. 진단이 아니라 ‘알아차림’이에요.",
            "minimal_elevated": "가벼운 상승이 보일 수 있어요. 작은 돌봄으로 조절해 볼 여지예요.",
        }.get(str(hint), "")
        if soft:
            return f"「{title}」을(를) 함께 봤어요. {soft}"
    return f"「{title}」을(를) 끝까지(또는 여기까지) 살펴봤어요. 그 자체로 이미 자기돌봄이에요."


def build_efficacy_card(instrument_id: str, score: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    bucket = _bucket_for(instrument_id)
    block = _DOMAIN_EFFICACY.get(bucket) or _DOMAIN_EFFICACY["default"]
    title = user_instrument_title(instrument_id) or "마음 살펴보기"
    affirmations = [
        "검사를 ‘통과’하는 게 목표가 아니에요. 알아차린 순간이 이미 효능감이에요.",
        "작은 성공을 쌓을수록, ‘나는 할 수 있다’는 감각이 자랍니다.",
        "완벽하지 않아도, 한 걸음을 고르는 힘이 자기효능감이에요.",
    ]
    # rses / gse: lean into mastery language
    if instrument_id in {"rses", "self_efficacy_gse"} or bucket == "self":
        affirmations.insert(
            0,
            "자신감은 큰 성취만이 아니라, ‘내가 나를 도운 작은 증거’에서 자랍니다.",
        )
    return {
        "layer": "efficacy",
        "label": LAYER_LABELS["efficacy"],
        "headline": "자기효능감 · 작은 힘으로",
        "instrument_id": instrument_id,
        "instrument_title": title,
        "strength_prompt": block["strength_prompt"],
        "seeds": list(block["seeds"]),
        "affirmation": affirmations[0],
        "affirmations": affirmations[:3],
        "cta_chat": "대화에서 이 힘을 더 키워 보기",
        "cta_next": "다른 주제도 같은 방식으로",
        "how_to": "아래에서 오늘 실천할 씨앗 하나를 고르면, 그것이 ‘할 수 있다’는 증거가 됩니다.",
        "disclaimer": DISCLAIMER,
        "severity_hint": (score or {}).get("severity_hint"),
    }


def build_assessment_directing(
    instrument_id: str,
    *,
    item_index: int = 0,
    total_items: Optional[int] = None,
    score: Optional[Dict[str, Any]] = None,
    completed: bool = False,
) -> Dict[str, Any]:
    """문항 진행에 맞춰 5레이어 디렉팅 블록을 만든다."""
    voice = INSTRUMENT_USER_VOICE.get(instrument_id) or {}
    profile = INSTRUMENT_PROFILES.get(instrument_id) or {}
    title = user_instrument_title(instrument_id) or profile.get("display_name") or instrument_id
    instrument = ALL_INSTRUMENTS.get(instrument_id)
    if total_items is None:
        total_items = len(instrument.items()) if instrument else 1
    total_items = max(int(total_items or 1), 1)
    item_index = max(0, min(int(item_index), total_items - 1))

    arrival = {
        "layer": "arrival",
        "label": LAYER_LABELS["arrival"],
        "title": title,
        "body": voice.get("intro")
        or f"「{title}」로 요즘 마음을 가볍게 들여다볼게요.",
        "focus": profile.get("focus") or "",
    }
    orient = {
        "layer": "orient",
        "label": LAYER_LABELS["orient"],
        "body": voice.get("example")
        or "맞는 느낌만 골라 주세요. 정답은 없고, 지금은 넘어가도 괜찮아요.",
        "safety": "부담되면 건너뛰어도 됩니다. 급할 필요 없어요.",
    }
    progress = {
        "layer": "progress",
        "label": LAYER_LABELS["progress"],
        "body": _progress_line(item_index, total_items),
        "item_index": item_index,
        "total_items": total_items,
        "pct": int(round(100 * (item_index + (1 if completed else 0)) / total_items)),
    }
    complete = {
        "layer": "complete",
        "label": LAYER_LABELS["complete"],
        "body": _complete_line(instrument_id, score if completed else None),
        "ready": completed,
    }
    efficacy = build_efficacy_card(instrument_id, score if completed else None)

    # Active layer for UI
    if completed:
        active = "efficacy"
    elif item_index == 0:
        active = "orient"
    else:
        active = "progress"

    layers: List[Dict[str, Any]] = [arrival, orient, progress, complete, efficacy]
    return {
        "instrument_id": instrument_id,
        "active_layer": active,
        "layer_ids": list(LAYER_IDS),
        "layer_labels": dict(LAYER_LABELS),
        "layers": {L["layer"]: L for L in layers},
        "stack": layers,
        "rail": [
            {
                "id": lid,
                "label": LAYER_LABELS[lid],
                "state": (
                    "done"
                    if (
                        (lid == "arrival")
                        or (lid == "orient" and item_index > 0)
                        or (lid == "progress" and completed)
                        or (lid == "complete" and completed)
                        or (lid == "efficacy" and completed)
                    )
                    else ("active" if lid == active else "todo")
                ),
            }
            for lid in LAYER_IDS
        ],
        "disclaimer": DISCLAIMER,
        "coach_line": (
            efficacy["affirmation"]
            if completed
            else (orient["body"] if item_index == 0 else progress["body"])
        ),
    }


def build_submit_directing_payload(
    instrument_id: str,
    *,
    item_index: int,
    total_items: int,
    score: Optional[Dict[str, Any]],
    instrument_complete: bool,
) -> Dict[str, Any]:
    directing = build_assessment_directing(
        instrument_id,
        item_index=item_index,
        total_items=total_items,
        score=score,
        completed=instrument_complete,
    )
    out: Dict[str, Any] = {"directing": directing}
    if instrument_complete:
        out["efficacy"] = directing["layers"]["efficacy"]
    return out
