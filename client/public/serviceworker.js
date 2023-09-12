// Don't judge me, ich wollte nicht so viele Fehler in der Konsole :(
const cacheFiles = [
    "/", 
    "/base_static/global.css", 
    "/build/bundle.css", 
    "/base_static/webfont.js", 
    "/build/bundle.js",
    "/base_static/site.webmanifest",
    "/base_static/images/better_vp_white.svg",
    "/base_static/fonts/material_icons/kJF1BvYX7BgnkSrUwT8OhrdQw4oELdPIeeII9v6oDMzByHX9rA6RzaxHMPdY43zj-jCxv3fzvRNU22ZXGJpEpjC_1n-q_4MrImHCIJIZrDCvHOej.woff2",
    "/base_static/favicon.png",
    "/base_static/icons/favicon.ico",
    "/base_static/icons/favicon-16x16.png",
    "/base_static/icons/favicon-32x32.png",
    "/base_static/fonts/poppins/poppins-v20-latin-100.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-100italic.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-200.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-200italic.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-300.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-300italic.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-500.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-500italic.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-600.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-600italic.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-700.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-700italic.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-800.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-800italic.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-900.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-900italic.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-italic.woff2", 
    "/base_static/fonts/poppins/poppins-v20-latin-regular.woff2",
];

self.addEventListener("install", event => {
    console.log("[SW] Installing Service Worker...");
    event.waitUntil(
        caches.open("cache")
        .then(cache => {
            return cache.addAll(cacheFiles);
        })
    );
});

self.addEventListener('activate', event => {
    console.log("[SW] Activating Service Worker...");
    const currentCaches = ['cache'];
    event.waitUntil(
        caches.keys().then(cacheNames => {
        return cacheNames.filter(cacheName => !currentCaches.includes(cacheName));
        }).then(cachesToDelete => {
            return Promise.all(cachesToDelete.map(cacheToDelete => {
                return caches.delete(cacheToDelete);
            }));
        }).then(() => self.clients.claim())
    );
});

self.addEventListener("fetch", event => {
    let tmp_url_obj = new URL(event.request.url);
    if(!tmp_url_obj.pathname.startsWith("/api/") && !tmp_url_obj.pathname.startsWith("/auth/")) {
        event.respondWith(
            fetch(event.request)
            .then((res) => {
                return caches.open('cache')
                    .then(function(cache) {
                        cache.put(tmp_url_obj.pathname.startsWith("/#") ? event.request.url.split("/#")[0] + "/" : event.request.url, res.clone());
                        return res;
                    })
            })
            .catch(error => {
                return caches.match(event.request);
            })
        );
    }
});