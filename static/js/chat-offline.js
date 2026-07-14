/** Offline counseling fallback — no assessments, keyword-matched empathy replies. */
(function (global) {
  const BUNDLE_URL = "/static/counsel-offline.bundle.json";
  const CACHE_KEY = "counsel_offline_bundle_v2";
  const QUEUE_KEY = "chat_offline_queue_v1";
  const TURN_KEY = "chat_offline_turn_v1";

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

  function nextTurnIndex() {
    try {
      const current = parseInt(localStorage.getItem(TURN_KEY) || "0", 10) || 0;
      const next = current + 1;
      localStorage.setItem(TURN_KEY, String(next));
      return next;
    } catch (_) {
      return 0;
    }
  }

  function matchReply(message) {
    const b = bundle || readCache() || {};
    const blob = (message || "").trim().toLowerCase();
    const turnIndex = nextTurnIndex();
    const rules = b.rules || [];
    for (const rule of rules) {
      if ((rule.keywords || []).some((kw) => blob.includes(kw))) {
        const replies = (rule.alternates && rule.alternates.length ? rule.alternates : [rule.reply]).filter(Boolean);
        const reply_text = replies[turnIndex % replies.length] || rule.reply;
        return {
          reply_text,
          rule_id: rule.id,
          crisis: !!rule.crisis,
          offline: true,
        };
      }
    }
    return {
      reply_text: b.default_reply || "말씀해 주셔서 고마워요. 연결되면 더 깊은 대화를 이어갈 수 있어요.",
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
