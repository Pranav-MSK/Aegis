// ChartManager class to manage charts
class ChartManager {
    constructor() {
        this.charts = {};
    }

    createChart(ctx, label, data, yLabel) {
        this.setupCanvasStyle(ctx.canvas);
        

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
            labels: data.labels,
            datasets: data.datasets.map(dataset => ({
                ...dataset,
                borderWidth: 2,
                fill: true,
                tension: 0.4, // Adjusted tension for a balanced curve
                pointRadius: 0, // Added point radius for better visibility
                pointHoverRadius: 6,
                backgroundColor: dataset.backgroundColor || 'rgba(75, 192, 192, 0.2)',
                borderColor: dataset.borderColor || 'rgba(75, 192, 192, 1)',
                pointBackgroundColor: dataset.borderColor || 'rgba(75, 192, 192, 1)', // Match point color with border color
                pointBorderColor: '#fff', // White border for points
                pointHoverBackgroundColor: '#fff', // White background on hover
                pointHoverBorderColor: dataset.borderColor || 'rgba(75, 192, 192, 1)', // Match hover border color with dataset border color
            })),
            },
            options: this.getChartOptions(yLabel),
        });

        this.charts[label] = chart;
        return chart;
    }

    destroyChart(label) {
        if (this.charts[label]) {
            this.charts[label].destroy();
            delete this.charts[label];
        }
    }

    setupCanvasStyle(canvas) {
        canvas.height = "500px";
        canvas.style.padding = "20px";
        canvas.style.margin = "30px";
        canvas.style.border = "1px solid #ccc";
        canvas.style.borderRadius = "10px";
        canvas.style.backgroundColor = "white";
    }

    getChartOptions(yLabel) {
        return {
            responsive: true,
            scales: {
                x: {
                    type: 'category',
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 10,
                        maxRotation: 0,
                        minRotation: 0,
                        padding: 10,
                        font: {
                            size: 12,
                            weight: 'bold',
                            color: '#333' // Improved color for better visibility
                        }
                    },
                    grid: {
                        display: false // Remove grid lines for a cleaner look
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: yLabel,
                        font: {
                            size: 16,
                            weight: 'bold',
                            color: '#333' // Improved color for better visibility
                        },
                    },
                    ticks: {
                        font: {
                            size: 12,
                            weight: 'bold',
                            color: '#333' // Improved color for better visibility
                        },
                        padding: 10,
                    },
                    grid: {
                        display: false // Remove y-axis grid lines for a cleaner look
                    },
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14,
                            weight: 'bold',
                            color: '#333'
                        }
                    }
                },
                tooltip: {
                    enabled: true,  // Enable tooltips
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',  // Dark background
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    titleFont: { size: 14, weight: 'bold' },
                    bodyFont: { size: 12 },
                    padding: 10,
                    mode: 'nearest',
                    intersect: false,
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += `Value: ${Math.round(context.raw * 100) / 100}`;
                            return label;
                        },
                        title: function (context) {
                            return `Time: ${context[0].label}`;
                        },
                        
                    }
                },
                legend: {
                    display: true  // Keep the legend hidden to avoid clutter
                }
            }
        };
    }
}


// Variables to store chart instances
let chartManager = new ChartManager();

// Configuration for the charts
const chartConfigurations = [
    { id: 'cpuTimeChart', label: 'CPU Usage (%)', yLabel: 'CPU Usage (%)' },
    { id: 'memoryTimeChart', label: 'Memory Usage (%)', yLabel: 'Memory Usage (%)' },
    { id: 'batteryTimeChart', label: 'Power Usage (%)', yLabel: 'Power Usage (%)' },
    { id: 'networkTimeChart', label: 'Data Transferred (MB)', yLabel: 'Data Transferred (MB)', combine: true },
    { id: 'dashboardMemoryTimeChart', label: 'Dashboard Memory Usage', yLabel: 'Memory Usage' },
    { id: 'cpuFrequencyTimeChart', label: 'CPU Frequency (GHz)', yLabel: 'Frequency (GHz)' },
    { id: 'currentTempTimeChart', label: 'Current Temperature (°C)', yLabel: 'Temperature (°C)' },
];

