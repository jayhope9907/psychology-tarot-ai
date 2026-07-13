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

    cards.forEach((card) => {
      const orientation = card.reversed ? "역방향" : "정방향";
      cardLines.push({
        position: card.position || "",
        title: `${card.name_ko} (${card.name_en}) · ${orientation}`,
        meaning: card.meaning_ko || "",
        psychology_theme: card.psychology_theme || "",
      });
      if (card.psychology_theme) themes.push(card.psychology_theme);
    });

    const primary = cards[0] || {};
    const summaryParts = [
      "카드는 지금 마음을 **살짝** 비춰 주는 거울이에요. 깊게 파고들 필요는 없어요.",
    ];
    const story = (userStory || "").trim();
    if (story) summaryParts.push("적어 주신 상황을 바탕으로, 부담 없이 읽을 수 있게 정리했어요.");
    if (primary.name_ko) {
      summaryParts.push(
        `'${primary.name_ko}' 카드가 ${primary.psychology_theme || "지금 마음"}과 가볍게 연결될 수 있어요.`
      );
    }

    const cbtActions = [
      "카드가 건드린 느낌 중 하나만 골라 한 줄 적어 보세요.",
      "부담 없는 작은 행동 하나만 떠올려 보세요.",
    ];
    if (story.includes("직장") || story.includes("회사")) {
      cbtActions[1] = "직장에서 통제 가능한 작은 한 가지를 정해 실천해 보세요.";
    }

    return {
      summary: summaryParts.join(" "),
      cards: cardLines,
      psychology_themes: themes,
      cbt_actions: cbtActions,
      primary_card: primary.name_en || "The Fool",
      reading_tone: "light_projection",
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
