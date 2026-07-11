/**
 * Tarot card image visibility: peek (default) | hidden
 */
(function (global) {
  const KEY = "psychology_ai_tarot_card_images";
  const MODES = { PEEK: "peek", HIDDEN: "hidden" };

  function getMode() {
    const v = localStorage.getItem(KEY);
    return v === MODES.HIDDEN ? MODES.HIDDEN : MODES.PEEK;
  }

  function setMode(mode) {
    localStorage.setItem(KEY, mode === MODES.HIDDEN ? MODES.HIDDEN : MODES.PEEK);
    global.dispatchEvent(new CustomEvent("tarot-image-mode-change", { detail: { mode: getMode() } }));
  }

  function shouldShowImage(flipped) {
    if (getMode() === MODES.HIDDEN) return false;
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
