from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.services.assessment_selector import _conversation_text
from app.services.chat_session import ChatSessionState

CASE_PROFILES: Dict[str, Dict[str, Any]] = {
    "depressive": {
        "label": "우울·무기력형",
        "screening_note": "우울 증후군·적응장애(우울 기조) 스크리닝 해당 가능성",
        "instrument_ids": ("phq9", "behavioral", "micro_emotion"),
        "keywords": ("우울", "무기력", "의욕", "흥미", "공허", "슬픔", "기운", "피곤"),
        "future_vision": [
            "우울 강도와 일상 리듬 회복 가능성을 수치로 확인",
            "상담·병원 중 어디가 맞는지 확률로 안내",
            "작은 행동 활성화 목표를 함께 설계",
        ],
        "defense_points": [
            "만성화·퇴사·관계 단절로 번지는 패턴 조기 포착",
            "수면·식욕 악화 신호를 놓치지 않도록 경고",
            "자기 비난·무가치감 고리를 일찍 식별",
        ],
    },
    "anxiety": {
        "label": "불안·긴장형",
        "screening_note": "범불안·공황·사회불안 스크리닝 해당 가능성",
        "instrument_ids": ("gad7", "pss", "micro_emotion"),
        "keywords": ("불안", "초조", "긴장", "걱정", "두려움", "가슴", "떨림", "공포"),
        "future_vision": [
            "불안 강도와 촉발 상황을 구조화",
            "완화·노출·호흡 등 맞춤 대처 방향 제시",
            "정상 범주 대비 주의 수준을 명확히",
        ],
        "defense_points": [
            "회피 습관이 고착되기 전에 패턴 확인",
            "신체화(두근거림·호흡) 악화 조기 감지",
            "과각성·불면으로 이어지는 악순환 차단",
        ],
    },
    "stress_adjustment": {
        "label": "스트레스·적응형",
        "screening_note": "적응장애·번아웃·스트레스 관련 스크리닝 해당 가능성",
        "instrument_ids": ("pss", "isi", "micro_emotion"),
        "keywords": ("스트레스", "압박", "지침", "버거", "번아웃", "적응", "일", "직장"),
        "future_vision": [
            "스트레스 지수와 회복 리듬 파악",
            "생활·업무 경계 재설계 포인트 도출",
            "회복력 회복 로드맵 제시",
        ],
        "defense_points": [
            "번아웃·이직 충동 전에 소진 신호 포착",
            "수면·식사 리듬 붕괴 예방",
            "만성 피로가 우울로 전이되는 것 방지",
        ],
    },
    "relational": {
        "label": "관계·애착형",
        "screening_note": "애착 불안·관계 갈등·대인민감 스크리닝 해당 가능성",
        "instrument_ids": ("attachment_ecr", "psychodynamic", "micro_emotion"),
        "keywords": ("관계", "대인", "친구", "연인", "가족", "외로", "버림", "거리"),
        "future_vision": [
            "관계에서 반복되는 감정·패턴 가시화",
            "안전한 애착 회복 방향 탐색",
            "소통·경계 설정 목표 설정",
        ],
        "defense_points": [
            "관계 단절·집착·회피의 반복 고리 조기 발견",
            "고립·자책 악화 방지",
            "갈등 폭발 전 감정 트리거 파악",
        ],
    },
    "sleep": {
        "label": "수면·리듬형",
        "screening_note": "불면·수면리듬 장애 스크리닝 해당 가능성",
        "instrument_ids": ("isi", "phq9", "pss"),
        "keywords": ("잠", "수면", "불면", "깨", "악몽", "밤"),
        "future_vision": [
            "수면 질과 낮 기능 저하 연결 이해",
            "수면 위생·리듬 개선 우선순위 제시",
            "정서와 수면의 상호 영향 지도",
        ],
        "defense_points": [
            "불면이 우울·불안으로 번지는 것 예방",
            "야간 각성·낮 졸림 악순환 차단",
            "수면제 의존 전 생활습관 개입 포인트",
        ],
    },
    "trauma": {
        "label": "외상·경험형",
        "screening_note": "외상후 스트레스·복합 PTSD 스크리닝 해당 가능성",
        "instrument_ids": ("pcl5", "gad7", "micro_emotion"),
        "keywords": ("외상", "트라우마", "악몽", "플래시", "사고", "폭력", "상처"),
        "future_vision": [
            "외상 반응 강도와 안전 자원 평가",
            "전문 치료 연계 필요성 확률 안내",
            "안전·안정화 우선 계획 수립",
        ],
        "defense_points": [
            "회피·과각성 고착 조기 포착",
            "재경험·악몽 악화 전 전문 연계",
            "대처기제 무너짐(자해·중독) 위험 신호",
        ],
    },
    "self_esteem": {
        "label": "자존감·자기평가형",
        "screening_note": "자존감 저하·완벽주의·자기비난 스크리닝 해당 가능성",
        "instrument_ids": ("rses", "cbt_thought", "micro_emotion"),
        "keywords": ("자존감", "자신", "실패", "못난", "부족", "완벽"),
        "future_vision": [
            "자기 평가 패턴과 인지 왜곡 식별",
            "자기 수용·현실적 목표 설정",
            "성취와 자존감 분리 연습",
        ],
        "defense_points": [
            "자기비난·burnout 악순환 차단",
            "사회비교·열등감 고착 예방",
            "우울·불안으로의 전이 조기 감지",
        ],
    },
    "cognitive_behavioral": {
        "label": "사고·행동 패턴형",
        "screening_note": "인지 왜곡·회피·행동 활성화 저하 스크리닝 해당 가능성",
        "instrument_ids": ("cbt_thought", "behavioral", "gad7"),
        "keywords": ("생각", "반복", "미루", "피하", "왜곡", "항상", "최악"),
        "future_vision": [
            "자동적 사고·행동 실험 포인트 도출",
            "작은 행동 변화로 큰 감정 변화 설계",
            "문제 해결 가능성 재구성",
        ],
        "defense_points": [
            "회피·미루기 습관 고착 방지",
            "파국화·흑백사고 악화 차단",
            "무기력→우울 악순환 조기 개입",
        ],
    },
    "general_distress": {
        "label": "복합·탐색형",
        "screening_note": "복합 정서고통·원인 탐색 스크리닝 해당 가능성",
        "instrument_ids": ("micro_emotion", "phq9", "gad7"),
        "keywords": ("힘들", "답답", "모르", "복잡", "막막", "상담"),
        "future_vision": [
            "마음 지도를 그려 원인·강도 가시화",
            "우선순위 영역(정서·관계·수면) 선별",
            "맞춤 상담·검사 경로 제시",
        ],
        "defense_points": [
            "원인 불명의 고통이 만성화되는 것 방지",
            "혼자 버티다 번아웃·우울로 번지는 것 차단",
            "조기 스크리닝으로 치료 지연 예방",
        ],
    },
}

