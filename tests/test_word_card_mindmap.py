from app.services.word_card_mindmap import (
    MAX_SELECTED_CARDS,
    analyze_conscious_boundary,
    build_mindmap_model,
    build_warm_boundary_question,
    build_word_card_prompt_block,
    extract_conversation_keywords,
    get_word_card_deck,
    sanitize_word_card_selection,
)


def test_deck_payload_shape():
    deck = get_word_card_deck()
    assert deck["maxSelect"] == MAX_SELECTED_CARDS
    assert deck["non_diagnostic"] is True
    all_cards = [c for cat in deck["categories"] for c in cat["cards"]]
    assert len(all_cards) >= 20
    assert all("id" in c and "label_ko" in c for c in all_cards)


def test_sanitize_allowlist_drops_free_text():
    picked = sanitize_word_card_selection(
        ["emptiness", "기쁨", "DROP TABLE users", "<script>", "emptiness", None, 123]
    )
    ids = [c["id"] for c in picked]
    assert ids == ["emptiness", "joy"]


def test_sanitize_caps_selection():
    everything = [c["id"] for c in get_word_card_deck()["categories"][0]["cards"]] * 5
    from app.services.word_card_mindmap import WORD_CARD_DECK

    picked = sanitize_word_card_selection([c["id"] for c in WORD_CARD_DECK])
    assert len(picked) == MAX_SELECTED_CARDS
    assert everything  # sanity


def test_boundary_analysis_layers():
    picked = sanitize_word_card_selection(["joy", "emptiness", "mask"])
    analysis = analyze_conscious_boundary(picked)
    assert analysis["selectedCount"] == 3
    layer_ids = {n["id"] for n in analysis["layers"]["unconscious"]}
    assert "emptiness" in layer_ids and "mask" in layer_ids
    assert any(n["id"] == "joy" for n in analysis["layers"]["conscious"])
    assert 0.0 <= analysis["boundaryScore"] <= 1.0


def test_warm_question_tone():
    picked = sanitize_word_card_selection(["joy", "emptiness"])
    analysis = analyze_conscious_boundary(picked)
    q = build_warm_boundary_question(analysis, display_name="지수")
    assert q.startswith("지수님")
    assert "의식" in q and "무의식" in q
    assert "함께 천천히" in q
    for cold in ("검사", "진단", "테스트"):
        assert cold not in q


def test_prompt_block_binds_warm_rules():
    picked = sanitize_word_card_selection(["emptiness", "longing"])
    analysis = analyze_conscious_boundary(picked)
    block = build_word_card_prompt_block(analysis)
    assert "낱말카드" in block
    assert "따뜻한" in block
    assert "진단 단정 금지" in block
    assert build_word_card_prompt_block({}) == ""


def test_conversation_keywords_allowlist():
    msgs = [
        {"role": "user", "content": "회사에서 너무 지치고 가족이랑도 힘들어요"},
        {"role": "assistant", "content": "회사 이야기 나눠 주셔서 고마워요"},
        {"role": "user", "content": "잠도 잘 안 와요"},
    ]
    kws = extract_conversation_keywords(msgs)
    assert "회사" in kws and "가족" in kws and "잠" in kws


def test_mindmap_model_structure():
    picked = sanitize_word_card_selection(["joy", "emptiness", "rest"])
    analysis = analyze_conscious_boundary(picked)
    mm = build_mindmap_model(
        user_id="u1",
        analysis=analysis,
        conversation_keywords=["회사"],
        stress_summary={"tickCount": 2, "latest": {"preSud": 7}},
        display_name="지수",
    )
    node_ids = {n["id"] for n in mm["nodes"]}
    assert "me_now" in node_ids
    assert "conscious" in node_ids and "deep" in node_ids
    assert "s_resets" in node_ids  # stress tracking integration
    assert any(e["from"] == "me_now" for e in mm["edges"])
    assert mm["titleKo"].startswith("지수님의")
    assert mm["reflectionPromptKo"]
    stress_node = next(n for n in mm["nodes"] if n["id"] == "s_resets")
    assert stress_node["link"] == "stress_management_history"
