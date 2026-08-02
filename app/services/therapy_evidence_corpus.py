"""Peer-reviewed / landmark evidence corpus mapped to ClinicalSchool + architecture.

비진단 웰니스 참고용. 논문이 의료 효능·기기 승인을 입증한다고 주장하지 않는다.
인용은 교육·아키텍처 설계 근거이며, 원문 DOI로 재확인해야 한다.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# type: meta | rct | review | theoretical | guideline
EVIDENCE_PAPERS: List[Dict[str, Any]] = [
    {
        "id": "hayes_hofmann_2017_pbt",
        "year": 2017,
        "authors": "Hayes SC, Hofmann SG",
        "title": "The third wave of cognitive behavioral therapy and the rise of process-based therapy",
        "venue": "World Psychiatry",
        "doi": "10.1002/wps.20442",
        "type": "theoretical",
        "schools": ["ACT", "BECK_CBT", "INTEGRATIVE", "DBT", "MBCT"],
        "architecture_hooks": [
            "process_based_therapy",
            "therapy_biomarker_engine",
            "instant_keyword_router",
        ],
        "implication_ko": "증상 범주보다 변화 과정(수용·알아차림·전념 등)을 라우팅·바이오마커 축으로 둔다.",
    },
    {
        "id": "hofmann_hayes_2019_pbt",
        "year": 2019,
        "authors": "Hofmann SG, Hayes SC",
        "title": "The Future of Intervention Science: Process-Based Therapy",
        "venue": "Clinical Psychological Science",
        "doi": "10.1177/2167702618772296",
        "type": "theoretical",
        "schools": ["ACT", "INTEGRATIVE", "BECK_CBT"],
        "architecture_hooks": ["process_based_therapy", "user_agent_algorithm"],
        "implication_ko": "개인별 과정 네트워크(idiographic) 추적을 ALG·세션 피드백에 연결한다.",
    },
    {
        "id": "cuijpers_2019_cbt_meta",
        "year": 2019,
        "authors": "Cuijpers P et al.",
        "title": "Cognitive behavior therapy vs. control conditions, other psychotherapies, pharmacotherapies and psychotherapy-pharmacotherapy combinations for depression",
        "venue": "World Psychiatry / meta-analytic program",
        "doi": "10.1002/wps.20610",
        "type": "meta",
        "schools": ["BECK_CBT", "BEHAVIORAL_ACTIVATION"],
        "architecture_hooks": ["therapy_biomarker_engine", "counseling_theories"],
        "implication_ko": "CBT·행동활성화 축을 기본 근거 기반 레퍼토리로 유지한다.",
    },
    {
        "id": "dimidjian_2006_ba",
        "year": 2006,
        "authors": "Dimidjian S et al.",
        "title": "Randomized trial of behavioral activation, cognitive therapy, and antidepressant medication in the acute treatment of adults with major depression",
        "venue": "Journal of Consulting and Clinical Psychology",
        "doi": "10.1037/0022-006X.74.4.658",
        "type": "rct",
        "schools": ["BEHAVIORAL_ACTIVATION", "BECK_CBT"],
        "architecture_hooks": ["therapy_biomarker_engine", "homework"],
        "implication_ko": "행동활성화 completion ratio를 독립 바이오마커·숙제 모듈로 둔다.",
    },
    {
        "id": "linehan_2006_dbt",
        "year": 2006,
        "authors": "Linehan MM et al.",
        "title": "Two-year randomized controlled trial and follow-up of dialectical behavior therapy vs therapy by experts for suicidal behaviors and borderline personality disorder",
        "venue": "Archives of General Psychiatry",
        "doi": "10.1001/archpsyc.63.7.757",
        "type": "rct",
        "schools": ["DBT"],
        "architecture_hooks": ["therapy_biomarker_engine", "crisis_guardrails"],
        "implication_ko": "고통감내·감정조절 점수를 위기 톤 게이팅과 함께 둔다(진단 아님).",
    },
    {
        "id": "powers_2009_act_meta",
        "year": 2009,
        "authors": "Powers MB, Zum Vorde Sive Vording MB, Emmelkamp PMG",
        "title": "Acceptance and commitment therapy: A meta-analytic review",
        "venue": "Psychotherapy and Psychosomatics",
        "doi": "10.1159/000190790",
        "type": "meta",
        "schools": ["ACT"],
        "architecture_hooks": ["process_based_therapy", "therapy_biomarker_engine"],
        "implication_ko": "가치·전념 행동 비율을 ACT 축·PBT engagement 차원에 매핑한다.",
    },
    {
        "id": "kuyken_2016_mbct",
        "year": 2016,
        "authors": "Kuyken W et al.",
        "title": "Efficacy of mindfulness-based cognitive therapy in prevention of depressive relapse",
        "venue": "JAMA Psychiatry",
        "doi": "10.1001/jamapsychiatry.2016.0076",
        "type": "meta",
        "schools": ["MBCT", "MINDFULNESS"],
        "architecture_hooks": ["therapy_biomarker_engine"],
        "implication_ko": "탈중심(decentering) 비율을 MBCT/마음챙김 축으로 둔다.",
    },
    {
        "id": "resick_2017_cpt",
        "year": 2017,
        "authors": "Resick PA, Monson CM, Chard KM",
        "title": "Cognitive Processing Therapy for PTSD: A Comprehensive Manual",
        "venue": "Guilford (manual / evidence base)",
        "doi": "10.1891/9780826136091",
        "type": "guideline",
        "schools": ["CPT_INFORMED", "TRAUMA_INFORMED"],
        "architecture_hooks": ["therapy_biomarker_engine", "trauma_safety_gate"],
        "implication_ko": "stuck-point 전환 속도·안전 게이트를 CPT 안내 레이어로 둔다(자격 치료 대체 금지).",
    },
    {
        "id": "foa_2007_pe",
        "year": 2007,
        "authors": "Foa EB, Hembree EA, Rothbaum BO",
        "title": "Prolonged Exposure Therapy for PTSD: Emotional Processing of Traumatic Experiences",
        "venue": "Oxford University Press (protocol)",
        "doi": "10.1093/med:psych/9780195308501.001.0001",
        "type": "guideline",
        "schools": ["PROLONGED_EXPOSURE_INFORMED", "TRAUMA_INFORMED"],
        "architecture_hooks": ["trauma_safety_gate", "therapy_biomarker_engine"],
        "implication_ko": "점진 접근 비율만 교육적으로 추적하고 강한 노출은 전문 치료로 넘긴다.",
    },
    {
        "id": "lee_cuijpers_2013_emdr",
        "year": 2013,
        "authors": "Lee CW, Cuijpers P",
        "title": "A meta-analysis of the contribution of eye movements in processing emotional memories",
        "venue": "Journal of Behavior Therapy and Experimental Psychiatry",
        "doi": "10.1016/j.jbtep.2012.11.001",
        "type": "meta",
        "schools": ["EMDR_INFORMED"],
        "architecture_hooks": ["trauma_safety_gate"],
        "implication_ko": "EMDR은 안정화·정보제공 축만 두고 재처리 시술은 수행하지 않는다.",
    },
    {
        "id": "johnson_2019_eft",
        "year": 2019,
        "authors": "Johnson SM",
        "title": "Attachment Theory in Practice: Emotionally Focused Therapy (EFT) with Individuals, Couples, and Families",
        "venue": "Guilford",
        "doi": "10.1891/9781462539956",
        "type": "guideline",
        "schools": ["EFT", "ATTACHMENT"],
        "architecture_hooks": ["therapy_biomarker_engine", "maum_organism"],
        "implication_ko": "정서 유대·안전기지 점수를 관계/오거니즘 연결에 쓴다.",
    },
    {
        "id": "miller_rollnick_2013_mi",
        "year": 2013,
        "authors": "Miller WR, Rollnick S",
        "title": "Motivational Interviewing: Helping People Change (3rd ed.)",
        "venue": "Guilford",
        "doi": "10.1093/acrefore/9780199975839.013.1283",
        "type": "guideline",
        "schools": ["MOTIVATIONAL"],
        "architecture_hooks": ["instant_keyword_router", "therapy_biomarker_engine"],
        "implication_ko": "변화대화 비율을 MI 축·즉시 라우팅 가중치에 반영한다.",
    },
    {
        "id": "barlow_2017_unified",
        "year": 2017,
        "authors": "Barlow DH et al.",
        "title": "The Unified Protocol for Transdiagnostic Treatment of Emotional Disorders",
        "venue": "Oxford University Press",
        "doi": "10.1093/med-psych/9780190685973.001.0001",
        "type": "guideline",
        "schools": ["INTEGRATIVE", "BECK_CBT", "MINDFULNESS"],
        "architecture_hooks": ["process_based_therapy", "emotional_spectrum"],
        "implication_ko": "초진단 정서 과정(회피·감정인식)을 스펙트럼·PBT 공용 차원으로 둔다.",
    },
    {
        "id": "wampold_2015_common",
        "year": 2015,
        "authors": "Wampold BE, Imel ZE",
        "title": "The Great Psychotherapy Debate: The Evidence for What Makes Psychotherapy Work",
        "venue": "Routledge",
        "doi": "10.4324/9780203582015",
        "type": "review",
        "schools": ["INTEGRATIVE", "ROGERIAN"],
        "architecture_hooks": ["process_based_therapy", "fit_session_feedback"],
        "implication_ko": "공통요인(관계·기대·피드백)을 FIT 세션 피드백 레이어로 둔다.",
    },
    {
        "id": "lambert_2010_rom",
        "year": 2010,
        "authors": "Lambert MJ, Shimokawa K",
        "title": "Collecting client feedback",
        "venue": "Psychotherapy",
        "doi": "10.1037/a0022178",
        "type": "review",
        "schools": ["INTEGRATIVE"],
        "architecture_hooks": ["fit_session_feedback", "stress_management_store"],
        "implication_ko": "세션 성과·연합 피드백(ROM/FIT)을 측정기반 케어 모듈로 구현한다.",
    },
    {
        "id": "schwartz_2021_ifs",
        "year": 2021,
        "authors": "Schwartz RC, Sweezy M",
        "title": "Internal Family Systems Therapy (2nd ed.)",
        "venue": "Guilford",
        "doi": "10.1891/9781462541478",
        "type": "guideline",
        "schools": ["IFS"],
        "architecture_hooks": ["therapy_biomarker_engine"],
        "implication_ko": "Self-leadership 비율을 IFS 축으로 두고 파트 은유로 안내한다.",
    },
    {
        "id": "porges_2022_polyvagal",
        "year": 2022,
        "authors": "Porges SW",
        "title": "Polyvagal Theory: A Science of Safety",
        "venue": "Frontiers in Integrative Neuroscience (program)",
        "doi": "10.3389/fnint.2022.871227",
        "type": "theoretical",
        "schools": ["POLYVAGAL_INFORMED", "SOMATIC_EXPERIENCING", "TRAUMA_INFORMED"],
        "architecture_hooks": ["trauma_safety_gate", "therapy_biomarker_engine"],
        "implication_ko": "안전 신호 비율로 톤·개입 강도를 조절하는 안전 게이트를 둔다(신경 진단 아님).",
    },
    {
        "id": "levine_2010_se",
        "year": 2010,
        "authors": "Levine PA",
        "title": "In an Unspoken Voice: How the Body Releases Trauma and Restores Goodness",
        "venue": "North Atlantic Books",
        "doi": "10.1037/e528492013-001",
        "type": "theoretical",
        "schools": ["SOMATIC_EXPERIENCING"],
        "architecture_hooks": ["trauma_safety_gate"],
        "implication_ko": "타이틀레이션·자원 감각 안내만 두고 강한 체성 재노출은 금지한다.",
    },
    {
        "id": "young_2003_schema",
        "year": 2003,
        "authors": "Young JE, Klosko JS, Weishaar ME",
        "title": "Schema Therapy: A Practitioner's Guide",
        "venue": "Guilford",
        "doi": "10.4324/9780203571798",
        "type": "guideline",
        "schools": ["SCHEMA_THERAPY"],
        "architecture_hooks": ["therapy_biomarker_engine", "user_agent_algorithm"],
        "implication_ko": "모드 전환 지연을 스키마 축·장기 패턴 ALG에 연결한다.",
    },
    {
        "id": "gilbert_2014_cft",
        "year": 2014,
        "authors": "Gilbert P",
        "title": "The origins and nature of compassion focused therapy",
        "venue": "British Journal of Clinical Psychology",
        "doi": "10.1111/bjc.12043",
        "type": "theoretical",
        "schools": ["CFT"],
        "architecture_hooks": ["therapy_biomarker_engine"],
        "implication_ko": "자기자비 비율을 CFT 축·톤 조절에 쓴다.",
    },
    {
        "id": "norcross_2019_relations",
        "year": 2019,
        "authors": "Norcross JC, Lambert MJ",
        "title": "Psychotherapy relationships that work III",
        "venue": "Psychotherapy",
        "doi": "10.1037/pst0000233",
        "type": "meta",
        "schools": ["INTEGRATIVE", "ROGERIAN"],
        "architecture_hooks": ["fit_session_feedback", "process_based_therapy"],
        "implication_ko": "치료 동맹·피드백 수용을 FIT alliance 점수로 둔다.",
    },
    {
        "id": "bowen_2014_mbrp",
        "year": 2014,
        "authors": "Bowen S, Chawla N, Marlatt GA",
        "title": "Mindfulness-Based Relapse Prevention for Addictive Behaviors",
        "venue": "Guilford",
        "doi": "10.1891/9781462515158",
        "type": "guideline",
        "schools": ["CRAVING_MINDFULNESS", "RELAPSE_PREVENTION", "MINDFULNESS"],
        "architecture_hooks": ["addiction_theories", "therapy_biomarker_engine"],
        "implication_ko": "갈망 관찰 비율을 중독·회복 기법 라우팅에 연결한다.",
    },
    {
        "id": "van_ijzendoorn_1995_aai",
        "year": 1995,
        "authors": "van IJzendoorn MH",
        "title": "Adult attachment representations, parental responsiveness, and infant attachment: A meta-analysis on the predictive validity of the Adult Attachment Interview",
        "venue": "Psychological Bulletin",
        "doi": "10.1037/0033-2909.117.3.387",
        "type": "meta",
        "schools": ["ATTACHMENT", "EFT", "OBJECT_RELATIONS"],
        "architecture_hooks": [
            "aai_attachment_coherence",
            "therapy_biomarker_engine",
            "process_based_therapy",
        ],
        "implication_ko": "AAI 서술 일관성·안전기지 표상을 attachment/relatedness 축 참고로 둔다(정식 AAI 채점·진단 아님).",
    },
    {
        "id": "bakermans_1993_aai_psychometric",
        "year": 1993,
        "authors": "Bakermans-Kranenburg MJ, van IJzendoorn MH",
        "title": "A psychometric study of the Adult Attachment Interview: Reliability and discriminant validity",
        "venue": "Developmental Psychology",
        "doi": "10.1037/0012-1649.29.5.870",
        "type": "review",
        "schools": ["ATTACHMENT"],
        "architecture_hooks": ["aai_attachment_coherence"],
        "implication_ko": "애착 표상 측정의 신뢰·변별 근거를 코히어런스 프록시 설계에 참고한다.",
    },
    {
        "id": "main_1985_aai_protocol",
        "year": 1985,
        "authors": "George C, Kaplan N, Main M",
        "title": "Adult Attachment Interview (AAI) protocol",
        "venue": "University of California, Berkeley (unpublished protocol; widely cited)",
        "doi": "10.1037/0033-2909.117.3.387",
        "type": "guideline",
        "schools": ["ATTACHMENT"],
        "architecture_hooks": ["aai_attachment_coherence"],
        "implication_ko": "원 프로토콜은 자격 훈련 전제. 제품에서는 관계 서술의 일관성·안전감만 교육적으로 반영한다.",
        "note": "Original AAI protocol is unpublished; DOI points to the canonical predictive-validity meta-analysis that cites it.",
    },
    {
        "id": "reeb_2018_pesm",
        "year": 2018,
        "authors": "Reeb RN et al.",
        "title": "Psycho-Ecological Systems Model: A Systems Approach to Planning and Gauging the Community Impact of Community-Engaged Scholarship",
        "venue": "Michigan Journal of Community Service Learning",
        "doi": "10.3998/mjcsloa.3239521.0024.102",
        "type": "theoretical",
        "schools": ["INTEGRATIVE", "MULTICULTURAL", "BOWEN_SYSTEMS"],
        "architecture_hooks": [
            "pesm_ecological_systems",
            "process_based_therapy",
            "platform_ip_map",
        ],
        "implication_ko": "개인·관계·공동체·구조 다층(생태체계)을 라우팅·성과 평가 레이어로 둔다.",
    },
]


def list_evidence_papers(
    school: Optional[str] = None,
    hook: Optional[str] = None,
    year_from: Optional[int] = None,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for paper in EVIDENCE_PAPERS:
        if school and school not in paper["schools"]:
            continue
        if hook and hook not in paper["architecture_hooks"]:
            continue
        if year_from is not None and int(paper["year"]) < int(year_from):
            continue
        rows.append(dict(paper))
    return rows


def papers_for_school(school: str) -> List[Dict[str, Any]]:
    return list_evidence_papers(school=school)


def build_evidence_corpus() -> Dict[str, Any]:
    by_school: Dict[str, int] = {}
    by_hook: Dict[str, int] = {}
    for paper in EVIDENCE_PAPERS:
        for school in paper["schools"]:
            by_school[school] = by_school.get(school, 0) + 1
        for hook in paper["architecture_hooks"]:
            by_hook[hook] = by_hook.get(hook, 0) + 1
    return {
        "title": "Therapy evidence corpus (architecture-mapped)",
        "disclaimer": (
            "교육·아키텍처 설계용 참고 문헌입니다. 진단·처방·의료기기 성능·치료 효능을 주장하지 않으며, "
            "DOI는 원문 확인이 필요합니다."
        ),
        "non_diagnostic": True,
        "paper_count": len(EVIDENCE_PAPERS),
        "by_school": by_school,
        "by_architecture_hook": by_hook,
        "papers": list_evidence_papers(),
    }


def attach_evidence_to_axes(axes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for axis in axes:
        school = axis.get("school") or ""
        refs = [
            {
                "id": p["id"],
                "year": p["year"],
                "title": p["title"],
                "doi": p["doi"],
                "type": p["type"],
            }
            for p in papers_for_school(school)
        ]
        out.append({**axis, "evidence_papers": refs, "evidence_count": len(refs)})
    return out