CASE_TYPE_LABELS = {
    "depressive": "우울·무기력 케이스",
    "anxiety": "불안·긴장 케이스",
    "stress_adjustment": "스트레스·적응 케이스",
    "relational": "관계·애착 케이스",
    "sleep": "수면·리듬 케이스",
    "trauma": "외상·경험 케이스",
    "self_esteem": "자존감·자기평가 케이스",
    "cognitive_behavioral": "사고·행동 패턴 케이스",
    "general_distress": "복합·탐색 케이스",
}


def _score_case(case_id: str, profile: Dict[str, Any], combined_text: str, instrument_rank: Dict[str, float]) -> float:
    score = 0.0
    for keyword in profile.get("keywords", ()):
        if keyword in combined_text:
            score += 1.4

    for instrument_id in profile.get("instrument_ids", ()):
        score += instrument_rank.get(instrument_id, 0.0) * 0.85

    if case_id == "general_distress":
        score = max(score, 0.35)

    return score


def _normalize_probabilities(scores: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
    if not scores:
        return []

    total = sum(value for _, value in scores)
    if total <= 0:
        uniform = round(100 / len(scores))
        return [
            {"case_id": case_id, "probability": uniform, "probability_label": f"{uniform}%"}
            for case_id, _ in scores
        ]

    rows: List[Dict[str, Any]] = []
    running = 0
    for index, (case_id, value) in enumerate(scores):
        if index == len(scores) - 1:
            pct = max(0, 100 - running)
        else:
            pct = max(1, int(round((value / total) * 100)))
            running += pct
        rows.append(
            {
                "case_id": case_id,
                "probability": pct,
                "probability_label": f"{pct}%",
            }
        )
    return rows


def build_case_preview(
    state: ChatSessionState,
    user_message: str = "",
    ranked_instruments: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    ranked_instruments = ranked_instruments or []

    text = _conversation_text(state, user_message)
    chief = (state.phase_notes.get("chief_complaint") or "").lower()
    combined = f"{text}\n{chief}"
    instrument_rank = {row["instrument_id"]: row["score"] for row in ranked_instruments}

    raw_scores: List[Tuple[str, float]] = []
    for case_id, profile in CASE_PROFILES.items():
        raw_scores.append((case_id, _score_case(case_id, profile, combined, instrument_rank)))

    raw_scores.sort(key=lambda item: (-item[1], item[0]))
    prob_rows = _normalize_probabilities(raw_scores[:4])

    hypotheses: List[Dict[str, Any]] = []
    for prob in prob_rows:
        case_id = prob["case_id"]
        profile = CASE_PROFILES[case_id]
        hypotheses.append(
            {
                "case_id": case_id,
                "case_type": CASE_TYPE_LABELS.get(case_id, profile["label"]),
                "label": profile["label"],
                "probability": prob["probability"],
                "probability_label": prob["probability_label"],
                "screening_note": profile["screening_note"],
                "confidence_band": _confidence_band(prob["probability"]),
            }
        )

    primary = hypotheses[0]
    secondary = hypotheses[1:] if len(hypotheses) > 1 else []
    primary_profile = CASE_PROFILES[primary["case_id"]]
    future_vision = list(primary_profile["future_vision"])
    defense_points = list(primary_profile["defense_points"])

    if secondary and secondary[0]["probability"] >= 20:
        sec_profile = CASE_PROFILES[secondary[0]["case_id"]]
        future_vision = list(dict.fromkeys(future_vision + sec_profile["future_vision"][:1]))[:4]
        defense_points = list(dict.fromkeys(defense_points + sec_profile["defense_points"][:1]))[:4]

    chief_display = state.phase_notes.get("chief_complaint") or "지금까지 나눈 마음"

    return {
        "primary_case_type": primary["case_type"],
        "primary_label": primary["label"],
        "classification_summary": (
            f"라포 형성 후 초기 분류: {primary['case_type']}에 가장 가깝게 보입니다 "
            f"(참고 확률 {primary['probability_label']}). "
            f"아래 검사로 {primary['screening_note']}을 더 정밀하게 확인할 수 있어요."
        ),
        "chief_complaint": chief_display,
        "hypotheses": hypotheses,
        "comorbidity_note": _comorbidity_note(hypotheses),
        "future_vision": future_vision,
        "defense_points": defense_points,
        "value_proposition": {
            "headline": "이 검사로 그릴 수 있는 미래",
            "subheadline": "지금의 고통을 데이터로 바꾸면, 다음 한 걸음이 보입니다.",
            "prevention_headline": "함께 지켜낼 수 있는 것",
            "prevention_subheadline": "조기에 알아차리면, 혼자 버티다 무너지는 패턴을 막을 수 있어요.",
        },
        "disclaimer": (
            "※ 위 내용은 대화 기반 사전 분류·스크리닝 참고이며 의료 진단이 아닙니다. "
            "검사 후 확률과 권장 경로가 업데이트됩니다."
        ),
        "preview_confidence": _preview_confidence(state, combined),
    }


def _confidence_band(probability: int) -> str:
    if probability >= 45:
        return "높은 참고 가능성"
    if probability >= 25:
        return "중간 참고 가능성"
    return "탐색·확인 필요"


def _comorbidity_note(hypotheses: List[Dict[str, Any]]) -> str:
    if len(hypotheses) < 2:
        return ""
    second = hypotheses[1]
    if second["probability"] < 18:
        return ""
    return (
        f"{second['label']} 요소도 {second['probability_label']} 정도 함께 보여, "
        "복합적 케이스일 수 있어요. 패키지 검사로 영역별로 나눠 확인합니다."
    )


def _preview_confidence(state: ChatSessionState, combined_text: str) -> str:
    turns = max(1, state.turn_count)
    richness = min(1.0, len(combined_text) / 120.0)
    if turns >= 2 and richness >= 0.45:
        return "medium"
    if turns >= 2:
        return "low"
    return "exploratory"
