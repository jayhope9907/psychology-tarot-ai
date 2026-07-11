const CACHE = "maum-cache-v6";
const ASSETS = [
  "/",
  "/home",
  "/chat",
  "/tarot",
  "/picto",
  "/clinical",
  "/picture-assessment",
  "/legal",
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
  "/static/picto-catalog.bundle.json",
  "/static/tarot-deck.bundle.json",
  "/static/counsel-offline.bundle.json",
];

const BUNDLE_PATHS = new Set([
  "/static/picto-catalog.bundle.json",
  "/static/tarot-deck.bundle.json",
  "/static/counsel-offline.bundle.json",
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
      body: "오늘 마음 체크인, 30초면 충분해요 🌙",
      icon: "/static/icons/icon.svg",
      tag: "evening-checkin",
    });
    scheduleDailyReminder(hour);
  }, delay);
}
