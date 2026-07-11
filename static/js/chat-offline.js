/** Offline counseling fallback — no assessments, keyword-matched empathy replies. */
(function (global) {
  const BUNDLE_URL = "/static/counsel-offline.bundle.json";
  const CACHE_KEY = "counsel_offline_bundle_v1";
  const QUEUE_KEY = "chat_offline_queue_v1";

  let bundle = null;

  function cache(data) {
    try {
      if (data?.rules) localStorage.setItem(CACHE_KEY, JSON.stringify(data));
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

  async function loadBundle() {
    if (bundle?.rules) return bundle;
    if (navigator.onLine !== false) {
      try {
        const res = await fetch("/api/v1/counsel/offline-bundle", { cache: "no-store" });
        if (res.ok) {
          bundle = await res.json();
          cache(bundle);
          return bundle;
        }
      } catch (_) {}
    }
    try {
      const res = await fetch(BUNDLE_URL, { cache: "force-cache" });
      if (res.ok) {
        bundle = await res.json();
        cache(bundle);
        return bundle;
      }
    } catch (_) {}
    bundle = readCache();
    return bundle;
  }

  function isOffline() {
    return navigator.onLine === false;
  }

  function matchReply(message) {
    const b = bundle || readCache() || {};
    const blob = (message || "").trim().toLowerCase();
    const rules = b.rules || [];
    for (const rule of rules) {
      if ((rule.keywords || []).some((kw) => blob.includes(kw))) {
        return {
          reply_text: rule.reply,
          rule_id: rule.id,
          crisis: !!rule.crisis,
          offline: true,
        };
      }
    }
    return {
      reply_text: b.default_reply || "말씀해 주셔서 고마워요. 천천히 괜찮아질 거예요.",
      rule_id: "default",
      offline: true,
    };
  }

  function assessmentBlockedNotice() {
    const b = bundle || readCache() || {};
    return b.assessment_blocked_notice || "오프라인에서는 마음 검사를 할 수 없어요.";
  }

  function crisisResources() {
    const b = bundle || readCache() || {};
    return b.crisis_resources || [
      { label: "1393", tel: "1393" },
      { label: "119", tel: "119" },
    ];
  }

  function queueMessage(payload) {
    try {
      const q = JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
      q.push({ ...payload, queued_at: Date.now() });
      localStorage.setItem(QUEUE_KEY, JSON.stringify(q.slice(-50)));
    } catch (_) {}
  }

  async function flushQueue(sendFn) {
    if (isOffline() || typeof sendFn !== "function") return;
    let q = [];
    try {
      q = JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
    } catch (_) {}
    if (!q.length) return;
    const remaining = [];
    for (const item of q) {
      try {
        await sendFn(item);
      } catch (_) {
        remaining.push(item);
      }
    }
    localStorage.setItem(QUEUE_KEY, JSON.stringify(remaining));
  }

  global.ChatOffline = {
    loadBundle,
    isOffline,
    matchReply,
    assessmentBlockedNotice,
    crisisResources,
    queueMessage,
    flushQueue,
  };
})(typeof window !== "undefined" ? window : globalThis);
