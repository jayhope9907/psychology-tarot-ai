"""DSM-5-TR inspired screening spectrums (wellness / non-diagnostic)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.models.clinical import ClinicalSchool

# 스크리닝 영역 — 진단명이 아닌 '관찰·추적 축'
DSM5_SPECTRA: Dict[str, Dict[str, Any]] = {
    "depressive_disorders": {
        "label_ko": "우울·무기력 (Depressive Disorders)",
        "dsm_chapter": "DSM-5-TR · 우울 장애군",
        "instruments": ["phq9", "behavioral", "micro_emotion"],
        "theories": [ClinicalSchool.BECK_CBT, ClinicalSchool.IPT, ClinicalSchool.ROGERIAN, ClinicalSchool.ACT],
        "techniques": ["행동 활성화", "인지 재구조화", "감정 반영", "수면 위생", "작은 목표 설정"],
        "founders": ["Aaron Beck", "Carl Rogers", "Steven Hayes"],
        "keywords": ("우울", "무기력", "공허", "슬픔", "의욕", "흥미", "피곤", "절망"),
    },
    "anxiety_disorders": {
        "label_ko": "불안·걱정 (Anxiety Disorders)",
        "dsm_chapter": "DSM-5-TR · 불안 장애군",
        "instruments": ["gad7", "pss", "micro_emotion"],
        "theories": [ClinicalSchool.BECK_CBT, ClinicalSchool.DBT, ClinicalSchool.MINDFULNESS, ClinicalSchool.ACT],
        "techniques": ["호흡·grounding", "점진적 노출", "걱정 시간 제한", "마음챙김", "불안 기록"],
        "founders": ["Aaron Beck", "Marsha Linehan", "Jon Kabat-Zinn"],
        "keywords": ("불안", "걱정", "초조", "긴장", "두려", "공포", "가슴", "떨"),
    },
    "trauma_stressor": {
        "label_ko": "외상·스트레스 (Trauma & Stressor-Related)",
        "dsm_chapter": "DSM-5-TR · 외상 및 스트레스 관련",
        "instruments": ["pcl5", "gad7", "micro_emotion"],
        "theories": [ClinicalSchool.TRAUMA_INFORMED, ClinicalSchool.EFT, ClinicalSchool.MINDFULNESS],
        "techniques": ["안전·안정화", "감정 명명", "자원 연결", "트리거 기록", "전문 연계 고려"],
        "founders": ["Judith Herman", "Leslie Greenberg", "Bessel van der Kolk"],
        "keywords": ("외상", "트라우마", "악몽", "플래시", "사고", "폭력", "충격", "ptsd"),
    },
    "sleep_wake": {
        "label_ko": "수면·각성 (Sleep-Wake Disorders)",
        "dsm_chapter": "DSM-5-TR · 수면-각성 장애",
        "instruments": ["isi", "phq9", "pss"],
        "theories": [ClinicalSchool.BECK_CBT, ClinicalSchool.MINDFULNESS, ClinicalSchool.INTEGRATIVE],
        "techniques": ["수면 위생", "자극 조절", "취침 루틴", "걱정 분리", "이완 훈련"],
        "founders": ["Aaron Beck", "Richard Bootzin"],
        "keywords": ("잠", "수면", "불면", "악몽", "깨", "피곤", "졸"),
    },
    "ocd_related": {
        "label_ko": "강박·반복 (OCD & Related)",
        "dsm_chapter": "DSM-5-TR · 강박 및 관련 장애",
        "instruments": ["cbt_thought", "gad7", "behavioral"],
        "theories": [ClinicalSchool.BECK_CBT, ClinicalSchool.ACT, ClinicalSchool.DBT],
        "techniques": ["노출·반응 방지", "확실성 수용", "사고 거리두기", "루틴 조절"],
        "founders": ["Aaron Beck", "Steven Hayes"],
        "keywords": ("강박", "반복", "확인", "씻", "완벽", "통제", "루틴"),
    },
    "bipolar_spectrum": {
        "label_ko": "기분 변동·에너지 (Bipolar Spectrum)",
        "dsm_chapter": "DSM-5-TR · 양극성 및 관련 장애 (스크리닝)",
        "instruments": ["micro_emotion", "phq9", "pss"],
        "theories": [ClinicalSchool.DBT, ClinicalSchool.IPT, ClinicalSchool.INTEGRATIVE],
        "techniques": ["기분 일지", "수면 리듬", "에너지 관리", "조기 경고 신호", "전문 연계"],
        "founders": ["Marsha Linehan", "Kay Redfield Jamison"],
        "keywords": ("들뜸", "과활", "기분", "변덕", "충동", "에너지", "야간"),
    },
    "personality_interpersonal": {
        "label_ko": "대인·애착 패턴 (Personality & Interpersonal)",
        "dsm_chapter": "DSM-5-TR · 성격·대인 (스크리닝)",
        "instruments": ["attachment_ecr", "psychodynamic", "micro_emotion", "sct"],
        "theories": [ClinicalSchool.IPT, ClinicalSchool.BOWEN_SYSTEMS, ClinicalSchool.FREUDIAN, ClinicalSchool.DBT],
        "techniques": ["애착 탐색", "경계 설정", "관계 패턴 기록", "감정 조절", "가족도"],
        "founders": ["John Bowlby", "Murray Bowen", "Sigmund Freud"],
        "keywords": ("관계", "애착", "거리", "집착", "회피", "경계", "가족", "배신"),
    },
    "substance_behavioral": {
        "label_ko": "습관·중독 (Substance & Behavioral)",
        "dsm_chapter": "DSM-5-TR · 물질·중독 (스크리닝·교육)",
        "instruments": [
            "alcohol_probe",
            "audit",
            "nicotine_probe",
            "craving_probe",
            "internet_use",
            "behavioral",
            "pss",
            "micro_emotion",
        ],
        "theories": [
            ClinicalSchool.MOTIVATIONAL,
            ClinicalSchool.ADDICTION_CBT,
            ClinicalSchool.RELAPSE_PREVENTION,
            ClinicalSchool.CRA_COMMUNITY,
            ClinicalSchool.CRAFT_FAMILY,
            ClinicalSchool.HARM_REDUCTION,
            ClinicalSchool.CRAVING_MINDFULNESS,
            ClinicalSchool.ACT,
            ClinicalSchool.BECK_CBT,
        ],
        "techniques": [
            "동기 강화(OARS)",
            "기능분석",
            "고위험 상황 지도",
            "갈망 surfing",
            "거절 기술",
            "해로 줄이기",
            "가족 CRAFT",
            "전문 연계(1332)",
        ],
        "founders": [
            "William Miller",
            "G. Alan Marlatt",
            "Kathleen Carroll",
            "Robert Meyers",
            "Sarah Bowen",
        ],
        "keywords": (
            "술",
            "담배",
            "중독",
            "마약",
            "대마",
            "약물",
            "갈망",
            "재발",
            "과몰입",
            "게임",
            "폭식",
            "습관",
            "금단",
            "단주",
            "단약",
        ),
    },
    "somatic_distress": {
        "label_ko": "신체화·스트레스 (Somatic Symptom)",
        "dsm_chapter": "DSM-5-TR · 신체 증상·관련",
        "instruments": ["pss", "gad7", "micro_emotion"],
        "theories": [ClinicalSchool.MINDFULNESS, ClinicalSchool.GESTALT, ClinicalSchool.ROGERIAN],
        "techniques": ["몸 감각 스캔", "스트레스-신체 연결", "이완", "증상 일지"],
        "founders": ["Jon Kabat-Zinn", "Fritz Perls"],
        "keywords": ("두통", "소화", "가슴", "어지", "신체", "통증", "결림"),
    },
    "eating_body": {
        "label_ko": "섭식·몸 이미지 (Feeding & Eating)",
        "dsm_chapter": "DSM-5-TR · 섭식·섭취 (스크리닝)",
        "instruments": ["micro_emotion", "rses", "behavioral"],
        "theories": [ClinicalSchool.BECK_CBT, ClinicalSchool.ROGERIAN, ClinicalSchool.ACT],
        "techniques": ["식사·감정 연결", "자기 연민", "몸 존중", "규칙적 식사"],
        "founders": ["Aaron Beck", "Christopher Fairburn"],
        "keywords": ("식욕", "폭식", "거식", "체중", "몸", "비만", "다이어트"),
    },
    "dissociative_stress": {
        "label_ko": "해리·탈절 (Dissociative · 스트레스)",
        "dsm_chapter": "DSM-5-TR · 해리 (경량 스크리닝)",
        "instruments": ["pcl5", "micro_emotion", "psychodynamic"],
        "theories": [ClinicalSchool.TRAUMA_INFORMED, ClinicalSchool.GESTALT, ClinicalSchool.MINDFULNESS],
        "techniques": ["지금-여기 grounding", "안전 자원", "감각 연결", "전문 연계"],
        "founders": ["Judith Herman", "Pierre Janet"],
        "keywords": ("멍", "비현실", "해리", "공허", "기억", "블랙아웃"),
    },
    "neurodevelopmental": {
        "label_ko": "주의·실행 (Neurodevelopmental · 스크리닝)",
        "dsm_chapter": "DSM-5-TR · 신경발달 (스크리닝)",
        "instruments": ["behavioral", "micro_emotion", "pss"],
        "theories": [ClinicalSchool.ADLERIAN, ClinicalSchool.BECK_CBT, ClinicalSchool.SOLUTION_FOCUSED],
        "techniques": ["구조화·루틴", "작업 분할", "보상 체계", "강점 활용"],
        "founders": ["Alfred Adler", "Russell Barkley"],
        "keywords": ("산만", "집중", "adhd", "실행", "미루", "체계"),
    },
}


def list_dsm5_catalog() -> Dict[str, Any]:
    theories = []
    for school in ClinicalSchool:
        from app.services.counseling_theories import get_theory_meta

        theories.append(get_theory_meta(school))

    spectra = []
    for key, meta in DSM5_SPECTRA.items():
        spectra.append(
            {
                "spectrum_id": key,
                "label_ko": meta["label_ko"],
                "dsm_chapter": meta["dsm_chapter"],
                "instruments": meta["instruments"],
                "theory_ids": [t.value for t in meta["theories"]],
                "techniques": meta["techniques"],
                "founders": meta["founders"],
            }
        )
    return {
        "disclaimer": "스크리닝·웰니스 참고용이며 DSM-5 진단·의료행위가 아닙니다.",
        "spectrum_count": len(spectra),
        "theory_count": len(theories),
        "spectra": spectra,
        "theories": theories,
    }


def score_text_against_spectra(text: str) -> Dict[str, float]:
    blob = (text or "").lower()
    scores: Dict[str, float] = {}
    for key, meta in DSM5_SPECTRA.items():
        hits = sum(1 for kw in meta["keywords"] if kw in blob)
        if hits:
            scores[key] = min(1.0, hits * 0.22)
    return scores


def merge_spectrum_scores(*score_maps: Dict[str, float]) -> Dict[str, float]:
    merged: Dict[str, float] = {}
    for sm in score_maps:
        for key, val in sm.items():
            merged[key] = min(1.0, merged.get(key, 0.0) + val)
    return merged


def recommendations_from_spectra(
    scores: Dict[str, float],
    limit: int = 5,
) -> Dict[str, List[Dict[str, Any]]]:
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    instruments: List[Dict[str, Any]] = []
    techniques: List[Dict[str, Any]] = []
    theories: List[Dict[str, Any]] = []
    seen_inst: set[str] = set()
    seen_tech: set[str] = set()
    seen_theory: set[str] = set()

    for spectrum_id, strength in ranked:
        if strength < 0.15:
            continue
        meta = DSM5_SPECTRA[spectrum_id]
        for inst in meta["instruments"]:
            if inst not in seen_inst:
                seen_inst.add(inst)
                instruments.append(
                    {
                        "instrument_id": inst,
                        "spectrum_id": spectrum_id,
                        "reason": f"{meta['label_ko']} 신호 ({round(strength * 100)}%)",
                        "priority": round(strength, 2),
                    }
                )
        for tech in meta["techniques"][:2]:
            if tech not in seen_tech:
                seen_tech.add(tech)
                techniques.append(
                    {
                        "technique": tech,
                        "spectrum_id": spectrum_id,
                        "reason": meta["label_ko"],
                        "priority": round(strength, 2),
                    }
                )
        for theory in meta["theories"][:2]:
            tid = theory.value
            if tid not in seen_theory:
                seen_theory.add(tid)
                from app.services.counseling_theories import get_theory_meta

                tmeta = get_theory_meta(theory)
                theories.append(
                    {
                        "theory_id": tid,
                        "label": tmeta.get("user_label") or tmeta.get("label"),
                        "founder": tmeta.get("founder") or tmeta.get("subtitle", ""),
                        "spectrum_id": spectrum_id,
                        "priority": round(strength, 2),
                    }
                )

    instruments.sort(key=lambda x: x["priority"], reverse=True)
    techniques.sort(key=lambda x: x["priority"], reverse=True)
    theories.sort(key=lambda x: x["priority"], reverse=True)
    return {
        "instruments": instruments[:8],
        "techniques": techniques[:8],
        "theories": theories[:6],
        "top_spectra": [
            {"spectrum_id": k, "label_ko": DSM5_SPECTRA[k]["label_ko"], "score": round(v, 2)}
            for k, v in ranked
        ],
    }


def instrument_to_spectrum(instrument_id: str) -> Optional[str]:
    for key, meta in DSM5_SPECTRA.items():
        if instrument_id in meta["instruments"]:
            return key
    return None
