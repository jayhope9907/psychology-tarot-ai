/**
 * Browser TTS voice engine — maps server presets to SpeechSynthesis voices.
 */
(function (global) {
  const STATE = {
    voices: [],
    preset: null,
    enabled: true,
    autoSpeak: false,
    ready: false,
  };

  function loadVoices() {
    return new Promise((resolve) => {
      const pick = () => {
        STATE.voices = speechSynthesis.getVoices() || [];
        if (STATE.voices.length) {
          STATE.ready = true;
          resolve(STATE.voices);
          return true;
        }
        return false;
      };
      if (pick()) return;
      speechSynthesis.onvoiceschanged = () => {
        if (pick()) speechSynthesis.onvoiceschanged = null;
      };
      setTimeout(() => resolve(pick() ? STATE.voices : []), 1200);
    });
  }

  function scoreVoice(voice, preset) {
    if (!voice || !preset) return 0;
    const name = `${voice.name} ${voice.lang}`.toLowerCase();
    let score = 0;
    if (voice.lang && voice.lang.toLowerCase().startsWith("ko")) score += 8;
    (preset.voice_hints || []).forEach((hint) => {
      if (name.includes(String(hint).toLowerCase())) score += 4;
    });
    if (preset.gender === "female" && /female|여성|sunhi|heami|yuna/i.test(name)) score += 3;
    if (preset.gender === "male" && /male|남성|injoon|hyunsu|seungho/i.test(name)) score += 3;
    if (voice.default) score += 1;
    return score;
  }

  function matchVoice(preset) {
    if (!preset || !STATE.voices.length) return null;
    const ranked = STATE.voices
      .map((voice) => ({ voice, score: scoreVoice(voice, preset) }))
      .sort((a, b) => b.score - a.score);
    return ranked[0]?.score > 0 ? ranked[0].voice : STATE.voices.find((v) => v.lang?.startsWith("ko")) || null;
  }

  function listSystemVoices(query = "") {
    const q = query.trim().toLowerCase();
    return STATE.voices
      .filter((v) => !q || `${v.name} ${v.lang}`.toLowerCase().includes(q))
      .map((v) => ({
        name: v.name,
        lang: v.lang,
        localService: v.localService,
        default: v.default,
      }));
  }

  function configure(options = {}) {
    STATE.preset = options.preset || STATE.preset;
    STATE.enabled = options.enabled !== undefined ? options.enabled : STATE.enabled;
    STATE.autoSpeak = options.autoSpeak !== undefined ? options.autoSpeak : STATE.autoSpeak;
  }

  function stop() {
    if ("speechSynthesis" in window) speechSynthesis.cancel();
  }

  function speak(text, presetOverride) {
    if (!("speechSynthesis" in window) || !STATE.enabled) return Promise.resolve(false);
    const clean = String(text || "").replace(/\*\*/g, "").trim();
    if (!clean) return Promise.resolve(false);
    const preset = presetOverride || STATE.preset;
    stop();
    const utter = new SpeechSynthesisUtterance(clean);
    const voice = matchVoice(preset);
    if (voice) utter.voice = voice;
    utter.lang = voice?.lang || "ko-KR";
    utter.pitch = preset?.pitch ?? 1;
    utter.rate = preset?.rate ?? 1;
    utter.volume = preset?.volume ?? 1;
    speechSynthesis.speak(utter);
    return Promise.resolve(true);
  }

  function searchPresets(catalogPresets, query = "", gender = "") {
    const q = query.trim().toLowerCase();
    return (catalogPresets || []).filter((preset) => {
      if (gender && preset.gender !== gender) return false;
      if (!q) return true;
      const hay = `${preset.label} ${preset.gender} ${(preset.tags || []).join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }

  async function init(options = {}) {
    if (!("speechSynthesis" in window)) return { supported: false, voices: [] };
    configure(options);
    const voices = await loadVoices();
    return { supported: true, voices: listSystemVoices() };
  }

  global.VoiceEngine = {
    init,
    configure,
    speak,
    stop,
    listSystemVoices,
    searchPresets,
    matchVoice: () => matchVoice(STATE.preset),
    isSupported: () => "speechSynthesis" in window,
  };
})(window);
