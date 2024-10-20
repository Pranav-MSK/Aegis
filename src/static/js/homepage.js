// Configuration object for chart settings
const CONFIG = {
  REFRESH_INTERVAL: 1000,
  MAX_DATA_POINTS: 30,
  CHART_COLORS: {
    CPU: 'rgba(59, 130, 246, 1)',
    MEMORY: 'rgba(16, 185, 129, 1)',
    TEMPERATURE: 'rgba(239, 68, 68, 1)',
    NETWORK: 'rgba(234, 179, 8, 1)',
  },
  API_ENDPOINTS: {
    SYSTEM_INFO: '/api/v1/system-info',
    DASHBOARD_STATS: '/api/dashboard/stats'
  }
};

// Chart factory class for creating and managing charts
class ChartFactory {
  static createBaseOptions(title) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: 300,
        easing: 'easeInOutQuad'
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          grid: { display: false },
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
          grid: { display: false },
          ticks: { color: '#6b7280' }
        }
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
          callbacks: {
            label: tooltipItem => `${tooltipItem.dataset.label}: ${tooltipItem.raw}%`
          }
        }
      }
    };
  }

  static createChart(ctx, title, datasets = []) {
    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: datasets.map(dataset => ({
          ...dataset,
          fill: false,
          tension: 0.4
        }))
      },
      options: this.createBaseOptions(title)
    });
  }
}

// Dashboard controller class
class DashboardController {
  constructor() {
    this.charts = new Map();
    this.setupCharts();
    this.setupEventListeners();
  }

  setupCharts() {
    // System metrics chart
    const metricsCtx = this.getContext('system-metrics');
    if (metricsCtx) {
      this.charts.set('metrics', ChartFactory.createChart(metricsCtx, 'System Metrics Over Time', [
        { label: 'CPU Usage (%)', borderColor: CONFIG.CHART_COLORS.CPU, backgroundColor: this.getBackgroundColor(CONFIG.CHART_COLORS.CPU) },
        { label: 'Memory Usage (%)', borderColor: CONFIG.CHART_COLORS.MEMORY, backgroundColor: this.getBackgroundColor(CONFIG.CHART_COLORS.MEMORY) },
        { label: 'Temperature (°C)', borderColor: CONFIG.CHART_COLORS.TEMPERATURE, backgroundColor: this.getBackgroundColor(CONFIG.CHART_COLORS.TEMPERATURE) }
      ]));
    }

    // CPU cores chart (initialized when data is received)
    this.cpuCoresCtx = this.getContext('cpu-usage-core');
  }

  getContext(id) {
    const canvas = document.getElementById(id);
    return canvas?.getContext('2d');
  }

  getBackgroundColor(color) {
    return color.replace('1)', '0.2)');
  }

  setupEventListeners() {
    // Add error handling for chart updates
    window.addEventListener('error', (event) => {
      console.error('Chart update error:', event.error);
      this.handleError('Chart update failed');
    });
  }

  async updateDashboard() {
    try {
      const [systemInfo, dashboardStats] = await Promise.all([
        this.fetchData(CONFIG.API_ENDPOINTS.SYSTEM_INFO),
        this.fetchData(CONFIG.API_ENDPOINTS.DASHBOARD_STATS)
      ]);

      this.updateCharts(systemInfo);
      this.updateMetricsDisplay(systemInfo);
      this.updateProcessGrid(systemInfo.top_processes);
      this.updateDashboardStats(dashboardStats);
    } catch (error) {
      this.handleError('Failed to update dashboard', error);
    }
  }

