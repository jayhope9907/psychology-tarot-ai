/** Offline tarot: deck load, pick resolution, local reading (mirrors server tarot.py). */
(function (global) {
  const BUNDLE_URL = "/static/tarot-deck.bundle.json";
  const CACHE_KEY = "tarot_deck_bundle_v1";

  function cache(data) {
    try {
      if (data?.cards?.length) localStorage.setItem(CACHE_KEY, JSON.stringify(data));
    } catch (_) {}
  }

  function readCache() {
    try {
      const raw = localStorage.getItem(CACHE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  }

  async function loadDeckCatalog() {
    if (navigator.onLine !== false) {
      try {
        const res = await fetch("/api/v1/tarot/deck", { cache: "no-store" });
        if (res.ok) {
          const data = await res.json();
          cache(data);
          return data;
        }
      } catch (_) {}
    }
    try {
      const res = await fetch(BUNDLE_URL, { cache: "force-cache" });
      if (res.ok) {
        const data = await res.json();
        cache(data);
        return data;
      }
    } catch (_) {}
    const cached = readCache();
    if (cached?.cards?.length) return cached;
    return null;
  }

  function cardMap(catalog) {
    const m = {};
    (catalog?.cards || []).forEach((c) => {
      m[c.id] = c;
    });
    return m;
  }

  function buildDrawFromPicks(cardIds, spread, catalog, reversedFlags) {
    const spreads = catalog?.spreads || {};
    const spreadMeta =
      spreads.three_card ||
      spreads[spread] || {
        label_ko: "3카드 스프레드",
        positions: ["과거·뿌리", "현재·핵심", "미래·방향"],
      };
    const positions = spreadMeta.positions || [];
    const map = cardMap(catalog);
    const drawn = [];
    const uniqueIds = [...new Set(cardIds)].slice(0, 3);

    uniqueIds.forEach((id, index) => {
      const card = map[id];
      if (!card) return;
      const reversed =
        reversedFlags && index < reversedFlags.length
          ? reversedFlags[index]
          : Math.random() < 0.5;
      const position = positions[index] || `카드 ${index + 1}`;
      drawn.push({
        id: card.id,
        number: card.number,
        arcana: card.arcana,
        suit: card.suit,
        rank: card.rank,
        name_en: card.name_en,
        name_ko: card.name_ko,
        symbol: card.symbol,
        keywords_ko: card.keywords_ko,
        gradient: card.gradient,
        image_url: card.image_url,
        position,
        reversed,
        meaning_ko: reversed ? card.reversed_ko : card.upright_ko,
        psychology_theme: card.psychology_theme,
        archetype: card.archetype,
      });
    });

    return {
      spread: "three_card",
      spread_label_ko: spreadMeta.label_ko || "3카드 스프레드",
      positions: positions.slice(0, drawn.length),
      cards: drawn,
      rules: { spread: "three_card", count: 3, reverse_chance: 0.5 },
      offline: navigator.onLine === false,
    };
  }

  function buildLocalReading(userStory, drawResult) {
    const cards = drawResult?.cards || [];
    const cardLines = [];
    const themes = [];
    const guides = {
      "과거·뿌리": "과거의 뿌리·배경·무엇이 지금의 마음을 만들었는지",
      "현재·핵심": "지금 상황의 핵심·현재 감정·직면하고 있는 것",
      "미래·방향": "앞으로의 방향·가능성·가볍게 열어둘 다음 한 걸음",
    };

    cards.forEach((card) => {
      const orientation = card.reversed ? "역방향" : "정방향";
      cardLines.push({
        position: card.position || "",
        position_guide: guides[card.position] || card.position_guide || "",
        title: `${card.name_ko} (${card.name_en}) · ${orientation}`,
        meaning: card.meaning_ko || "",
        psychology_theme: card.psychology_theme || "",
        archetype: card.archetype || "",
        orientation_guide: card.reversed
          ? "막힘·내면화·과잉·시기가 아직 아님 — 운명 단정 금지"
          : "에너지가 비교적 열리고 표현되기 쉬운 상태",
        suit_label: card.suit_rule?.label_ko || "",
        element: card.suit_rule?.element_ko || "",
        rank_guide: card.rank_rule?.guide_ko || "",
      });
      if (card.psychology_theme) themes.push(card.psychology_theme);
    });

    const summaryParts = [
      "클래식 3카드(과거·현재·미래) · 78장 · 정/역 공정 · 위치·수트·아르카나 규칙으로 읽어요.",
    ];
    const story = (userStory || "").trim();
    if (story) summaryParts.push("적어 주신 상황을 바탕으로, 부담 없이 읽을 수 있게 정리했어요.");
    cards.forEach((card) => {
      const orientation = card.reversed ? "역방향" : "정방향";
      summaryParts.push(
        `${card.position}(${guides[card.position] || ""}): ${card.name_ko} (${orientation})`
      );
    });

    const cbtActions = [
      "과거·뿌리 카드가 건드린 배경을 한 줄로 적어 보세요.",
      "현재·핵심에서 오늘 할 수 있는 작은 행동 하나만 정해 보세요.",
      "미래·방향은 확정이 아니라 가능성 — 부담 없는 다음 한 걸음만 열어 두세요.",
    ];
    if (story.includes("직장") || story.includes("회사")) {
      cbtActions[1] = "직장에서 통제 가능한 작은 한 가지를 정해 실천해 보세요.";
    }

    const primary = cards[1] || cards[0] || {};
    return {
      summary: summaryParts.join(" "),
      cards: cardLines,
      psychology_themes: themes,
      cbt_actions: cbtActions,
      primary_card: primary.name_en || "The Fool",
      reading_tone: "three_card_classic",
      practice_rules_ko: [
        "질문 하나에 3장만 뽑습니다. (과거·현재·미래)",
        "덱은 78장(메이저 22 + 마이너 56)이며, 중복 없이 뽑습니다.",
        "섞은 뒤 뒷면만 보고 직감으로 고릅니다. 앞면을 보고 고르지 않습니다.",
        "정방향/역방향은 카드마다 독립적으로 공정하게 결정됩니다.",
        "각 카드는 자기 위치(과거/현재/미래)로만 읽습니다.",
        "미래는 예언이 아니라 가능성·방향입니다.",
        "메이저는 큰 테마, 마이너(수트·원소)는 일상의 결로 읽습니다.",
        "궁정 카드는 사람·태도·접근 방식으로 가볍게 봅니다.",
        "진단·운명·확정 예언으로 쓰지 않습니다. 자기성찰 거울입니다.",
      ],
      offline: true,
    };
  }

  function buildBridgeMessage(userStory, draw, reading) {
    const lines = (draw?.cards || []).map(
      (c) => `${c.position}: ${c.name_ko}${c.reversed ? " (역)" : ""} — ${c.meaning_ko || ""}`
    );
    return (
      "[타로 자기성찰 · 오프라인]\n" +
      (userStory ? `질문: ${userStory}\n` : "") +
      lines.join("\n") +
      (reading?.summary ? `\n\n풀이: ${reading.summary.replace(/\*\*/g, "")}` : "")
    );
  }

  global.TarotOffline = {
    loadDeckCatalog,
    buildDrawFromPicks,
    buildLocalReading,
    buildBridgeMessage,
  };
})(typeof window !== "undefined" ? window : globalThis);
