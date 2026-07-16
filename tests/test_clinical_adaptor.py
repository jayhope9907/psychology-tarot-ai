from app.services.clinical_adaptor import (
    build_clinical_adaptor_prompt,
    normalize_clinical_setup,
)


def test_normalize_clinical_setup_defaults():
    setup = normalize_clinical_setup()
    assert setup["resistance_level"] == "LOW"
    assert setup["sensory_impairment_deaf"] is False
    assert setup["cognitive_level"] == "STANDARD"
    assert setup["adaptive_enabled"] is False


def test_normalize_clinical_setup_adaptive_enabled():
    setup = normalize_clinical_setup(
        resistance_level="high",
        sensory_impairment_deaf=True,
        cognitive_level="SIMPLE_EASY",
    )
    assert setup["resistance_level"] == "HIGH"
    assert setup["sensory_impairment_deaf"] is True
    assert setup["cognitive_level"] == "SIMPLE_EASY"
    assert setup["adaptive_enabled"] is True


def test_prompt_contains_required_adaptations():
    setup = normalize_clinical_setup(
        resistance_level="HIGH",
        sensory_impairment_deaf=True,
        cognitive_level="SIMPLE_EASY",
    )
    prompt = build_clinical_adaptor_prompt(setup)
    assert "초등 저학년 수준" in prompt
    assert "검사/테스트/진단/스크리닝" in prompt
    assert "이모지 요약" in prompt

