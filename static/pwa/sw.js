const CACHE_NAME = 'pod-v1';
const STATIC_ASSETS = [
    '/pwa/',
    '/static/pwa/app.js',
    '/static/pwa/app.css',
    '/static/pwa/manifest.json',
    '/pwa/offline/',
];

// Install: cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            )
        )
    );
    self.clients.claim();
});

// Fetch: network-first for API, cache-first for static
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // API requests: network only (offline handled by app)
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() =>
                new Response(JSON.stringify({ offline: true }), {
                    headers: { 'Content-Type': 'application/json' },
                    status: 503,
                })
            )
        );
        return;
    }

    // Static assets: cache first
    event.respondWith(
        caches.match(event.request).then((cached) => {
            return cached || fetch(event.request).then((response) => {
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                }
                return response;
            });
        }).catch(() => {
            if (event.request.mode === 'navigate') {
                return caches.match('/pwa/offline/');
            }
        })
    );
});

// Background sync for offline POD records
self.addEventListener('sync', (event) => {
    if (event.tag === 'pod-sync') {
        event.waitUntil(syncOfflinePODs());
    }
});

async function syncOfflinePODs() {
    // Get pending records from IndexedDB
    const db = await openDB();
    const tx = db.transaction('pending_pods', 'readonly');
    const store = tx.objectStore('pending_pods');
    const records = await getAllFromStore(store);

    for (const record of records) {
        try {
            const token = await getStoredToken();
            const response = await fetch('/api/v1/pod/sync/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify([record.data]),
            });

            if (response.ok) {
                // Remove synced record
                const deleteTx = db.transaction('pending_pods', 'readwrite');
                deleteTx.objectStore('pending_pods').delete(record.id);
            }
        } catch (e) {
            console.error('Sync failed for record:', record.id, e);
        }
    }
}

function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('pod_db', 1);
        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains('pending_pods')) {
                db.createObjectStore('pending_pods', { keyPath: 'id', autoIncrement: true });
            }
            if (!db.objectStoreNames.contains('auth')) {
                db.createObjectStore('auth', { keyPath: 'key' });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function getAllFromStore(store) {
    return new Promise((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

async function getStoredToken() {
    const db = await openDB();
    const tx = db.transaction('auth', 'readonly');
    const store = tx.objectStore('auth');
    return new Promise((resolve) => {
        const request = store.get('access_token');
        request.onsuccess = () => resolve(request.result?.value || '');
        request.onerror = () => resolve('');
    });
}
