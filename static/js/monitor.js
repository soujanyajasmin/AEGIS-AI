/**
 * Live Monitoring Console Controller
 */

function sendCameraCommand(action) {
    const validActions = ['start', 'stop', 'pause', 'resume', 'snapshot'];
    if (!validActions.includes(action)) return;

    fetch(`/api/camera/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            if (action === "snapshot") {
                alert(`Snapshot saved successfully!\nPath: ${data.snapshot_path}`);
            }
            refreshCameraControls();
        } else {
            alert(`Error: ${data.message || 'Operation failed'}`);
        }
    })
    .catch(err => {
        console.error("Camera command error:", err);
    });
}

function handleCameraSwitch(selectEl) {
    const camId = selectEl.value;
    if (!camId) return;

    fetch("/api/camera/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ camera_id: parseInt(camId) })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            // Reload stream by re-setting src
            const streamImg = document.getElementById("main-video-feed");
            if (streamImg) {
                streamImg.src = "/video_feed?t=" + new Date().getTime();
            }
            refreshCameraControls();
        } else {
            alert("Failed to switch camera: " + data.message);
        }
    });
}

function refreshCameraControls() {
    fetch("/api/camera/status")
        .then(res => res.json())
        .then(status => {
            const startBtn = document.getElementById("btn-start");
            const stopBtn = document.getElementById("btn-stop");
            const pauseBtn = document.getElementById("btn-pause");
            const resumeBtn = document.getElementById("btn-resume");

            if (startBtn && stopBtn && pauseBtn && resumeBtn) {
                if (status.running) {
                    startBtn.style.display = "none";
                    stopBtn.style.display = "inline-flex";

                    if (status.paused) {
                        pauseBtn.style.display = "none";
                        resumeBtn.style.display = "inline-flex";
                    } else {
                        pauseBtn.style.display = "inline-flex";
                        resumeBtn.style.display = "none";
                    }
                } else {
                    startBtn.style.display = "inline-flex";
                    stopBtn.style.display = "none";
                    pauseBtn.style.display = "none";
                    resumeBtn.style.display = "none";
                }
            }

            // Update FPS and status text
            const infoText = document.getElementById("stream-fps-counter");
            if (infoText) {
                infoText.textContent = `${status.fps} FPS | ${status.active_tracks_count} Active Track(s)`;
            }

            const streamImg = document.getElementById("main-video-feed");
            if (streamImg && !status.running) {
                // If stopped, keep image connection clear
            }
        });
}

document.addEventListener("DOMContentLoaded", () => {
    refreshCameraControls();
    setInterval(refreshCameraControls, 3000);
});
