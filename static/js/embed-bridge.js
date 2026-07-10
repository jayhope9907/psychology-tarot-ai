/**
 * Standalone pages: consent gate + embed navigation bridge for unified app shell.
 */
(function (global) {
  const embed = new URLSearchParams(global.location.search).get("embed") === "1";
  const CONSENT_KEY = "psychology_ai_consent_v1";

  if (!embed && global.localStorage.getItem(CONSENT_KEY) !== "1") {
    const tab = { "/home": "checkin", "/chat": "chat", "/tarot": "tarot" }[global.location.pathname];
    if (tab) {
      global.location.replace("/#" + tab);
      return;
    }
  }

  if (!embed) return;

  global.document.documentElement.classList.add("embed-mode");

  function parentNav(tab, extra) {
    if (global.parent && global.parent !== global) {
      global.parent.postMessage({ type: "maum-nav", tab, ...extra }, "*");
      return true;
    }
    return false;
  }

  global.MaumEmbed = {
    isEmbed: true,
    goTab(tab, extra) {
      if (parentNav(tab, extra || {})) return;
      const map = { checkin: "/home", chat: "/chat", tarot: "/tarot" };
      global.location.href = map[tab] || "/";
    },
    goChatFromTarot() {
      if (parentNav("chat", { from_tarot: 1 })) return;
      global.location.href = "/chat?from_tarot=1";
    },
  };

  global.document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (!link) return;
    const href = link.getAttribute("href") || "";
    if (!href.startsWith("/") || href.startsWith("//")) return;
    const path = href.split("?")[0].split("#")[0];
    const tabMap = { "/": "chat", "/chat": "chat", "/home": "checkin", "/tarot": "tarot" };
    const tab = tabMap[path];
    if (tab && parentNav(tab, {})) {
      event.preventDefault();
    }
  });
})(window);
