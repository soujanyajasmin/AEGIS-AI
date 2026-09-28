/**
 * Real-Time Notification & Alerting Engine
 * Connects to Server-Sent Events (SSE), handles audio chimes,
 * displays interactive toasts, and triggers Web Notifications.
 */

class NotificationEngine {
    constructor() {
        this.toastContainer = null;
        this.audioCtx = null;
        this.initDOM();
        this.initAudio();
        this.initSSE();
        this.initBrowserNotifications();
    }

    initDOM() {
        let container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            container.className = "toast-container";
            document.body.appendChild(container);
        }
        this.toastContainer = container;
    }

    initAudio() {
        // Initialize Web Audio API for synthetic cyber chime
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                this.audioCtx = new AudioContext();
            }
        } catch (e) {
            console.warn("AudioContext not supported:", e);
        }
    }

    playAlertChime(severity = "warning") {
        if (!this.audioCtx) return;
        try {
            if (this.audioCtx.state === "suspended") {
                this.audioCtx.resume();
            }
            const now = this.audioCtx.currentTime;
            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();

            osc.connect(gain);
            gain.connect(this.audioCtx.destination);

            if (severity === "critical") {
                // High urgent double beep
                osc.type = "sawtooth";
                osc.frequency.setValueAtTime(880, now); // A5
                osc.frequency.setValueAtTime(440, now + 0.1);
                osc.frequency.setValueAtTime(880, now + 0.2);
                gain.gain.setValueAtTime(0.15, now);
                gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
                osc.start(now);
                osc.stop(now + 0.35);
            } else {
                // Soft chime
                osc.type = "sine";
                osc.frequency.setValueAtTime(587.33, now); // D5
                osc.frequency.exponentialRampToValueAtTime(880, now + 0.15); // A5
                gain.gain.setValueAtTime(0.1, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
                osc.start(now);
                osc.stop(now + 0.3);
            }
        } catch (e) {
            // Audio policy might require user gesture
        }
    }

    initBrowserNotifications() {
        if ("Notification" in window && Notification.permission === "default") {
            // Request permission on first user interaction
            document.addEventListener("click", () => {
                if (Notification.permission === "default") {
                    Notification.requestPermission();
                }
            }, { once: true });
        }
    }

    initSSE() {
        if (!window.EventSource) {
            console.warn("Server-Sent Events not supported. Falling back to polling.");
            this.startPollingFallback();
            return;
        }

        const source = new EventSource("/api/notifications/stream");

        source.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleNewNotification(data);
            } catch (e) {
                console.error("Error parsing SSE event:", e);
            }
        };

        source.onerror = () => {
            // Reconnection handled automatically by browser EventSource
        };
    }

    startPollingFallback() {
        let lastNotifId = 0;
        setInterval(() => {
            fetch("/api/notifications?limit=5")
                .then(res => res.json())
                .then(data => {
                    if (data.status === "success" && data.notifications.length > 0) {
                        const latest = data.notifications[0];
                        if (latest.id > lastNotifId && lastNotifId !== 0) {
                            this.handleNewNotification(latest);
                        }
                        lastNotifId = latest.id;
                    }
                })
                .catch(() => {});
        }, 5000);
    }

    handleNewNotification(notif) {
        // 1. Play Audio Chime
        this.playAlertChime(notif.severity);

        // 2. Render On-Screen Toast
        this.renderToast(notif);

        // 3. Update Nav Badges
        this.updateUnreadCount(1);

        // 4. Fire Web Notification if allowed
        if ("Notification" in window && Notification.permission === "granted") {
            try {
                new Notification(notif.title, {
                    body: notif.message,
                    icon: notif.snapshot_url || "/static/images/logo.png"
                });
            } catch (e) {}
        }
    }

    renderToast(notif) {
        const toast = document.createElement("div");
        toast.className = `toast toast-${notif.severity || 'warning'}`;

        let icon = "⚠️";
        if (notif.severity === "critical") icon = "🚨";
        else if (notif.severity === "info") icon = "ℹ️";

        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-content" style="flex: 1;">
                <h5>${escapeHTML(notif.title)}</h5>
                <p>${escapeHTML(notif.message)}</p>
                <div class="toast-time">${notif.time || 'Just now'}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
        `;

        if (notif.snapshot_url) {
            const img = document.createElement("img");
            img.src = notif.snapshot_url;
            img.className = "thumbnail-img";
            img.style.marginTop = "6px";
            toast.querySelector(".toast-content").appendChild(img);
        }

        this.toastContainer.appendChild(toast);

        // Auto remove after 7 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = "0";
                toast.style.transition = "opacity 0.5s ease";
                setTimeout(() => toast.remove(), 500);
            }
        }, 7000);
    }

    updateUnreadCount(delta = 1) {
        const badge = document.getElementById("nav-unread-badge");
        if (badge) {
            let current = parseInt(badge.textContent || "0");
            current = Math.max(0, current + delta);
            badge.textContent = current;
            badge.style.display = current > 0 ? "inline-block" : "none";
        }
    }
}

function escapeHTML(str) {
    if (!str) return "";
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

// Instantiate engine when DOM ready
document.addEventListener("DOMContentLoaded", () => {
    window.notificationEngine = new NotificationEngine();
});
