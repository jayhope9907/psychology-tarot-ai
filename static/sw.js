const CACHE = "maum-cache-v2";
const ASSETS = ["/", "/home", "/chat", "/tarot", "/legal", "/static/css/toss-ui.css", "/static/css/embed.css"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).catch(() => {}));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
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
