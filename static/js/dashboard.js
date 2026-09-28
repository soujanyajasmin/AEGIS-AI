/**
 * Dashboard Controller & Live Telemetry
 */

let hourlyChart = null;

function initHourlyChart(labels, data) {
    const ctx = document.getElementById("hourlyEventsChart");
    if (!ctx) return;

    if (hourlyChart) {
        hourlyChart.destroy();
    }

    hourlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: "Detections Today",
                data: data,
                borderColor: '#388bfd',
                backgroundColor: 'rgba(56, 139, 253, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: '#58a6ff',
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: '#21262d' },
                    ticks: { color: '#8b949e', maxTicksLimit: 12 }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: '#21262d' },
                    ticks: { color: '#8b949e', stepSize: 1 }
                }
            }
        }
    });
}

function refreshDashboardMetrics() {
    fetch("/api/statistics")
        .then(res => res.json())
        .then(res => {
            if (res.status === "success") {
                const m = res.metrics;
                setText("stat-today-events", m.today_events);
                setText("stat-people-detected", m.people_detected);
                setText("stat-known-people", m.known_people);
                setText("stat-unknown-people", m.unknown_people);
                setText("stat-vehicles", m.vehicles);
                setText("stat-animals", m.animals);
                setText("stat-storage-used", `${m.storage_used_mb} MB`);

                // Update Chart
                if (hourlyChart && res.hourly_chart) {
                    hourlyChart.data.labels = res.hourly_chart.labels;
                    hourlyChart.data.datasets[0].data = res.hourly_chart.data;
                    hourlyChart.update('none');
                }

                // Update Camera status pill
                updateCameraStatusPill(res.camera_status);
            }
        })
        .catch(err => console.error("Error polling metrics:", err));
}

function updateCameraStatusPill(status) {
    const pill = document.getElementById("camera-status-indicator");
    if (!pill) return;

    if (status.online) {
        pill.className = "camera-status-pill";
        pill.innerHTML = `<span class="pulse-dot"></span> 🟢 Camera Online (${status.fps} FPS)`;
    } else {
        pill.className = "camera-status-pill offline";
        pill.innerHTML = `<span class="pulse-dot"></span> 🔴 Camera Offline`;
    }
}

function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

document.addEventListener("DOMContentLoaded", () => {
    // Initial fetch
    refreshDashboardMetrics();
    // Poll every 5 seconds for telemetry
    setInterval(refreshDashboardMetrics, 5000);
});
