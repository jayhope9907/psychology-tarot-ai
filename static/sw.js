const CACHE = "maum-cache-v25";
const ASSETS = [
  "/static/manifest.json",
  "/static/icons/icon.svg",
  "/static/css/toss-ui.css",
  "/static/css/embed.css",
  "/static/js/embed-bridge.js",
  "/static/js/voice-engine.js",
  "/static/js/tarot-scene.js",
  "/static/js/tarot-offline.js",
  "/static/js/tarot-image-settings.js",
  "/static/js/chat-offline.js",
  "/static/js/maum-organism.js",
  "/static/js/vendor/three.min.js",
  "/static/tarot-deck.bundle.json",
  "/static/counsel-offline.bundle.json",
];

const BUNDLE_PATHS = new Set([
  "/static/tarot-deck.bundle.json",
  "/static/counsel-offline.bundle.json",
]);

const NETWORK_FIRST_PATHS = new Set([
  "/",
  "/home",
  "/chat",
  "/tarot",
  "/clinical",
  "/picture-assessment",
  "/psychometrics",
  "/legal",
  "/deploy",
]);

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/api/")) return;

  // HTML pages: always prefer network so chat/home fixes ship immediately
  if (
    event.request.mode === "navigate" ||
    NETWORK_FIRST_PATHS.has(url.pathname) ||
    (url.pathname.endsWith(".html"))
  ) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, copy)).catch(() => {});
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  if (BUNDLE_PATHS.has(url.pathname)) {
    event.respondWith(
      caches.match(event.request).then(
        (cached) =>
          cached ||
          fetch(event.request).then((response) => {
            const copy = response.clone();
            caches.open(CACHE).then((cache) => cache.put(event.request, copy));
            return response;
          })
      )
    );
    return;
  }

  // JS/CSS: stale-while-revalidate so deploys ship without waiting for purge
  if (
    url.pathname.startsWith("/static/js/")
    || url.pathname.startsWith("/static/css/")
    || url.pathname.endsWith(".js")
    || url.pathname.endsWith(".css")
  ) {
    event.respondWith(
      caches.open(CACHE).then(async (cache) => {
        const cached = await cache.match(event.request);
        const network = fetch(event.request)
          .then((response) => {
            cache.put(event.request, response.clone()).catch(() => {});
            return response;
          })
          .catch(() => cached);
        return cached || network;
      })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SCHEDULE_REMINDER") {
    const hour = event.data.hour || 21;
    scheduleDailyReminder(hour);
  }
});

function scheduleDailyReminder(hour) {
  const now = new Date();
  const next = new Date();
  next.setHours(hour, 0, 0, 0);
  if (next <= now) next.setDate(next.getDate() + 1);
  const delay = next.getTime() - now.getTime();
  setTimeout(() => {
    self.registration.showNotification("마음쉼터", {
      body: "오늘 마음은 어떤가요? 30초만 체크인해요.",
      icon: "/static/icons/icon.svg",
    });
    scheduleDailyReminder(hour);
  }, delay);
}
