const CACHE = 'famcal-v2';  // bump version to force reload

const ASSETS = [
  '/',
  '/index.html',
  '/calendar.html',
  '/assets/styles.css',
  '/manifest.json'
];

// Install: cache essential assets
self.addEventListener('install', (event) => {
  self.skipWaiting();  // take over immediately
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS))
  );
});

// Activate: clear old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(key => {
        if (key !== CACHE) {
          return caches.delete(key);
        }
      }))
    ).then(() => self.clients.claim())
  );
});

// Fetch handler
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API: always try network first
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
    return;
  }

  // App shell (HTML, CSS, JS): try network first, fallback to cache
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Save fresh copy to cache
        const clone = response.clone();
        caches.open(CACHE).then(cache => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
