from app.services.homework import HOMEWORK_TEMPLATES


def test_grounding_log_is_stress_reset_template():
    tpl = HOMEWORK_TEMPLATES["grounding_log"]
    assert tpl["title_ko"] == "스트레스 3분 리셋"
    assert tpl["duration_min"] == 3
    fields = {f["id"]: f for f in tpl.get("fields") or []}
    assert "body_sensation" in fields
    assert "five_senses" in fields
    assert "after_grounding" in fields

