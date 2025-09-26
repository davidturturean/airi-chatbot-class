/**
 * AIRI Chatbot Real-time Metrics Dashboard
 */

// Configuration
const API_BASE_URL = 'http://localhost:8090'; // Update for production
const REFRESH_INTERVAL = 30000; // 30 seconds
const MAX_QUERY_ITEMS = 20;
const MAX_CHART_POINTS = 24; // 24 hours of data

// State
let latencyChart = null;
let volumeChart = null;
let refreshTimer = REFRESH_INTERVAL / 1000;

// Gate thresholds - REALISTIC VALUES (3000ms = 3 seconds, not 3ms!)
const DEPLOYMENT_GATES = {
    groundedness: { threshold: 0.95, operator: '>=', label: 'Groundedness', unit: '%', description: 'Percentage of response content backed by citations' },
    hallucination_rate: { threshold: 0.02, operator: '<=', label: 'Hallucination Rate', unit: '%', description: 'Percentage of unsupported claims' },
    retrieval_hit_rate: { threshold: 0.90, operator: '>=', label: 'Retrieval Hit Rate', unit: '%', description: 'Percentage of queries finding relevant documents' },
    latency_median: { threshold: 3000, operator: '<=', label: 'Median Latency', unit: 'ms', description: 'Middle response time value' },
    latency_p95: { threshold: 7000, operator: '<=', label: 'P95 Latency', unit: 'ms', description: '95% of responses faster than this' },
    containment_rate: { threshold: 0.60, operator: '>=', label: 'Containment Rate', unit: '%', description: 'Queries resolved without escalation' },
    satisfaction_score: { threshold: 0.70, operator: '>=', label: 'Satisfaction Score', unit: '%', description: 'User feedback rating' },
    cost_per_query: { threshold: 0.30, operator: '<=', label: 'Cost per Query', unit: '$', description: 'Average cost per query' },
    safety_violations: { threshold: 0, operator: '==', label: 'Safety Violations', unit: '', description: 'Number of safety issues detected' },
    freshness_hours: { threshold: 24, operator: '<=', label: 'Data Freshness', unit: 'h', description: 'Hours since last data update' }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    fetchMetrics();
    startRefreshTimer();
});

// Initialize Chart.js charts
function initializeCharts() {
    // Latency trend chart
    const latencyCtx = document.getElementById('latency-chart').getContext('2d');
    latencyChart = new Chart(latencyCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Median Latency',
                data: [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4
            }, {
                label: 'P95 Latency',
                data: [],
                borderColor: '#f093fb',
                backgroundColor: 'rgba(240, 147, 251, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Latency (ms)'
                    }
                }
            }
        }
    });
    
    // Query volume chart
    const volumeCtx = document.getElementById('volume-chart').getContext('2d');
    volumeChart = new Chart(volumeCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Queries per Hour',
                data: [],
                backgroundColor: '#667eea',
                borderColor: '#764ba2',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Query Count'
                    }
                }
            }
        }
    });
}

// Fetch metrics from API
async function fetchMetrics() {
    try {
        // Fetch dashboard data
        const dashboardResponse = await fetch(`${API_BASE_URL}/api/metrics/dashboard?hours=24`);
        const dashboardData = await dashboardResponse.json();
        
        // Fetch gates status
        const gatesResponse = await fetch(`${API_BASE_URL}/api/metrics/gates?hours=24`);
        const gatesData = await gatesResponse.json();
        
        // Update UI
        updateMetrics(dashboardData);
        updateGates(gatesData);
        updateCharts(dashboardData);
        updateSystemStatus(dashboardData, gatesData);
        
    } catch (error) {
        console.error('Failed to fetch metrics:', error);
        showError('Failed to connect to metrics API');
    }
}

// Update metric displays
function updateMetrics(data) {
    if (!data.global_metrics || !data.global_metrics.metrics) {
        return;
    }
    
    const metrics = data.global_metrics.metrics;
    
    // Update latency metrics
    document.getElementById('median-latency').textContent = 
        metrics.latency?.median_ms ? Math.round(metrics.latency.median_ms) : '--';
    document.getElementById('p95-latency').textContent = 
        metrics.latency?.p95_ms ? Math.round(metrics.latency.p95_ms) : '--';
    
    // Update success metrics
    const errorRate = metrics.quality?.error_rate || 0;
    const successRate = (1 - errorRate) * 100;
    document.getElementById('success-rate').textContent = 
        `${successRate.toFixed(1)}%`;
    
    const containmentRate = (metrics.engagement?.containment_rate || 0) * 100;
    document.getElementById('containment-rate').textContent = 
        `${containmentRate.toFixed(1)}%`;
    
    // Update cost metrics
    document.getElementById('cost-per-query').textContent = 
        metrics.cost?.per_query ? `$${metrics.cost.per_query.toFixed(3)}` : '$--';
    document.getElementById('total-queries').textContent = 
        data.global_metrics.total_queries || '--';
    
    // Update query stream
    updateQueryStream(data.recent_sessions);
}

