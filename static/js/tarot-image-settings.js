/**
 * Tarot card image visibility: hidden (default, fair pick) | peek
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
