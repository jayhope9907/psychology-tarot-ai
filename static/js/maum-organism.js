/**
 * 마음쉼터 유기체 — 통합 user/session 키, 거미줄 UI, iframe 간 동기화.
 */
(function (global) {
  const USER_KEY = "psychology_ai_user_id";
  const SESSION_KEY = "psychology_ai_session_id";
  const LEGACY_PICTO_SESSION = "psychology_ai_picto_session";

  function userId() {
    let id = global.localStorage.getItem(USER_KEY);
    if (!id) {
      id = `user-${crypto.randomUUID().slice(0, 8)}`;
      global.localStorage.setItem(USER_KEY, id);
    }
    return id;
  }

  function unifySession() {
    const main = global.localStorage.getItem(SESSION_KEY);
    const picto = global.localStorage.getItem(LEGACY_PICTO_SESSION);
    if (!main && picto) {
      global.localStorage.setItem(SESSION_KEY, picto);
      global.localStorage.removeItem(LEGACY_PICTO_SESSION);
      return picto;
    }
    if (main && picto && main !== picto) {
      global.localStorage.removeItem(LEGACY_PICTO_SESSION);
    }
    return main;
  }

  function setSession(sessionId) {
    if (sessionId) global.localStorage.setItem(SESSION_KEY, sessionId);
  }

  function broadcastRefresh(reason) {
    const msg = { type: "maum-organism-refresh", reason: reason || "activity" };
    if (global.parent && global.parent !== global) {
      global.parent.postMessage(msg, "*");
    }
    global.dispatchEvent(new CustomEvent("maum-organism-refresh", { detail: msg }));
  }

  async function fetchState() {
    const uid = userId();
    try {
      const res = await fetch(`/api/v1/organism/${encodeURIComponent(uid)}`, { cache: "no-store" });
      if (!res.ok) return null;
      const data = await res.json();
      if (data.unified_session_id) setSession(data.unified_session_id);
      return data;
    } catch (_) {
      return null;
    }
  }

  function renderWeb(container, state) {
    if (!container || !state) return;
    const nodes = state.nodes || [];
    const edges = state.edges || [];
    const strong = new Set(
      edges.filter((e) => e.strength >= 0.7).flatMap((e) => [e.from, e.to])
    );

    container.innerHTML = `
      <div class="organism-nodes" role="list" aria-label="마음 기능 연결">
        ${nodes.map((n) => `
          <button type="button" class="organism-node ${n.active_today ? "active" : ""} ${strong.has(n.id) ? "linked" : ""}"
            data-tab="${n.tab}" title="${n.label}" style="--pulse:${n.pulse}">
            <span class="organism-emoji">${n.emoji}</span>
          </button>`).join('<span class="organism-wire" aria-hidden="true"></span>')}
      </div>
      <div class="organism-actions" id="organismActions"></div>`;

    container.querySelectorAll(".organism-node").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        if (global.parent && global.parent !== global) {
          global.parent.postMessage({ type: "maum-nav", tab }, "*");
        } else if (tab) {
          global.location.href = { checkin: "/home", chat: "/chat", tarot: "/tarot", picto: "/picto" }[tab] || "/";
        }
      });
    });

    const actionsEl = container.querySelector("#organismActions");
    (state.next_actions || []).slice(0, 2).forEach((act) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "organism-action-chip";
      chip.textContent = `${act.emoji} ${act.label}`;
      chip.title = act.reason || "";
      chip.addEventListener("click", () => {
        if (global.parent && global.parent !== global) {
          global.parent.postMessage({ type: "maum-nav", tab: act.tab }, "*");
        }
      });
      actionsEl.appendChild(chip);
    });
  }

  global.MaumOrganism = {
    userId,
    unifySession,
    setSession,
    sessionId: () => unifySession(),
    broadcastRefresh,
    fetchState,
    renderWeb,
  };

  unifySession();
})(typeof window !== "undefined" ? window : globalThis);
