const CACHE_NAME = "obamify-pwa-v2"
const FILES_TO_CACHE = ["./", "./index.html", "./styles.css", "./manifest.json"]

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(FILES_TO_CACHE))
    )
})

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches
            .keys()
            .then((names) => names.filter((name) => name !== CACHE_NAME))
            .then((stale) => Promise.all(stale.map((name) => caches.delete(name))))
    )
})

self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((cached) => cached || fetch(event.request))
    )
})