// Update deployment gates display with clickable details
function updateGates(data) {
    const container = document.getElementById('gates-container');
    container.innerHTML = '';
    
    if (!data.gates) {
        container.innerHTML = '<div class="gate-status">No gate data available. Submit queries to generate metrics.</div>';
        return;
    }
    
    let passingCount = 0;
    const totalGates = Object.keys(data.gates).length;
    
    for (const [gateName, gateData] of Object.entries(data.gates)) {
        const gateConfig = DEPLOYMENT_GATES[gateName];
        if (!gateConfig) continue;
        
        const passing = gateData.passing;
        if (passing) passingCount++;
        
        const gateElement = document.createElement('div');
        gateElement.className = `gate-status ${passing ? 'passing' : 'failing'}`;
        gateElement.style.cursor = 'pointer';
        gateElement.onclick = () => showMetricDetails(gateName);
        
        // Don't show failing indicator for metrics that are expected to be good
        // Just show the actual values without red/green judgment for now
        const value = formatGateValue(gateData.value, gateConfig.unit);
        const threshold = formatGateValue(gateData.threshold, gateConfig.unit);
        
        gateElement.innerHTML = `
            <div>
                <strong>${gateConfig.label}</strong>
                <span class="info-icon" title="${gateConfig.description}. Click for details.">ⓘ</span>
            </div>
            <div>
                ${value} (target: ${threshold})
            </div>
        `;
        
        container.appendChild(gateElement);
    }
    
    // Update deployment recommendation
    const recommendation = document.getElementById('deployment-recommendation');
    const ready = passingCount >= 8;
    recommendation.className = `deployment-recommendation ${ready ? 'ready' : 'not-ready'}`;
    
    if (passingCount >= 10) {
        recommendation.innerHTML = '🎉 Ready for full deployment!';
    } else if (passingCount >= 8) {
        recommendation.innerHTML = '✅ Ready for canary deployment (5-10% traffic)';
    } else if (passingCount >= 6) {
        recommendation.innerHTML = '🔄 Ready for expanded beta testing';
    } else {
        recommendation.innerHTML = '⚠️ Continue internal testing and optimization';
    }
    
    recommendation.innerHTML += `<br><small>${passingCount}/${totalGates} gates passing</small>`;
}

// Format gate values
function formatGateValue(value, unit) {
    if (unit === '%') {
        return `${(value * 100).toFixed(1)}%`;
    } else if (unit === '$') {
        return `$${value.toFixed(2)}`;
    } else if (unit === 'ms') {
        return `${Math.round(value)}ms`;
    } else if (unit === 'h') {
        return `${value}h`;
    } else if (value < 1) {
        return `${(value * 100).toFixed(1)}%`;
    } else {
        return value.toFixed(2);
    }
}

// Update charts with REAL data from API - NO MOCK DATA
async function updateCharts(data) {
    try {
        // Fetch REAL hourly data from API
        const response = await fetch(`${API_BASE_URL}/api/metrics/hourly?hours=24`);
        const hourlyData = await response.json();
        
        if (!hourlyData.hourly_breakdown || hourlyData.hourly_breakdown.length === 0) {
            // No data available - show message, don't generate fake data
            showNoDataMessage();
            return;
        }
        
        // Use ACTUAL data from database
        const hours = hourlyData.hourly_breakdown;
        const labels = hours.map(h => {
            const date = new Date(h.hour);
            return `${date.getHours()}:00`;
        });
        const medianData = hours.map(h => h.median_latency || 0);
        const p95Data = hours.map(h => h.p95_latency || 0);
        const volumeData = hours.map(h => h.query_count || 0);
        
        // Update latency chart with REAL data
        latencyChart.data.labels = labels;
        latencyChart.data.datasets[0].data = medianData;
        latencyChart.data.datasets[1].data = p95Data;
        latencyChart.update();
        
        // Update volume chart with REAL data
        volumeChart.data.labels = labels;
        volumeChart.data.datasets[0].data = volumeData;
        volumeChart.update();
        
    } catch (error) {
        console.error('Failed to fetch hourly metrics:', error);
        showNoDataMessage();
    }
}

// Show message when no data is available
function showNoDataMessage() {
    // Update charts to show "No data" message
    const emptyLabels = ['No data available'];
    const emptyData = [0];
    
    latencyChart.data.labels = emptyLabels;
    latencyChart.data.datasets[0].data = emptyData;
    latencyChart.data.datasets[1].data = emptyData;
    latencyChart.update();
    
    volumeChart.data.labels = emptyLabels;
    volumeChart.data.datasets[0].data = emptyData;
    volumeChart.update();
    
    // Add message to charts
    document.querySelectorAll('.chart-container').forEach(container => {
        if (!container.querySelector('.no-data-message')) {
            const message = document.createElement('div');
            message.className = 'no-data-message';
            message.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(255,255,255,0.9); padding: 20px; border-radius: 10px; font-weight: bold;';
            message.textContent = 'Submit queries to see metrics';
            container.appendChild(message);
        }
    });
}

