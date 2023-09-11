const cacheFiles = [
    "/", 
    "/base_static/global.css", 
    "/build/bundle.css", 
    "/base_static/webfont.js", 
    "/build/bundle.js",
];

self.addEventListener("install", event => {
    console.log("[SW] Installing Service Worker...");
    event.waitUntil(
        caches.open("pwa-assets")
        .then(cache => {
            return cache.addAll(cacheFiles);
        })
    );
});

self.addEventListener("fetch", event => {
    console.log(event.request);
    event.respondWith(
        fetch(event.request)
        .catch(error => {
            return caches.match(event.request);
        })
    );
});