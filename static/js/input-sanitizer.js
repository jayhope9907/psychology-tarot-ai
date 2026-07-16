/**
 * Pre-AI input gate — sanitize & compensate (client mirror of app/services/input_sanitizer.py).
 *
 * @typedef {'psychology' | 'faith'} ConsultationMode
 * @typedef {{ mood?: number, energy?: number, anxiety?: number }} CheckInMetrics
 * @typedef {{
 *   consultationMode: ConsultationMode,
 *   step: number,
 *   selectedCard?: string | null,
 *   checkInMetrics?: CheckInMetrics | null
 * }} RawInputData
 */

export const DEFAULT_CHECKIN_WEIGHT = 50;
export const ARCHETYPE_NONE = "None";

function clampInt(value, lo, hi, fallback) {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  return Math.max(lo, Math.min(hi, Math.round(n)));
}

function normalizeWeight(value, fallback = DEFAULT_CHECKIN_WEIGHT) {
  if (value == null || value === "") return fallback;
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  if (n >= 1 && n <= 5 && Number.isInteger(n)) {
    return Math.round(((n - 1) / 4) * 100);
  }
  return clampInt(n, 0, 100, fallback);
}

/**
 * AI 분석 엔진으로 들어가기 전, 유저 데이터를 안전하게 보완 및 정제하는 알고리즘
 * @param {RawInputData} input
 */
export function sanitizeAndCompensate(input) {
  const mode =
    String(input?.consultationMode || "psychology").toLowerCase() === "faith"
      ? "faith"
      : "psychology";
  const step = clampInt(input?.step, 1, 5, 1);
  const safeCard =
    step < 2 || !input?.selectedCard ? ARCHETYPE_NONE : String(input.selectedCard).trim() || ARCHETYPE_NONE;

  const safeCheckIn = {
    mood: normalizeWeight(input?.checkInMetrics?.mood),
    energy: normalizeWeight(input?.checkInMetrics?.energy),
    anxiety: normalizeWeight(input?.checkInMetrics?.anxiety),
  };

  const isFaithMode = mode === "faith";
  return {
    mode,
    consultationMode: mode,
    currentStep: step,
    step,
    dominantArchetype: safeCard,
    selectedCard: safeCard === ARCHETYPE_NONE ? null : safeCard,
    initialWeights: safeCheckIn,
    checkInMetrics: safeCheckIn,
    isFaithMode,
    defenseMechanismEnabled: !isFaithMode,
    defenseMechanism: isFaithMode ? null : "active",
  };
}

if (typeof window !== "undefined") {
  window.PsychologyInputSanitizer = { sanitizeAndCompensate, DEFAULT_CHECKIN_WEIGHT, ARCHETYPE_NONE };
}
