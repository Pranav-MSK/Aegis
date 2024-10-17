// Function to create a chart
function createChart(ctx, title, labels, datasets) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 300,
                easing: 'easeInOutQuad'
            },
            scales: {
                y: {
                    display: true,
                    beginAtZero: true,
                    grid: { display: false, color: 'rgba(200, 200, 200, 0.2)' },
                    ticks: {
                        callback: value => `${value}%`,
                        color: '#6b7280'
                    },
                    title: {
                        display: true,
                        text: 'Percentage',
                        color: '#6b7280',
                        font: { size: 14, weight: 'bold' }
                    }
                },
                x: {
                    display: true,
                    grid: { display: false },
                    ticks: {
                        color: '#6b7280'
                    },
                    title: {
                        display: true,
                        text: 'Time',
                        color: '#6b7280',
                        font: { size: 14, weight: 'bold' }
                    }
                },
            },
            plugins: {
                title: {
                    display: true,
                    text: title,
                    font: { size: 20, weight: 'bold' },
                    padding: { top: 10, bottom: 20 }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: { boxWidth: 12, padding: 15 }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    callbacks: {
                        label: tooltipItem => `${tooltipItem.dataset.label}: ${tooltipItem.raw} %`
                    }
                }
            }
        }
    });
}

// Initialize charts
const metricsCtx = document.getElementById('system-metrics').getContext('2d');

const metricsChart = createChart(metricsCtx, 'System Metrics Over Time', [], [
    { label: 'CPU Usage (%)', borderColor: 'rgba(59, 130, 246, 1)', backgroundColor: 'rgba(59, 130, 246, 0.2)', data: [], fill: false, tension: 0.4 },
    { label: 'Memory Usage (%)', borderColor: 'rgba(16, 185, 129, 1)', backgroundColor: 'rgba(16, 185, 129, 0.2)', data: [], fill: false, tension: 0.4 },
    { label: 'Temperature (°C)', borderColor: 'rgba(239, 68, 68, 1)', backgroundColor: 'rgba(239, 68, 68, 0.2)', data: [], fill: false, tension: 0.4 }
]);

// Function to update chart data
function updateChart() {
    fetch('/api/v1/system-info')
        .then(response => response.json())
        .then(data => {
            const timestamp = new Date().toLocaleTimeString();

            // Update metrics chart
            updateChartData(metricsChart, timestamp, [data.cpu_percent, data.memory_percent, data.current_temp]);

            // Update metric display
            updateMetricsDisplay(data);

            // Update top processes
            updateProcessGrid(data.top_processes);
        });
}

// Function to update chart data
function updateChartData(chart, timestamp, newData) {
    chart.data.labels.push(timestamp);
    newData.forEach((dataPoint, index) => {
        chart.data.datasets[index].data.push(dataPoint);
    });

    if (chart.data.labels.length > 30) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => dataset.data.shift());
    }
    
    chart.update();
}

// Function to update metrics display
function updateMetricsDisplay(data) {
    document.querySelector('.cpu-percent').textContent = data.cpu_percent;
    document.querySelector('.cpu-frequency').textContent = data.cpu_frequency;
    document.querySelector('.memory-percent').textContent = data.memory_percent;
    document.querySelector('.memory-used').textContent = data.memory_used;
    document.querySelector('.current-temp').textContent = data.current_temp;
    document.querySelector('.network-received').textContent = data.network_received;
    document.querySelector('.network-sent').textContent = data.network_sent;
    document.querySelector('.disk-percent').textContent = data.disk_percent;
    document.querySelector('.battery-percent').textContent = data.battery_percent;
    document.querySelector('.battery-status').textContent = data.battery_status;
    document.querySelector('.current-server-time').textContent = data.timestamp;
}

// Function to update process grid
function updateProcessGrid(topProcesses) {
    const processGrid = document.querySelector('.process-grid');
    processGrid.innerHTML = '';
    topProcesses.forEach(process => {
        const processItem = document.createElement('div');
        processItem.classList.add('process-item');
        processItem.innerHTML = `
            <span class="process-name">${process[0]}</span>
            <span class="process-cpu">CPU: ${process[1]}%</span>
            <span class="process-memory">Memory: ${process[2]}%</span>`;
        processGrid.appendChild(processItem);
    });
}

// Update every 2 seconds
setInterval(updateChart, 2000);
updateChart(); // Initial update
