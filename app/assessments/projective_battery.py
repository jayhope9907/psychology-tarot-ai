"""임상심리 투영검사 배터리 — HTP·DAP·로orschach·TAT·KFD·SCT."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProjectiveResponseType(str, Enum):
    DRAWING = "drawing"
    INKBLOT = "inkblot"
    TAT_STORY = "tat_story"
    OPEN_TEXT = "open_text"


@dataclass(frozen=True)
class ProjectiveItem:
    instrument_id: str
    item_id: str
    prompt: str
    response_type: ProjectiveResponseType
    framing: str = ""
    clinical_note: str = ""
    stimulus_url: Optional[str] = None
    stimulus_svg: Optional[str] = None
    follow_up: Optional[str] = None
    stem: Optional[str] = None
    weight: float = 1.0


@dataclass(frozen=True)
class ProjectiveInstrument:
    instrument_id: str
    display_name: str
    school: str
    clinical_reference: str
    intro: str
    emoji: str
    items: List[ProjectiveItem] = field(default_factory=list)


INKBLOT_STIMULI = [
    {"item_id": "rorschach_01", "url": "/static/projective/inkblot-01.svg", "card": "Card I"},
    {"item_id": "rorschach_02", "url": "/static/projective/inkblot-02.svg", "card": "Card II"},
    {"item_id": "rorschach_03", "url": "/static/projective/inkblot-03.svg", "card": "Card III"},
    {"item_id": "rorschach_04", "url": "/static/projective/inkblot-04.svg", "card": "Card IV"},
    {"item_id": "rorschach_05", "url": "/static/projective/inkblot-05.svg", "card": "Card V"},
]

TAT_STIMULI = [
    {
        "item_id": "tat_01",
        "url": "/static/projective/tat-01.svg",
        "title": "창가의 사람",
        "scene_hint": "실루엣 — 창문을 바라보는 한 사람",
    },
    {
        "item_id": "tat_02",
        "url": "/static/projective/tat-02.svg",
        "title": "두 사람",
        "scene_hint": "실루엣 — 서로 마주 선 두 사람",
    },
    {
        "item_id": "tat_03",
        "url": "/static/projective/tat-03.svg",
        "title": "계단 위",
        "scene_hint": "실루엣 — 계단 위에 서 있는 사람",
    },
    {
        "item_id": "tat_04",
        "url": "/static/projective/tat-04.svg",
        "title": "어른과 아이",
        "scene_hint": "실루엣 — 어른과 아이",
    },
    {
        "item_id": "tat_05",
        "url": "/static/projective/tat-05.svg",
        "title": "혼자 앉은 사람",
        "scene_hint": "실루엣 — 의자에 앉아 있는 사람",
    },
    {
        "item_id": "tat_06",
        "url": "/static/projective/tat-06.svg",
        "title": "문 앞",
        "scene_hint": "실루엣 — 문 앞에 선 사람",
    },
]

SCT_STEMS = [
    ("sct_self", "나에게 '나'란 …", "자아·자기상에 대한 투사"),
    ("sct_mother", "어머니(또는 나를 키운 분)는 …", "양육·애착 대상 투사"),
    ("sct_stress", "힘들 때 나는 …", "스트레스 대처·방어 투사"),
    ("sct_men", "남자들은 …", "대상관계·성역할 투사"),
    ("sct_women", "여자들은 …", "대상관계·성역할 투사"),
    ("sct_future", "앞으로 나는 …", "미래·희망·불안 투사"),
]


def _htp_instrument() -> ProjectiveInstrument:
    items = [
        ProjectiveItem(
            "htp",
            "htp_house",
            "집(House)을 그려 주세요.",
            ProjectiveResponseType.DRAWING,
            framing="Buck HTP — 가정·안전·자아 경계를 상징합니다. 크기·문·창·굴뚝·울타리 등이 드러나면 좋아요.",
            clinical_note="집: Buck(1948) · Hammer(1958) 질적 지표",
            follow_up="이 집 그림에서 특별히 눈에 띄는 점이나 느낌을 적어 주세요.",
        ),
        ProjectiveItem(
            "htp",
            "htp_tree",
            "나무(Tree)를 그려 주세요.",
            ProjectiveResponseType.DRAWING,
            framing="생명력·성장·무의식적 에너지를 봅니다. 뿌리·줄기·가지·열매·상처 등을 자유롭게.",
            clinical_note="나무: Koch Baum · HTP tree sign",
            follow_up="이 나무가 지금 당신의 마음과 닮은 점은 무엇인가요?",
        ),
        ProjectiveItem(
            "htp",
            "htp_person",
            "사람(Person) 한 명을 그려 주세요.",
            ProjectiveResponseType.DRAWING,
            framing="자기상·대인관계·신체화를 봅니다. 성별·크기·표정·손·발·옷 등을 포함해 주세요.",
            clinical_note="사람: HTP person · Machover DAP 연계",
            follow_up="그 사람은 누구에 가깝나요? (자신·가족·타인 등)",
        ),
    ]
    return ProjectiveInstrument(
        instrument_id="htp",
        display_name="HTP — 집·나무·사람",
        school="투사검사 · Buck HTP",
        clinical_reference="Buck (1948); Hammer (1958)",
        intro="그림을 통해 무의식적 자아·가정·관계를 탐색하는 고전 투사검사입니다. 정답은 없으며, 느껴지는 대로 그리면 됩니다.",
        emoji="🏠",
        items=items,
    )


def _dap_instrument() -> ProjectiveInstrument:
    return ProjectiveInstrument(
        instrument_id="dap",
        display_name="DAP — 사람 그리기",
        school="투사검사 · Machover",
        clinical_reference="Machover (1949)",
        intro="사람 그림 한 장으로 자기상·정서·대인관계 특성을 살펴보는 투사검사입니다.",
        emoji="🧍",
        items=[
            ProjectiveItem(
                "dap",
                "dap_person",
                "사람 한 명 전신을 그려 주세요.",
                ProjectiveResponseType.DRAWING,
                framing="머리·몸·팔·다리가 보이도록. 연필·손가락 한 가지 도구만 사용해 주세요.",
                clinical_note="DAP: head emphasis, trunk, extremities, line quality",
                follow_up="그린 사람은 누구이며, 지금 어떤 기분일까요?",
            ),
        ],
    )


def _kfd_instrument() -> ProjectiveInstrument:
    return ProjectiveInstrument(
        instrument_id="kfd",
        display_name="KFD — 가족검사",
        school="투사검사 · Kinetic Family",
        clinical_reference="Burns & Kaufman (1970)",
        intro="가족 구성원이 함께 무언가를 하는 모습을 그려, 가족 역동·애착·역할을 탐색합니다.",
        emoji="👨‍👩‍👧",
        items=[
            ProjectiveItem(
                "kfd",
                "kfd_family",
                "가족(또는 가까운 사람들)이 함께 무언가를 하는 모습을 그려 주세요.",
                ProjectiveResponseType.DRAWING,
                framing="누가 있는지·무엇을 하는지·누가 가까운지 등이 드러나면 좋아요.",
                clinical_note="KFD: distance, action, omission, boundary",
                follow_up="그림 속에서 당신은 어디에 있나요? 누구와 가장 가깝나요?",
            ),
        ],
    )


def _rorschach_instrument() -> ProjectiveInstrument:
    items = [
        ProjectiveItem(
            "rorschach",
            spec["item_id"],
            f"이 잉크반점({spec['card']})에서 무엇이 보이나요?",
            ProjectiveResponseType.INKBLOT,
            framing="Rorschach — 형태·운동·색(해당 시)·위치를 자유 연상합니다. 여러 가지가 보이면 모두 적어 주세요.",
            clinical_note="Rorschach (1921) · 축약 5매 · 진단용 아님",
            stimulus_url=spec["url"],
        )
        for spec in INKBLOT_STIMULI
    ]
    return ProjectiveInstrument(
        instrument_id="rorschach",
        display_name="로르샤흐 — 잉크반점",
        school="투사검사 · Rorschach",
        clinical_reference="Rorschach (1921); Exner Comprehensive System (참고)",
        intro="모호한 잉크반점에 대한 연상을 통해 인지·정서·대처 양식을 탐색합니다. '무엇처럼 보이는지' 자유롭게 말해 주세요.",
        emoji="🦋",
        items=items,
    )


def _tat_instrument() -> ProjectiveInstrument:
    items = [
        ProjectiveItem(
            "tat",
            spec["item_id"],
            f"TAT — {spec['title']}",
            ProjectiveResponseType.TAT_STORY,
            framing=spec["scene_hint"],
            clinical_note="TAT: Murray(1935) · need-press · hero identification",
            stimulus_url=spec["url"],
            follow_up="무슨 일이 일어나고 있나요? · 주인공의 기분은? · 이후 어떻게 될까요?",
        )
        for spec in TAT_STIMULI
    ]
    return ProjectiveInstrument(
        instrument_id="tat",
        display_name="TAT — 주제채도검사",
        school="투사검사 · Murray TAT",
        clinical_reference="Murray (1935); Morgan & Murray",
        intro="모호한 그림 장면에 이야기를 붙여, 욕구·갈등·대인관계 패턴을 탐색합니다.",
        emoji="🖼️",
        items=items,
    )


def _sct_instrument() -> ProjectiveInstrument:
    items = [
        ProjectiveItem(
            "sct",
            item_id,
            stem,
            ProjectiveResponseType.OPEN_TEXT,
            framing=framing,
            clinical_note="SCT: Rotter · sentence completion projective",
            stem=stem,
        )
        for item_id, stem, framing in SCT_STEMS
    ]
    return ProjectiveInstrument(
        instrument_id="sct",
        display_name="SCT — 문장완성검사",
        school="투사검사 · SCT",
        clinical_reference="Rotter Incomplete Sentences; Holtzman (참고)",
        intro="미완성 문장을 이어 써, 억압된 갈등·태도·대상관계를 탐색합니다.",
        emoji="✍️",
        items=items,
    )


PROJECTIVE_INSTRUMENTS: Dict[str, ProjectiveInstrument] = {
    inst.instrument_id: inst
    for inst in [
        _htp_instrument(),
        _dap_instrument(),
        _kfd_instrument(),
        _rorschach_instrument(),
        _tat_instrument(),
        _sct_instrument(),
    ]
}


def all_projective_items() -> List[ProjectiveItem]:
    items: List[ProjectiveItem] = []
    for inst in PROJECTIVE_INSTRUMENTS.values():
        items.extend(inst.items)
    return items


def instrument_to_catalog(inst: ProjectiveInstrument) -> Dict[str, Any]:
    return {
        "instrument_id": inst.instrument_id,
        "display_name": inst.display_name,
        "school": inst.school,
        "clinical_reference": inst.clinical_reference,
        "intro": inst.intro,
        "emoji": inst.emoji,
        "item_count": len(inst.items),
        "items": [
            {
                "instrument_id": item.instrument_id,
                "item_id": item.item_id,
                "prompt": item.prompt,
                "response_type": item.response_type.value,
                "framing": item.framing,
                "clinical_note": item.clinical_note,
                "stimulus_url": item.stimulus_url,
                "follow_up": item.follow_up,
                "stem": item.stem,
            }
            for item in inst.items
        ],
    }


def projective_battery_catalog() -> Dict[str, Any]:
    instruments = [instrument_to_catalog(inst) for inst in PROJECTIVE_INSTRUMENTS.values()]
    total = sum(i["item_count"] for i in instruments)
    return {
        "site": "projective-assessment",
        "mode": "clinical_projective",
        "disclaimer": "본 검사는 임상심리 투사검사 기법을 참고한 자기탐색 도구이며, 진단·치료 결정을 대체하지 않습니다.",
        "instruments": instruments,
        "instrument_count": len(instruments),
        "total_items": total,
    }