// Update query stream
function updateQueryStream(sessions) {
    const container = document.getElementById('query-stream');
    container.innerHTML = '';
    
    if (!sessions || sessions.length === 0) {
        container.innerHTML = '<div class="query-item">No recent queries</div>';
        return;
    }
    
    // Show last N queries
    sessions.slice(0, MAX_QUERY_ITEMS).forEach(session => {
        const queryElement = document.createElement('div');
        queryElement.className = 'query-item';
        
        const time = new Date(session.start_time).toLocaleTimeString();
        const latency = session.avg_latency_ms ? 
            `${Math.round(session.avg_latency_ms)}ms` : '--';
        
        queryElement.innerHTML = `
            <div><strong>Session:</strong> ${session.session_id.substring(0, 8)}...</div>
            <div>Queries: ${session.query_count} | Avg Latency: ${latency}</div>
            <div class="query-time">${time}</div>
        `;
        
        container.appendChild(queryElement);
    });
}

// System status instead of alerts
function updateSystemStatus(dashboardData, gatesData) {
    const container = document.getElementById('system-status-container');
    if (!container) {
        // Replace alerts container with system status
        const alertsCard = document.querySelector('#alerts-container').parentElement;
        alertsCard.querySelector('h2').textContent = '📊 System Status';
        alertsCard.querySelector('#alerts-container').id = 'system-status-container';
        return updateSystemStatus(dashboardData, gatesData);
    }
    
    container.innerHTML = '';
    
    const totalQueries = dashboardData?.global_metrics?.total_queries || 0;
    
    if (totalQueries === 0) {
        container.innerHTML = `
            <div class="system-status">
                <h3>No Data Available</h3>
                <p>Submit queries to the chatbot to start seeing metrics.</p>
                <p>The dashboard will update automatically as data comes in.</p>
            </div>
        `;
    } else {
        const lastHour = new Date(Date.now() - 3600000).toISOString();
        container.innerHTML = `
            <div class="system-status">
                <h3>System Operational</h3>
                <p><strong>${totalQueries}</strong> queries processed in last 24 hours</p>
                <p>Data quality: ${gatesData?.gates_passing || 0}/${gatesData?.gates_total || 10} metrics meeting targets</p>
                <p>Last update: ${new Date().toLocaleTimeString()}</p>
            </div>
        `;
    }
}

// Add function to show metric details
function showMetricDetails(metricName) {
    // Fetch and display actual query details
    fetch(`${API_BASE_URL}/api/metrics/details/${metricName}`)
        .then(response => response.json())
        .then(data => {
            // Create modal or expand section to show details
            const modal = document.createElement('div');
            modal.className = 'metric-details-modal';
            modal.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 50px rgba(0,0,0,0.3);
                max-width: 80%;
                max-height: 80vh;
                overflow-y: auto;
                z-index: 1000;
            `;
            
            modal.innerHTML = `
                <h2>${data.metric} Details</h2>
                <p>${data.description || ''}</p>
                <p><strong>Total:</strong> ${data.total || 0} queries</p>
                <p><strong>Passing:</strong> ${data.passing || 0} (${data.percentage?.toFixed(1) || 0}%)</p>
                <h3>Recent Queries:</h3>
                <div style="max-height: 400px; overflow-y: auto;">
                    ${(data.details || []).map(d => `
                        <div style="padding: 10px; margin: 5px 0; background: #f5f5f5; border-radius: 5px;">
                            <strong>Query:</strong> ${d.query}<br>
                            <strong>Score:</strong> ${d.groundedness_score?.toFixed(2) || d.latency_ms || 'N/A'}<br>
                            <strong>Time:</strong> ${new Date(d.timestamp).toLocaleString()}
                        </div>
                    `).join('')}
                </div>
                <button onclick="this.parentElement.remove(); document.getElementById('modal-overlay').remove()" 
                        style="margin-top: 20px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    Close
                </button>
            `;
            
            // Add overlay
            const overlay = document.createElement('div');
            overlay.id = 'modal-overlay';
            overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 999;';
            overlay.onclick = () => {
                modal.remove();
                overlay.remove();
            };
            
            document.body.appendChild(overlay);
            document.body.appendChild(modal);
        })
        .catch(error => {
            console.error('Failed to fetch metric details:', error);
        });
}

// Show error message
function showError(message) {
    const container = document.getElementById('alerts-container');
    const alertElement = document.createElement('div');
    alertElement.className = 'alert error';
    alertElement.textContent = message;
    container.prepend(alertElement);
}

// Refresh timer
function startRefreshTimer() {
    setInterval(() => {
        refreshTimer--;
        document.getElementById('refresh-countdown').textContent = refreshTimer;
        
        if (refreshTimer <= 0) {
            refreshTimer = REFRESH_INTERVAL / 1000;
            fetchMetrics();
        }
    }, 1000);
}

// Auto-refresh
setInterval(fetchMetrics, REFRESH_INTERVAL);