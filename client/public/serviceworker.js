const cacheFiles = [
    "/", 
    "/base_static/global.css", 
    "/build/bundle.css", 
    "/base_static/webfont.js", 
    "/build/bundle.js",
    "/base_static/images/better_vp_white.svg",
    "/base_static/fonts/material_icons/kJF1BvYX7BgnkSrUwT8OhrdQw4oELdPIeeII9v6oDMzByHX9rA6RzaxHMPdY43zj-jCxv3fzvRNU22ZXGJpEpjC_1n-q_4MrImHCIJIZrDCvHOej.woff2",
    "/base_static/favicon.png"
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
    event.respondWith(
        fetch(event.request)
        .catch(error => {
            return caches.match(event.request);
        })
    );
});