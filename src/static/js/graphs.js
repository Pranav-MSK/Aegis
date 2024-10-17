    // ChartManager class to manage charts
    class ChartManager {
        constructor() {
            this.charts = new Map();
        }

        createChart(ctx, data, config) {
            this.setupCanvasStyle(ctx.canvas);

            const chart = new Chart(ctx, {
                type: config.type || 'line',
                data: this.prepareChartData(data, config),
                options: this.getChartOptions(config),
            });

            this.charts.set(config.title, chart);
            return chart;
        }

        destroyChart(title) {
            const chart = this.charts.get(title);
            if (chart) {
                chart.destroy();
                this.charts.delete(title);
            }
        }

        setupCanvasStyle(canvas) {
            Object.assign(canvas.style, {
                height: "400px",
                padding: "20px",
                margin: "30px",
                border: "1px solid #ccc",
                borderRadius: "10px",
                backgroundColor: "white",
            });
        }

        prepareChartData(data, config) {
            const labels = data.time.map(t => this.formatDate(t));
            const datasets = this.prepareDatasets(data[config.metric_name], config);

            // Only return data if datasets are not empty
            return datasets.length ? { labels, datasets } : null;
        }

        prepareDatasets(data, config) {
            return data.map((item, index) => {
                const colors = this.generateColor(index);
                const values = item.values || item.data;

                // Skip datasets without data
                if (!values || !values.length) {
                    return null;
                }

                return {
                    label: item.metric ? item.metric.instance : `Dataset ${index + 1}`,
                    data: values,
                    borderWidth: 2,
                    fill: true,
                    tension: config.tension,
                    pointRadius: config.point_radius,
                    pointHoverRadius: config.point_hover_radius || 5,
                    ...colors,
                };
            }).filter(Boolean); // Remove null values
        }

        getChartOptions(config) {
            return {
                responsive: true,
                scales: this.getScalesOptions(config),
                plugins: this.getPluginsOptions(config),
            };
        }

        getScalesOptions(config) {
            const fontOptions = {
                size: 12,
                weight: 'bold',
                color: '#333',
            };

            return {
                x: {
                    type: 'category',
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 10,
                        maxRotation: 0,
                        minRotation: 0,
                        padding: 10,
                        font: fontOptions,
                    },
                    grid: { display: false },
                    title: {
                        display: true,
                        text: config.xlabel,
                        font: { ...fontOptions, size: 16 },
                    },
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: config.ylabel,
                        font: { ...fontOptions, size: 16 },
                    },
                    ticks: {
                        font: fontOptions,
                        padding: 10,
                    },
                    grid: { display: false },
                },
            };
        }

        getPluginsOptions(config) {
            return {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14,
                            weight: 'bold',
                            color: '#333',
                        },
                    },
                },
                tooltip: this.getTooltipOptions(),
                title: {
                    display: true,
                    text: config.title,
                    font: {
                        size: 20,
                        weight: 'bold',
                        color: '#333',
                    },
                },
            };
        }

        getTooltipOptions() {
            return {
                enabled: true,
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                titleColor: '#ffffff',
                bodyColor: '#ffffff',
                titleFont: { size: 14, weight: 'bold' },
                bodyFont: { size: 12 },
                padding: 10,
                mode: 'nearest',
                intersect: false,
                callbacks: {
                    label: (context) => {
                        const label = context.dataset.label || '';
                        const value = Math.round(context.raw * 100) / 100;
                        return `${label}: Value: ${value}`;
                    },
                    title: (context) => `Time: ${context[0].label}`,
                },
            };
        }

        generateColor(index) {
            const baseHue = 50; // Base hue for blue colors
            const hue = (baseHue + (index * 30)) % 360;  // Adjust hue for unique colors
            const lightness = 50 + (index * 5) % 10; // Vary lightness for more distinction
            const saturation = 70 + (index * 5) % 30; // Vary saturation for more distinction
        
            return {
                borderColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`, // Adjusted for better contrast
                backgroundColor: `hsla(${hue}, ${saturation}%, ${lightness}%, 0.2)`, // Transparent background
                pointBackgroundColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`, // Adjusted for better contrast
                pointBorderColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`, // Adjusted for better contrast
                pointHoverBackgroundColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`, // Adjusted for better contrast
                pointHoverBorderColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`, // Adjusted for better contrast
            };
        }
        

        formatDate(utcTime) {
            const date = new Date(utcTime);
            const options = {
                timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
            };
            return date.toLocaleString('en-US', options).replace(/, (\d{2}:\d{2})/, ' $1');
        }
    }

    class ChartUI {
        constructor(chartManager) {
            this.chartManager = chartManager;
            this.container = document.getElementById('chartsContainer');
        }                

        createChartContainer(config) {
            const chartDiv = document.createElement('div');
            chartDiv.className = 'chart-container';
        
            const metricCard = document.createElement('div');
            metricCard.className = 'metric-card';
        
            const cardHeader = document.createElement('div');
            cardHeader.className = 'card-header';
        
            // Set the card header to display the metric name
            const heading = document.createElement('h3');
            heading.textContent = config.title; // Change from config.title to config.metric_name
            cardHeader.appendChild(heading);
        
            const cardContent = document.createElement('div');
            cardContent.className = 'card-content';
        
            // Create the canvas element for the chart
            const canvas = document.createElement('canvas');
            canvas.className = 'graph';
            canvas.id = config.metric_name; // Ensure canvas ID is unique
        
            // Append the canvas to the card content
            cardContent.appendChild(canvas);
            
            // Append header and content to the card
            metricCard.appendChild(cardHeader);
            metricCard.appendChild(cardContent);
        
            // Finally, append the card to the chart container
            chartDiv.appendChild(metricCard);
            this.container.appendChild(chartDiv);
        }
        

        clearCharts() {
            this.container.innerHTML = '';
        }

        renderCharts(data, configurations) {
            this.clearCharts();
            configurations.forEach(config => {
                if (config.is_active) {
                    const chartData = this.chartManager.prepareChartData(data, config);
                    if (chartData) {
                        this.createChartContainer(config);
                        const ctx = document.getElementById(config.metric_name).getContext('2d');
                        this.chartManager.destroyChart(config.title);
                        this.chartManager.createChart(ctx, data, config);

                        // Add space between graphs
                        const chartContainer = document.getElementById(config.metric_name).closest('.chart-container');
                        chartContainer.style.marginBottom = '20px';
                    } else {
                        console.warn(`No data for chart: ${config.title}`);
                    }
                }    });
        }
    }

    class DataFetcher {
        static async fetchWithRetry(url, options = {}, retries = 3) {
            try {
                const response = await fetch(url, options);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return await response.json();
            } catch (error) {
                if (retries > 0) {
                    console.log(`Retrying fetch to ${url}. Attempts left: ${retries - 1}`);
                    return this.fetchWithRetry(url, options, retries - 1);
                } else {
                    console.error(`Failed to fetch ${url}: ${error.message}`);
                    throw error;
                }
            }
        }

        static async fetchChartConfigurations() {
            try {
                return await this.fetchWithRetry('/api/v1/chart-configurations');
            } catch (error) {
                console.error('Error fetching chart configurations:', error);
                throw error;
            }
        }

        static async fetchChartData(filterValue) {
            try {
                return await this.fetchWithRetry(`/api/v1/prometheus/graphs_data?filter=${filterValue}`);
            } catch (error) {
                console.error('Error fetching chart data:', error);
                throw error;
            }
        }

        static async fetchRetentionDays() {
            try {
                const data = await this.fetchWithRetry('/api/v1/get-retention');
                return data.retention_time;
            } catch (error) {
                console.error('Error fetching retention days:', error);
                throw error;
            }
        }
    }

    class App {
        constructor() {
            this.chartManager = new ChartManager();
            this.chartUI = new ChartUI(this.chartManager);
            this.filterValue = localStorage.getItem('filterValue') || 5;
            this.initEventListeners();
        }

        async init() {
            try {
                await this.updateRetentionDays();
                await this.fetchDataAndRenderCharts();
            } catch (error) {
                console.error('Error initializing app:', error);
                this.showErrorMessage('Failed to initialize the application. Please try refreshing the page.');
            }
        }

        initEventListeners() {
            document.getElementById('timeFilter').addEventListener('change', this.handleFilterChange.bind(this));
            document.getElementById('refreshData').addEventListener('click', this.fetchDataAndRenderCharts.bind(this));
        }

        async handleFilterChange(event) {
            this.filterValue = event.target.value;
            localStorage.setItem('filterValue', this.filterValue);
            await this.fetchDataAndRenderCharts();
        }

        async fetchDataAndRenderCharts() {
            try {
                const [configurations, data] = await Promise.all([
                    DataFetcher.fetchChartConfigurations(),
                    DataFetcher.fetchChartData(this.filterValue)
                ]);
                this.chartUI.renderCharts(data, configurations);
            } catch (error) {
                console.error('Error fetching data and rendering charts:', error);
                this.showErrorMessage('Failed to fetch data. Please try again later.');
            }
        }

        async updateRetentionDays() {
            try {
                const retentionDays = await DataFetcher.fetchRetentionDays();
                document.getElementById('dataretation').textContent = `Data Retention Days: ${retentionDays}`;
            } catch (error) {
                console.error('Error updating retention days:', error);
                this.showErrorMessage('Failed to fetch retention days. Please check your connection.');
            }
        }

        showErrorMessage(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            document.body.insertBefore(errorDiv, document.body.firstChild);
            setTimeout(() => errorDiv.remove(), 5000);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const app = new App();
        app.init();
    });