  async fetchData(endpoint) {
    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  updateCharts(data) {
    const timestamp = new Date().toLocaleTimeString();

    // Update system metrics chart
    this.updateChartData(this.charts.get('metrics'), timestamp, [
      data.cpu_percent,
      data.memory_percent,
      data.current_temp
    ]);

    // Initialize or update CPU cores chart
    if (!this.charts.get('cpuCores') && this.cpuCoresCtx) {
      const datasets = this.createCpuCoreDatasets(data.cpu_usage_core.length);
      this.charts.set('cpuCores', ChartFactory.createChart(this.cpuCoresCtx, 'CPU Usage Core Over Time', datasets));
    }
    if (this.charts.get('cpuCores')) {
      this.updateChartData(this.charts.get('cpuCores'), timestamp, data.cpu_usage_core);
    }
  }

  createCpuCoreDatasets(cpuCoreCount) {
    return Array.from({ length: cpuCoreCount }, (_, i) => ({
      label: `CPU Core ${i + 1} (%)`,
      borderColor: Object.values(CONFIG.CHART_COLORS)[i % Object.keys(CONFIG.CHART_COLORS).length],
      backgroundColor: this.getBackgroundColor(Object.values(CONFIG.CHART_COLORS)[i % Object.keys(CONFIG.CHART_COLORS).length])
    }));
  }

  updateChartData(chart, timestamp, newData) {
    if (!chart) return;

    chart.data.labels.push(timestamp);
    newData.forEach((dataPoint, index) => {
      chart.data.datasets[index].data.push(dataPoint);
    });

    if (chart.data.labels.length > CONFIG.MAX_DATA_POINTS) {
      chart.data.labels.shift();
      chart.data.datasets.forEach(dataset => dataset.data.shift());
    }

    chart.update('none'); // Use 'none' mode for better performance
  }

  updateMetricsDisplay(data) {
    const metrics = {
      'cpu-percent': data.cpu_percent,
      'cpu-frequency': data.cpu_frequency,
      'memory-percent': data.memory_percent,
      'memory-used': data.memory_used,
      'current-temp': data.current_temp,
      'network-received': `${data.network_received} MB`,
      'network-sent': `${data.network_sent} MB`,
      'disk-percent': data.disk_percent,
      'battery-percent': data.battery_percent,
      'battery-status': data.battery_status,
      'current-server-time': data.timestamp,
      'disk-read': data.disk_read,
      'disk-write': data.disk_write,
      'disk-write-per-sec': data.disk_write_per_sec,
      'disk-read-per-sec': data.disk_read_per_sec,
      'upload-speed': data.upload_speed,
      'download-speed': data.download_speed,
    };

    Object.entries(metrics).forEach(([className, value]) => {
      const element = document.querySelector(`.${className}`);
      if (element && element.textContent !== String(value)) {
        element.textContent = value;
      }
    });
  }

  updateProcessGrid(processes) {
    const grid = document.querySelector('.process-grid');
    if (!grid) return;

    const fragment = document.createDocumentFragment();
    processes.forEach(([name, cpu, memory]) => {
      const item = document.createElement('div');
      item.className = 'process-item';
      item.innerHTML = `
          <span class="process-name">${this.sanitizeHTML(name)}</span>
          <span class="process-cpu">CPU: ${cpu}%</span>
          <span class="process-memory">Memory: ${memory}%</span>
        `;
      fragment.appendChild(item);
    });

    grid.innerHTML = '';
    grid.appendChild(fragment);
  }

  updateDashboardStats(data) {
    const stats = {
      'total-users': `${data.user_stats?.total_users} / ${data.max_users_allowed}`,
      'active-users': data.user_stats?.active_users,
      'inactive-users': data.user_stats?.inactive_users,
      'admin-users': data.user_stats?.admin_users,
      'total-tickets': `${data.ticket_stats?.total_tickets} / ${data.monthly_alert_tickets_limit}`,
      'open-tickets': data.ticket_stats?.open_tickets,
      'in-progress-tickets': data.ticket_stats?.in_progress_tickets,
      'resolved-tickets': data.ticket_stats?.resolved_tickets,
      'closed-tickets': data.ticket_stats?.closed_tickets,
      'total-charts': `${data.chart_stats?.total_charts} / ${data.max_number_of_graphs}`,
      'active-charts': data.chart_stats?.active_charts,
      'critical-tickets': data.ticket_stats?.critical_tickets,
      'warning-tickets': data.ticket_stats?.warning_tickets,
      'info-tickets': data.ticket_stats?.info_tickets,
      'total-rules': `${data.total_rules} / ${data.max_alert_rules}`,
      'total-targets': `${data.total_targets} / ${data.max_scrap_target}`,

    };

    Object.entries(stats).forEach(([className, value]) => {
      if (value !== undefined) {
        const element = document.querySelector(`.${className}`);
        if (element && element.textContent !== String(value)) {
          element.textContent = value;
        }
      }
    });
  }

  sanitizeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  handleError(message, error = null) {
    console.error(message, error);
    // Implement your error handling strategy here (e.g., show toast notification)
  }

  start() {
    this.updateDashboard(); // Initial update
    setInterval(() => this.updateDashboard(), CONFIG.REFRESH_INTERVAL);
  }
}


function scrollToSection(sectionId) {
  const section = document.querySelector(`[data-feature="${sectionId}"]`);
  if (section) {
    section.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }
}
// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const dashboard = new DashboardController();
  dashboard.start();
});