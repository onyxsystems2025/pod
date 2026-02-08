/**
 * POD Corriere - Progressive Web App
 * Form POD con firma digitale, foto, GPS
 */

const API_BASE = '/api/v1';
let authToken = null;
let currentShipment = null;
let signatureCanvas = null;
let signatureCtx = null;
let isDrawing = false;
let capturedPhotos = [];

// ============================================================
// Init
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    // Register service worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/pwa/sw.js')
            .then(reg => console.log('SW registered'))
            .catch(err => console.error('SW registration failed:', err));
    }

    // Check auth
    authToken = localStorage.getItem('pod_token');
    if (authToken) {
        showScreen('shipments');
        loadShipments();
    } else {
        showScreen('login');
    }

    // Online/offline status
    updateOnlineStatus();
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);
});

function updateOnlineStatus() {
    const el = document.getElementById('connection-status');
    if (navigator.onLine) {
        el.textContent = 'Online';
        el.className = 'status online';
        // Try to sync offline records
        if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
            navigator.serviceWorker.ready.then(reg => reg.sync.register('pod-sync'));
        }
    } else {
        el.textContent = 'Offline';
        el.className = 'status offline';
    }
}

function showScreen(name) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const screen = document.getElementById(`screen-${name}`);
    if (screen) screen.classList.add('active');
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// ============================================================
// Auth
// ============================================================

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const res = await fetch(`${API_BASE}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        if (!res.ok) {
            showToast('Credenziali non valide');
            return;
        }

        const data = await res.json();
        authToken = data.access;
        localStorage.setItem('pod_token', data.access);
        localStorage.setItem('pod_refresh', data.refresh);

        // Store in IndexedDB for service worker
        const db = await openDB();
        const tx = db.transaction('auth', 'readwrite');
        tx.objectStore('auth').put({ key: 'access_token', value: data.access });

        showScreen('shipments');
        loadShipments();
    } catch (err) {
        showToast('Errore di connessione');
    }
}

function logout() {
    localStorage.removeItem('pod_token');
    localStorage.removeItem('pod_refresh');
    authToken = null;
    showScreen('login');
}

function apiHeaders() {
    return {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
    };
}

// ============================================================
// Shipments
// ============================================================

async function loadShipments() {
    try {
        const res = await fetch(`${API_BASE}/driver/shipments/today/`, {
            headers: apiHeaders(),
        });

        if (res.status === 401) {
            logout();
            return;
        }

        const data = await res.json();
        renderShipments(data.results || data);
    } catch (err) {
        showToast('Errore caricamento spedizioni');
    }
}

function renderShipments(shipments) {
    const container = document.getElementById('shipments-list');
    if (shipments.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#6b7280;padding:2rem;">Nessuna spedizione per oggi</p>';
        return;
    }

    container.innerHTML = shipments.map(s => `
        <div class="shipment-card" onclick="openShipment('${s.uuid}', ${JSON.stringify(s).replace(/'/g, "\\'").replace(/"/g, '&quot;')})">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span class="tracking">${s.tracking_code}</span>
                <span class="badge badge-${s.status}">${s.status}</span>
            </div>
            <div class="recipient">${s.recipient_name}</div>
            <div class="address">${s.delivery_address_display || ''}</div>
            <div class="meta">
                <span>${s.packages_count} colli</span>
                <span>${s.estimated_delivery_date || ''}</span>
            </div>
        </div>
    `).join('');
}

function openShipment(uuid, shipment) {
    currentShipment = typeof shipment === 'string' ? JSON.parse(shipment) : shipment;
    currentShipment.uuid = uuid;

    document.getElementById('pod-tracking').textContent = currentShipment.tracking_code;
    document.getElementById('pod-recipient').textContent = currentShipment.recipient_name;
    document.getElementById('pod-address').textContent = currentShipment.delivery_address_display || '';

    // Reset form
    document.getElementById('pod-result').value = 'delivered';
    document.getElementById('pod-signer').value = '';
    document.getElementById('pod-notes').value = '';
    capturedPhotos = [];
    renderPhotos();

    showScreen('pod-form');
    initSignatureCanvas();
}

function backToList() {
    showScreen('shipments');
    currentShipment = null;
}

// ============================================================
// Signature Canvas
// ============================================================

function initSignatureCanvas() {
    signatureCanvas = document.getElementById('signature-canvas');
    signatureCtx = signatureCanvas.getContext('2d');

    // Set actual size
    const rect = signatureCanvas.getBoundingClientRect();
    signatureCanvas.width = rect.width;
    signatureCanvas.height = 200;

    // Clear
    clearSignature();

    // Touch events
    signatureCanvas.addEventListener('touchstart', startDrawing, { passive: false });
    signatureCanvas.addEventListener('touchmove', draw, { passive: false });
    signatureCanvas.addEventListener('touchend', stopDrawing);

    // Mouse events (for testing)
    signatureCanvas.addEventListener('mousedown', startDrawing);
    signatureCanvas.addEventListener('mousemove', draw);
    signatureCanvas.addEventListener('mouseup', stopDrawing);
    signatureCanvas.addEventListener('mouseleave', stopDrawing);
}

function getPos(e) {
    const rect = signatureCanvas.getBoundingClientRect();
    if (e.touches) {
        return {
            x: e.touches[0].clientX - rect.left,
            y: e.touches[0].clientY - rect.top,
        };
    }
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
}

function startDrawing(e) {
    e.preventDefault();
    isDrawing = true;
    const pos = getPos(e);
    signatureCtx.beginPath();
    signatureCtx.moveTo(pos.x, pos.y);
}

function draw(e) {
    if (!isDrawing) return;
    e.preventDefault();
    const pos = getPos(e);
    signatureCtx.lineWidth = 2.5;
    signatureCtx.lineCap = 'round';
    signatureCtx.strokeStyle = '#111';
    signatureCtx.lineTo(pos.x, pos.y);
    signatureCtx.stroke();
}

function stopDrawing() {
    isDrawing = false;
}

function clearSignature() {
    if (signatureCtx) {
        signatureCtx.fillStyle = '#fff';
        signatureCtx.fillRect(0, 0, signatureCanvas.width, signatureCanvas.height);
    }
}

function getSignatureBlob() {
    return new Promise((resolve) => {
        signatureCanvas.toBlob(resolve, 'image/png');
    });
}

// ============================================================
// Camera / Photos
// ============================================================

function capturePhoto() {
    const input = document.getElementById('photo-input');
    input.click();
}

document.addEventListener('change', (e) => {
    if (e.target.id === 'photo-input') {
        const file = e.target.files[0];
        if (file) {
            // Resize image before storing
            resizeImage(file, 1920, 0.8).then(blob => {
                capturedPhotos.push(blob);
                renderPhotos();
            });
        }
        e.target.value = '';
    }
});

function resizeImage(file, maxWidth, quality) {
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let w = img.width;
                let h = img.height;
                if (w > maxWidth) {
                    h = (h * maxWidth) / w;
                    w = maxWidth;
                }
                canvas.width = w;
                canvas.height = h;
                canvas.getContext('2d').drawImage(img, 0, 0, w, h);
                canvas.toBlob(resolve, 'image/jpeg', quality);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    });
}

function renderPhotos() {
    const grid = document.getElementById('photo-grid');
    grid.innerHTML = capturedPhotos.map((blob, i) => {
        const url = URL.createObjectURL(blob);
        return `<img src="${url}" alt="Foto ${i + 1}">`;
    }).join('') + `<div class="photo-add" onclick="capturePhoto()">+</div>`;
}

function removeLastPhoto() {
    if (capturedPhotos.length > 0) {
        capturedPhotos.pop();
        renderPhotos();
    }
}

// ============================================================
// GPS
// ============================================================

function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            resolve({ latitude: null, longitude: null });
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => resolve({
                latitude: pos.coords.latitude,
                longitude: pos.coords.longitude,
            }),
            () => resolve({ latitude: null, longitude: null }),
            { enableHighAccuracy: true, timeout: 10000 }
        );
    });
}

// ============================================================
// Submit POD
// ============================================================

async function submitPOD() {
    if (!currentShipment) return;

    const submitBtn = document.getElementById('pod-submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Invio in corso...';

    try {
        const gps = await getCurrentPosition();
        const signatureBlob = await getSignatureBlob();

        const formData = new FormData();
        formData.append('delivery_result', document.getElementById('pod-result').value);
        formData.append('recipient_signer_name', document.getElementById('pod-signer').value);
        formData.append('notes', document.getElementById('pod-notes').value);
        formData.append('recorded_at', new Date().toISOString());
        if (gps.latitude) formData.append('latitude', gps.latitude);
        if (gps.longitude) formData.append('longitude', gps.longitude);
        if (signatureBlob) formData.append('signature_image', signatureBlob, 'signature.png');

        // Device ID for offline dedup
        let deviceUUID = localStorage.getItem('device_uuid');
        if (!deviceUUID) {
            deviceUUID = crypto.randomUUID();
            localStorage.setItem('device_uuid', deviceUUID);
        }
        formData.append('device_uuid', deviceUUID);
        formData.append('local_record_id', crypto.randomUUID());

        if (navigator.onLine) {
            // Online: submit directly
            const res = await fetch(`${API_BASE}/driver/shipments/${currentShipment.uuid}/pod/`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authToken}` },
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                showToast('Errore: ' + (err.error || 'invio fallito'));
                return;
            }

            const podRecord = await res.json();

            // Upload photos
            for (const photo of capturedPhotos) {
                const photoData = new FormData();
                photoData.append('image', photo, `photo_${Date.now()}.jpg`);
                await fetch(`${API_BASE}/pod/${podRecord.uuid}/photos/`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${authToken}` },
                    body: photoData,
                });
            }

            showToast('POD registrato con successo!');
        } else {
            // Offline: save to IndexedDB
            const db = await openDB();
            const tx = db.transaction('pending_pods', 'readwrite');
            tx.objectStore('pending_pods').add({
                data: {
                    shipment_uuid: currentShipment.uuid,
                    delivery_result: document.getElementById('pod-result').value,
                    recipient_signer_name: document.getElementById('pod-signer').value,
                    notes: document.getElementById('pod-notes').value,
                    recorded_at: new Date().toISOString(),
                    latitude: gps.latitude,
                    longitude: gps.longitude,
                    device_uuid: deviceUUID,
                    local_record_id: crypto.randomUUID(),
                },
                timestamp: Date.now(),
            });

            showToast('POD salvato offline. Verra sincronizzato automaticamente.');

            // Register background sync
            if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
                const reg = await navigator.serviceWorker.ready;
                await reg.sync.register('pod-sync');
            }
        }

        // Back to list
        showScreen('shipments');
        loadShipments();
    } catch (err) {
        console.error('Submit POD error:', err);
        showToast('Errore durante il salvataggio');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Conferma consegna';
    }
}

// ============================================================
// IndexedDB Helper
// ============================================================

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
