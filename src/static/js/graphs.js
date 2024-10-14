// ChartManager class to manage charts
class ChartManager {
    constructor() {
        this.charts = {};
    }

    createChart(ctx, data, title, xlabel, yLabel,
        type, tension, pointRadius, pointHoverRadius) {
        this.setupCanvasStyle(ctx.canvas);

        const chart = new Chart(ctx, {
            type: type || 'line',
            data: {
                labels: data.labels,
                datasets: data.datasets.map((dataset, index) => {
                    const { backgroundColor, borderColor, pointBackgroundColor, pointBorderColor,
                        pointHoverBackgroundColor, pointHoverBorderColor

                    } = generateColor(index);
                    return {
                        ...dataset,
                        borderWidth: 2,
                        fill: true,
                        tension: tension,
                        pointRadius: pointRadius,
                        pointHoverRadius: pointHoverRadius || 5,
                        backgroundColor: backgroundColor,
                        borderColor: borderColor,
                        pointBackgroundColor: pointBackgroundColor,
                        pointBorderColor: pointBorderColor,
                        pointHoverBackgroundColor: pointHoverBackgroundColor,
                        pointHoverBorderColor: pointHoverBorderColor,
                    };
                }),
            },
            options: this.getChartOptions(title, xlabel, yLabel),
        });

        this.charts[title] = chart;
        return chart;
    }

    destroyChart(title) {
        if (this.charts[title]) {
            this.charts[title].destroy();
            delete this.charts[title];
        }
    }

    setupCanvasStyle(canvas) {
        canvas.height = "400px";
        canvas.style.padding = "20px";
        canvas.style.margin = "30px";
        canvas.style.border = "1px solid #ccc";
        canvas.style.borderRadius = "10px";
        canvas.style.backgroundColor = "white";
    }

    getChartOptions(title, xlabel, yLabel) {
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
                    title: {
                        display: true,
                        text: xlabel,
                        font: {
                            size: 16,
                            weight: 'bold',
                            color: '#333' // Improved color for better visibility
                        },
                    }
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
                },
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 20,
                        weight: 'bold',
                        color: '#333' // Improved color for better visibility
                    }
                }
            }
        };
    }
}

// Variables to store chart instances
let chartManager = new ChartManager();

// Function to fetch chart configurations and render charts
function fetchChartConfigurations() {
    fetch('/api/v1/chart-configurations')
        .then(response => response.json())
        .then(configurations => {
            fetchDataAndRenderCharts(configurations);
        })
        .catch(error => console.error('Error fetching chart configurations:', error));
}

// Function to fetch data and render charts
function fetchDataAndRenderCharts(chartConfigurations) {
    const storedFilterValue = localStorage.getItem('filterValue') || 5;
    document.getElementById('timeFilter').value = storedFilterValue;

    fetch(`/api/v1/prometheus/graphs_data?filter=${storedFilterValue}`)
        .then(response => response.json())
        .then(data => {
            createCharts(data, chartConfigurations);
        })
        .catch(error => console.error('Error fetching data:', error));
}

// Function to create charts dynamically
function createChartContainer(chartConfig) {

    const container = document.getElementById('chartsContainer');

    // Create a new div for each chart
    const chartDiv = document.createElement('div');
    chartDiv.className = 'chart-container'; // Optional: add styles for better layout

    // Create a heading element
    const heading = document.createElement('h3');
    heading.textContent = chartConfig.title; // Use the chart title for the heading
    heading.className = 'chart-heading'; // Optional: add styles for the heading

    // Create a canvas element
    const canvas = document.createElement('canvas');
    canvas.className = 'graph';
    canvas.id = chartConfig.metric_name; // Use the metric name for the canvas ID

    // Append heading and canvas to the div
    chartDiv.appendChild(heading);
    chartDiv.appendChild(canvas);

    // Append the div to the charts container
    container.appendChild(chartDiv);
}

// Function to create charts with the fetched data
function createCharts(data, chartConfigurations) {
    // Clear previous charts
    const container = document.getElementById('chartsContainer');
    container.innerHTML = ''; // Clear the charts container

    chartConfigurations.forEach(config => {
        // Check if the chart is active
        if (config.is_active) {
            createChartContainer(config); // Create a container for each active chart

            const ctx = document.getElementById(config.metric_name).getContext('2d');
            const chartData = prepareChartData(data, config.metric_name);

            chartManager.destroyChart(config.title); // Ensure we destroy existing chart before creating a new one

            chartManager.createChart(ctx, chartData, config.title, config.xlabel, config.ylabel,
                config.chart_type, config.tension, config.point_radius, config.point_hover_radius
            );
        }
    });
}


// Prepare chart data based on the fetched data
function prepareChartData(data, metricName) {
    let datasets;
    datasets = prepareDatasets(data[metricName]);
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
        };
    });
}

// Generate color for datasets
function generateColor(index) {
    const baseHue = 100; // Base hue for blue colors
    const hue = (baseHue + (index * 30)) % 360;  // Adjust hue for unique colors
    const lightness = 50 + (index * 5) % 50; // Vary lightness for more distinction
    const saturation = 70 + (index * 5) % 30; // Vary saturation for more distinction

    return {
        borderColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`, // Adjusted for better contrast
        backgroundColor: `hsla(${hue}, ${saturation}%, ${lightness}%, 0.8)`, // Transparent background
        pointBackgroundColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`, // Adjusted for better contrast
        pointBorderColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`, // Adjusted for better contrast
        pointHoverBackgroundColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`, // Adjusted for better contrast
        pointHoverBorderColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`, // Adjusted for better contrast
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
    fetchChartConfigurations();
});

document.getElementById('refreshData').addEventListener('click', fetchChartConfigurations);

// Ensure the DOM is fully loaded before running scripts
document.addEventListener('DOMContentLoaded', () => {
    fetchChartConfigurations();
    getRetentionDays();
});
