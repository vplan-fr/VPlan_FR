// Don't judge me, ich wollte nicht so viele Fehler in der Konsole :(
const cacheFiles = [
    "/",
    "/public/base_static/global.css",
    "/public/build/bundle.css",
    "/public/base_static/webfont.js",
    "/public/build/bundle.js",
    "/public/base_static/site.webmanifest",
    "/public/base_static/images/better_vp_white.svg",
    "/public/base_static/fonts/material_icons/kJF1BvYX7BgnkSrUwT8OhrdQw4oELdPIeeII9v6oDMzByHX9rA6RzaxHMPdY43zj-jCxv3fzvRNU22ZXGJpEpjC_1n-q_4MrImHCIJIZrDCvHOej.woff2",
    "/public/base_static/favicon.png",
    "/public/base_static/icons/favicon.ico",
    "/public/base_static/icons/favicon-16x16.png",
    "/public/base_static/icons/favicon-32x32.png",
    "/public/base_static/fonts/poppins/poppins-v20-latin-100.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-100italic.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-200.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-200italic.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-300.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-300italic.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-500.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-500italic.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-600.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-600italic.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-700.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-700italic.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-800.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-800italic.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-900.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-900italic.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-italic.woff2",
    "/public/base_static/fonts/poppins/poppins-v20-latin-regular.woff2",
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
    if (tmp_url_obj.pathname.startsWith("/public/") || tmp_url_obj.pathname === "/") {
        event.respondWith(
            fetch(event.request)
                .then((res) => {
                    return caches.open('cache')
                        .then(function (cache) {
                            cache.put(event.request.url, res.clone());
                            return res;
                        })
                })
                .catch(error => {
                    return caches.match(event.request);
                })
        );
    }
});

self.addEventListener('push', (event) => {
    obj = event.data.json();
    console.log(obj);
    if (obj.type === "new-revision-available") {
        self.registration.showNotification("Neuer Plan verfügbar", {
            body: `Tag: ${obj.data.date}. Uhrzeit: ${obj.data.revision}.`,
            icon: "/public/base_static/icons/favicon.ico",
            data: {
                url: `/#plan|${obj.data.school_number}|${obj.data.date}`
            }
        }).then(() => {
           self.registration.getNotifications().then(
            (notifications) => {
                console.log(notifications);
                notifications.forEach((notification) => {
                    if (notification.data.url != null) {
                        notification.addEventListener('click', (event) => {
                            let tmp_url_obj = new URL(event.target.data.url);
                            console.log(tmp_url_obj);
                            self.clients.openWindow(event.target.data.url);
                        });
                    }
                });
            }
        );
        });
    }

    // self.registration.showNotification('Hello world!', options);
});