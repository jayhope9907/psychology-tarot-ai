/**
 * Tarot card image visibility for pick UI:
 * - hidden (default): backs stay blank until flipped; revealed faces always use original art
 * - peek: faint face image on backs / pick tiles
 */
(function (global) {
  const KEY = "psychology_ai_tarot_card_images";
  const MODES = { PEEK: "peek", HIDDEN: "hidden" };

  function getMode() {
    const v = localStorage.getItem(KEY);
    if (v === MODES.PEEK) return MODES.PEEK;
    return MODES.HIDDEN;
  }

  function setMode(mode) {
    localStorage.setItem(KEY, mode === MODES.PEEK ? MODES.PEEK : MODES.HIDDEN);
    global.dispatchEvent(new CustomEvent("tarot-image-mode-change", { detail: { mode: getMode() } }));
  }

  /** Revealed faces always use original Rider–Waite (etc.) art when available. */
  function shouldShowImage(flipped) {
    return !!flipped;
  }

  function peekOpacity() {
    return 0.22;
  }

  global.TarotImageSettings = {
    KEY,
    MODES,
    getMode,
    setMode,
    shouldShowImage,
    peekOpacity,
  };
})(window);
