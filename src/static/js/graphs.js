class ChartManager {
    constructor() {
        this.charts = new Map();
        this.isDarkMode = localStorage.getItem('darkMode') === 'true';
        this.applyTheme();
    }

    createChart(ctx, data, config) {
        this.setupCanvasStyle(ctx.canvas);
        console.log("config", config)

        const chart = new Chart(ctx, {
            type: config.chart_type || 'line',
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
            backgroundColor: this.isDarkMode ? "#2d2d2d" : "white",
        });
    }

    prepareChartData(data, config) {
        const labels = data.time.map(t => this.formatDate(t));
        const datasets = this.prepareDatasets(data[config.metric_name], config);

        return datasets.length ? { labels, datasets } : null;
    }

    prepareDatasets(data, config) {
        return data.map((item, index) => {
            const colors = this.generateColor(index);
            const values = item.values || item.data;

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
        }).filter(Boolean);
    }

    getChartOptions(config) {
        return {
            responsive: true,
            scales: this.getScalesOptions(config),
            plugins: this.getPluginsOptions(config),
        };
    }

    getScalesOptions(config) {
        const textColor = this.isDarkMode ? '#fff' : '#333';
        const fontOptions = {
            size: 12,
            weight: 'bold',
            color: textColor,
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
                    color: textColor,
                },
                grid: {
                    display: false,
                    color: this.isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
                },
                title: {
                    display: true,
                    text: config.xlabel,
                    font: { ...fontOptions, size: 16 },
                    color: textColor,
                },
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: config.ylabel,
                    font: { ...fontOptions, size: 16 },
                    color: textColor,
                },
                ticks: {
                    font: fontOptions,
                    padding: 10,
                    color: textColor,
                },
                grid: {
                    display: false,
                    color: this.isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
                },
            },
        };
    }

    getPluginsOptions(config) {
        const textColor = this.isDarkMode ? '#fff' : '#333';
        return {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    font: {
                        size: 14,
                        weight: 'bold',
                        color: textColor,
                    },
                },
            },
            tooltip: this.getTooltipOptions(),
            // title: {
            //     display: true,
            //     text: config.title,
            //     font: {
            //         size: 20,
            //         weight: 'bold',
            //         color: textColor,
            //     },
            // },
        };
    }

    getTooltipOptions() {
        return {
            enabled: true,
            backgroundColor: this.isDarkMode ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.7)',
            titleColor: this.isDarkMode ? '#000' : '#fff',
            bodyColor: this.isDarkMode ? '#000' : '#fff',
            titleFont: { size: 14, weight: 'bold' },
            bodyFont: { size: 12 },
            padding: 10,
            mode: 'nearest',
            intersect: false,
            callbacks: {
                label: (context) => {
                    const label = context.dataset.label || '';
                    const value = Math.round(context.raw * 100) / 100;
                    return `${label}: ${value}`;
                },
                title: (context) => `Time: ${context[0].label}`,
            },
        };
    }

    generateColor(index) {
        const baseHue = 50;
        const hue = (baseHue + (index * 30)) % 360;
        const lightness = this.isDarkMode ? 70 : 50;
        const saturation = 70 + (index * 5) % 30;

        return {
            borderColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`,
            backgroundColor: `hsla(${hue}, ${saturation}%, ${lightness}%, 0.2)`,
            pointBackgroundColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`,
            pointBorderColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`,
            pointHoverBackgroundColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`,
            pointHoverBorderColor: `hsl(${hue}, ${saturation}%, ${lightness - 20}%)`,
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

    toggleTheme() {
        this.isDarkMode = !this.isDarkMode;
        localStorage.setItem('darkMode', this.isDarkMode);
        this.applyTheme();
        this.updateChartsTheme();
    }

    applyTheme() {
        document.body.classList.toggle('dark-mode', this.isDarkMode);
        const themeIcon = document.querySelector('#themeToggle i');
        if (themeIcon) {
            themeIcon.className = this.isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    updateChartsTheme() {
        this.charts.forEach(chart => {
            chart.options.scales = this.getScalesOptions(chart.options.plugins.title);
            chart.options.plugins = this.getPluginsOptions(chart.options.plugins.title);
            chart.update();
        });
    }

}

class ChartUI {
    constructor(chartManager) {
        this.chartManager = chartManager;
        this.container = document.getElementById('chartsContainer');
        this.initializeUIControls();
    }

    initializeUIControls() {
        // Theme toggle
        document.getElementById('themeToggle')?.addEventListener('click', () => {
            this.chartManager.toggleTheme();
        });

        // Fullscreen toggle
        document.getElementById('fullscreenToggle')?.addEventListener('click', () => {
            this.toggleFullscreen();
        });

        // Export button and modal
        document.getElementById('exportData')?.addEventListener('click', () => {
            this.showExportModal();
        });

        document.querySelector('.close-modal')?.addEventListener('click', () => {
            this.hideExportModal();
        });

        // Export format buttons
        document.querySelectorAll('.export-options button').forEach(button => {
            button.addEventListener('click', () => {
                const format = button.dataset.format;
                this.chartManager.exportCharts(format);
                this.hideExportModal();
            });
        });

        // Close modal when clicking outside
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('exportModal');
            if (event.target === modal) {
                this.hideExportModal();
            }
        });

        // Handle fullscreen change
        document.addEventListener('fullscreenchange', () => {
            const icon = document.querySelector('#fullscreenToggle i');
            if (icon) {
                icon.className = document.fullscreenElement ? 'fas fa-compress' : 'fas fa-expand';
            }
        });
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error('Failed to enter fullscreen:', err);
            });
        } else {
            document.exitFullscreen().catch(err => {
                console.error('Failed to exit fullscreen:', err);
            });
        }
    }

    showExportModal() {
        const modal = document.getElementById('exportModal');
        if (modal) {
            modal.style.display = 'block';
        }
    }

    hideExportModal() {
        const modal = document.getElementById('exportModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    createChartContainer(config) {
        const chartDiv = document.createElement('div');
        chartDiv.className = 'chart-container p-4';

        const metricCard = document.createElement('div');
        metricCard.className = 'metric-card bg-white dark:bg-gray-800 shadow-md rounded-lg overflow-hidden';

        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header bg-gray-100 dark:bg-gray-700 p-4 border-b border-gray-200 dark:border-gray-600';

        const heading = document.createElement('h3');
        heading.className = 'text-lg font-semibold text-gray-900 dark:text-gray-100';
        heading.textContent = config.title;
        cardHeader.appendChild(heading);

        const cardContent = document.createElement('div');
        cardContent.className = 'card-content p-4';

        const canvas = document.createElement('canvas');
        canvas.className = 'graph w-full h-96';
        canvas.id = config.metric_name;

        cardContent.appendChild(canvas);
        metricCard.appendChild(cardHeader);
        metricCard.appendChild(cardContent);
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
                } else {
                    console.warn(`No data for chart: ${config.title}`);
                }
            }
        });
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
        this.autoRefreshInterval = null;
        this.initEventListeners();
        this.initAutoRefresh();
        this.initTimeZoneInfo();
    }

    async init() {
        try {
            await this.updateRetentionDays();
            await this.fetchDataAndRenderCharts();
            this.updateCurrentTime();
            // Start the current time update interval
            setInterval(() => this.updateCurrentTime(), 1000);
        } catch (error) {
            console.error('Error initializing app:', error);
            this.showErrorMessage('Failed to initialize the application. Please try refreshing the page.');
        }
    }

    initEventListeners() {
        // Time filter change
        const timeFilter = document.getElementById('timeFilter');
        if (timeFilter) {
            timeFilter.value = localStorage.getItem('filterValue') || '5 minutes';
            timeFilter.addEventListener('change', this.handleFilterChange.bind(this));
        }

        // Refresh button
        document.getElementById('refreshData')?.addEventListener('click', () => {
            this.fetchDataAndRenderCharts();
        });

        // Initialize keyboard shortcuts
        this.initKeyboardShortcuts();
    }

    initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R to refresh
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.fetchDataAndRenderCharts();
            }
            // Ctrl/Cmd + E to export
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                this.chartUI.showExportModal();
            }
            // Ctrl/Cmd + F to toggle fullscreen
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                this.chartUI.toggleFullscreen();
            }
            // Ctrl/Cmd + D to toggle dark mode
            if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
                e.preventDefault();
                this.chartManager.toggleTheme();
            }
        });
    }

    initAutoRefresh() {
        const refreshInterval = document.getElementById('refreshInterval');
        if (refreshInterval) {
            refreshInterval.value = localStorage.getItem('autoRefreshInterval') || '0';

            refreshInterval.addEventListener('change', (event) => {
                const seconds = parseInt(event.target.value);
                localStorage.setItem('autoRefreshInterval', seconds.toString());

                // Clear existing interval
                if (this.autoRefreshInterval) {
                    clearInterval(this.autoRefreshInterval);
                    this.autoRefreshInterval = null;
                }

                // Set new interval if seconds > 0
                if (seconds > 0) {
                    this.autoRefreshInterval = setInterval(() => {
                        this.fetchDataAndRenderCharts();
                    }, seconds * 1000);
                }
            });

            // Initialize auto-refresh if saved value exists
            const savedInterval = parseInt(localStorage.getItem('autoRefreshInterval') || '0');
            if (savedInterval > 0) {
                this.autoRefreshInterval = setInterval(() => {
                    this.fetchDataAndRenderCharts();
                }, savedInterval * 1000);
            }
        }
    }

    initTimeZoneInfo() {
        const timeZoneElement = document.getElementById('timeZoneName');
        if (timeZoneElement) {
            const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            timeZoneElement.textContent = timeZone;
        }
    }

    updateCurrentTime() {
        const currentTimeElement = document.getElementById('currentTime');
        if (currentTimeElement) {
            const now = new Date();
            const options = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false,
                timeZoneName: 'short'
            };
            currentTimeElement.textContent = now.toLocaleString('en-US', options);
        }
    }

    async handleFilterChange(event) {
        this.filterValue = event.target.value;
        localStorage.setItem('filterValue', this.filterValue);
        await this.fetchDataAndRenderCharts();
    }

    async fetchDataAndRenderCharts() {
        try {
            const loadingIndicator = this.showLoadingIndicator();

            const [configurations, data] = await Promise.all([
                DataFetcher.fetchChartConfigurations(),
                DataFetcher.fetchChartData(this.filterValue)
            ]);

            // Update active charts counter
            const activeCharts = document.getElementById('activeCharts');
            if (activeCharts) {
                const active = configurations.filter(config => config.is_active).length;
                const total = configurations.length;
                activeCharts.textContent = `${active} / ${total}`;
            }

            this.chartUI.renderCharts(data, configurations);
            this.hideLoadingIndicator(loadingIndicator);
        } catch (error) {
            console.error('Error fetching data and rendering charts:', error);
            this.showErrorMessage('Failed to fetch data. Please try again later.');
            this.hideLoadingIndicator(loadingIndicator);
        }
    }

    async updateRetentionDays() {
        try {
            const retentionDays = await DataFetcher.fetchRetentionDays();
            const retentionElement = document.getElementById('dataretation');
            if (retentionElement) {
                if (typeof retentionDays === 'number') {
                    retentionElement.textContent = `${retentionDays} days`;
                } else {
                    retentionElement.textContent = retentionDays;
                }
            }
        } catch (error) {
            console.error('Error updating retention days:', error);
            this.showErrorMessage('Failed to fetch retention days.');
        }
    }

    showLoadingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'loading-indicator';
        indicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        document.body.appendChild(indicator);
        return indicator;
    }

    hideLoadingIndicator(indicator) {
        if (indicator && indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
    }

    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        document.body.appendChild(errorDiv);

        // Remove the error message after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init().catch(error => {
        console.error('Failed to initialize the application:', error);
    });
});