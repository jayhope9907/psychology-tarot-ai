from app.models.clinical import ClinicalSchool
from app.services.counseling_theories import THEORY_CATALOG, build_theory_directive, list_theories_for_api
from app.services.persona_router import route_clinical_persona


def test_theory_catalog_covers_major_approaches():
    assert len(THEORY_CATALOG) >= 18
    schools = {item["school"] for item in list_theories_for_api()}
    for expected in (
        "ROGERIAN",
        "BECK_CBT",
        "FREUDIAN",
        "GESTALT",
        "SOLUTION_FOCUSED",
        "DBT",
        "ACT",
        "TRAUMA_INFORMED",
        "INTEGRATIVE",
        "PSYCHODRAMA",
        "DRAMA_THERAPY",
    ):
        assert expected in schools


def test_build_theory_directive_includes_techniques():
    block = build_theory_directive(ClinicalSchool.BECK_CBT, ["all_or_nothing"])
    assert "인지" in block
    assert "소크라테스" in block or "CBT" in block
    assert "all_or_nothing" in block


def test_route_keyword_match_solution_focused():
    routing = route_clinical_persona("해결 방법을 찾고 싶어요. 예외도 있었어요.")
    assert routing["school"] == ClinicalSchool.SOLUTION_FOCUSED


def test_theories_have_user_facing_labels():
    theories = list_theories_for_api()
    ipt = next(t for t in theories if t["school"] == "IPT")
    assert ipt["user_label"] == "대인관계상담"
    bowen = next(t for t in theories if t["school"] == "BOWEN_SYSTEMS")
    assert bowen["user_label"] == "가족상담"


def test_route_counselor_default_when_neutral():
    routing = route_clinical_persona(
        "안녕하세요.",
        counselor_default_school=ClinicalSchool.EXISTENTIAL,
    )
    assert routing["school"] == ClinicalSchool.EXISTENTIAL
    assert routing["reason"] == "counselor_specialty_default"