// Function to fetch data and render charts
function fetchDataAndRenderCharts() {
    const storedFilterValue = localStorage.getItem('filterValue') || 5;
    document.getElementById('timeFilter').value = storedFilterValue;

    fetch(`/api/v1/prometheus/graphs_data?filter=${storedFilterValue}`)
        .then(response => response.json())
        .then(data => {
            createCharts(data);
        })
        .catch(error => console.error('Error fetching data:', error));
}

// Function to create charts with the fetched data
function createCharts(data) {
    chartConfigurations.forEach(({ id, label, yLabel }) => {
        const ctx = document.getElementById(id).getContext('2d');
        const chartData = prepareChartData(data, label);
        chartManager.destroyChart(label); // Ensure we destroy existing chart before creating a new one
        chartManager.createChart(ctx, label, chartData, yLabel);
    });
}

// Prepare chart data based on the fetched data
function prepareChartData(data, label) {
    let datasets;

    switch (label) {
        case 'CPU Usage (%)':
            datasets = prepareDatasets(data.cpu);
            break;
        case 'Memory Usage (%)':
            datasets = prepareDatasets(data.memory);
            break;
        case 'Power Usage (%)':
            datasets = prepareDatasets(data.battery);
            break;
        case 'Data Transferred (MB)':
            datasets = prepareDatasets([...data.network_sent, ...data.network_received]);
            break;
        case 'Dashboard Memory Usage':
            datasets = prepareDatasets(data.dashboard_memory_usage);
            break;
        case 'CPU Frequency (GHz)':
            datasets = prepareDatasets(data.cpu_frequency);
            break;
        case 'Current Temperature (°C)':
            datasets = prepareDatasets(data.current_temp);
            break;
        default:
            datasets = [];
            break;
    }

    return {
        labels: data.time.map(t => formatDate(t, Intl.DateTimeFormat().resolvedOptions().timeZone)),
        datasets,
    };
}

// Prepare datasets based on the data
function prepareDatasets(data) {
    return data.map((item, index) => {
        const { borderColor, backgroundColor } = generateColor(index);
        return {
            label: item.metric ? item.metric.instance : `Dataset ${index + 1}`,
            data: item.values || item.data,
            borderColor: borderColor,
            backgroundColor: backgroundColor,
            tension: 0.4,
        };
    });
}

// Generate color for datasets
function generateColor(index) {
    const hue = (index * 40) % 360;  // Adjust hue for unique colors
    return {
        borderColor: `hsl(${hue}, 40%, 50%)`,
        backgroundColor: `hsla(${hue}, 40%, 50%, 0.3)`,
    };
}

// Fetch retention days
function getRetentionDays() {
    fetch('/api/v1/get-retention')
        .then(response => response.json())
        .then(data => {
            document.getElementById('dataretation').textContent = "Data Retention Days: " + data.retention_time;
        })
        .catch(error => console.error('Error fetching data:', error));
}

// Format date
function formatDate(utcTime, timeZone) {
    const date = new Date(utcTime);
    const options = {
        timeZone: timeZone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
    };
    return date.toLocaleString('en-US', options).replace(/, (\d{2}:\d{2})/, ' $1');
}

// Event listeners
document.getElementById('timeFilter').addEventListener('change', (event) => {
    localStorage.setItem('filterValue', event.target.value);
    fetchDataAndRenderCharts();
});

document.getElementById('refreshData').addEventListener('click', fetchDataAndRenderCharts);

// Ensure the DOM is fully loaded before running scripts
document.addEventListener('DOMContentLoaded', () => {
    fetchDataAndRenderCharts();
    getRetentionDays();
});
