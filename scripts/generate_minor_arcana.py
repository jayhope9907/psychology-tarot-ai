"""One-off generator for minor_arcana.json (56 cards)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "app" / "data" / "minor_arcana.json"

SUITS = {
    "wands": {
        "name_en": "Wands",
        "name_ko": "지팡이",
        "file_prefix": "Wands",
        "symbol": "🜂",
        "keywords": ["열정", "행동", "창의"],
        "theme": "의욕·실행·에너지",
        "gradient": ["#8b2500", "#ff6b35"],
        "archetype_base": "The Creator",
    },
    "cups": {
        "name_en": "Cups",
        "name_ko": "컵",
        "file_prefix": "Cups",
        "symbol": "🏆",
        "keywords": ["감정", "관계", "직관"],
        "theme": "마음·교감·수용",
        "gradient": ["#1d3557", "#457b9d"],
        "archetype_base": "The Lover",
    },
    "swords": {
        "name_en": "Swords",
        "name_ko": "검",
        "file_prefix": "Swords",
        "symbol": "⚔",
        "keywords": ["생각", "결정", "갈등"],
        "theme": "사고·경계·진실",
        "gradient": ["#2b2d42", "#8d99ae"],
        "archetype_base": "The Thinker",
    },
    "pentacles": {
        "name_en": "Pentacles",
        "name_ko": "펜타클",
        "file_prefix": "Pents",
        "symbol": "🪙",
        "keywords": ["현실", "몸", "재정"],
        "theme": "생활·안정·돌봄",
        "gradient": ["#1b4332", "#52b788"],
        "archetype_base": "The Builder",
    },
}

RANKS = [
    ("ace", 1, "에이스", "Ace", "시작", "새로운 {theme}의 씨앗이 보입니다.", "시작이 막히거나 의욕이 약해질 수 있어요."),
    ("two", 2, "2", "Two", "선택", "두 갈래 사이에서 균형을 찾는 때예요.", "우유부단함이나 회피가 느껴질 수 있어요."),
    ("three", 3, "3", "Three", "확장", "협력과 확장의 에너지가 흐릅니다.", "소통 부족이나 산만함이 보일 수 있어요."),
    ("four", 4, "4", "Four", "안정", "기반을 다지고 쉬어 가도 좋아요.", "답답함·정체감이 올 수 있어요."),
    ("five", 5, "5", "Five", "갈등", "마찰 속에서 배우는 지점이 있어요.", "긴장이 길어지면 거리를 두세요."),
    ("six", 6, "6", "Six", "회복", "지나간 흐름에서 도움을 받을 수 있어요.", "과거에 머물거나 비교가 많을 수 있어요."),
    ("seven", 7, "7", "Seven", "시험", "선택과 인내가 요구되는 구간이에요.", "불안·의심으로 흔들릴 수 있어요."),
    ("eight", 8, "8", "Eight", "집중", "한 방향으로 힘을 모을 때입니다.", "조급함·과로로 지칠 수 있어요."),
    ("nine", 9, "9", "Nine", "마무리", "거의 다 왔지만 마음의 여유가 필요해요.", "걱정·피로가 크게 느껴질 수 있어요."),
    ("ten", 10, "10", "Ten", "완성", "한 사이클의 무게와 결과가 보입니다.", "부담·과잉으로 무거울 수 있어요."),
    ("page", 11, "페이지", "Page", "탐색", "호기심과 새로운 소식을 받아들이는 시기예요.", "미숙함·산만함이 보일 수 있어요."),
    ("knight", 12, "나이트", "Knight", "추진", "행동으로 옮기려는 에너지가 강해요.", "성급함·고집이 부담이 될 수 있어요."),
    ("queen", 13, "퀸", "Queen", "성숙", "감정·경험을 부드럽게 다루는 힘이 있어요.", "과보호·감정 소모가 있을 수 있어요."),
    ("king", 14, "킹", "King", "통솔", "책임 있게 방향을 잡을 수 있는 때예요.", "통제·경직으로 답답할 수 있어요."),
]


def image_url(file_prefix: str, num: int) -> str:
    filename = f"{file_prefix}{num:02d}.svg"
    digest = hashlib.md5(filename.encode()).hexdigest()
    return f"https://upload.wikimedia.org/wikipedia/commons/{digest[0]}/{digest[:2]}/{filename}"


def main() -> None:
    cards = []
    number = 22
    for suit_key, suit in SUITS.items():
        for rank_key, rank_num, rank_ko, rank_en, rank_label, up_tpl, rev_tpl in RANKS:
            theme = suit["theme"]
            cards.append(
                {
                    "id": f"{suit_key}_{rank_key}",
                    "number": number,
                    "suit": suit_key,
                    "rank": rank_key,
                    "arcana": "minor",
                    "name_en": f"{rank_en} of {suit['name_en']}",
                    "name_ko": f"{suit['name_ko']} {rank_ko}",
                    "symbol": suit["symbol"],
                    "keywords_ko": suit["keywords"] + [rank_label],
                    "upright_ko": up_tpl.format(theme=theme),
                    "reversed_ko": rev_tpl,
                    "psychology_theme": f"{suit['name_ko']} · {rank_label} ({theme})",
                    "archetype": suit["archetype_base"],
                    "psychiatric_stress_weight": round(0.35 + (rank_num % 5) * 0.06, 2),
                    "cognitive_distortion_flag": "none",
                    "attachment_matrix_score": round(0.45 + (rank_num % 7) * 0.04, 2),
                    "gradient": suit["gradient"],
                    "image_file": f"{suit['file_prefix']}{rank_num:02d}.svg",
                }
            )
            number += 1
    OUT.write_text(json.dumps(cards, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(cards)} cards to {OUT}")


if __name__ == "__main__":
    main()
