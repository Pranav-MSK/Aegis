const CONFIG = {
  REFRESH_INTERVAL: 1000,
  MAX_DATA_POINTS: 50,
  CHART_COLORS: {
    CPU: 'rgba(59, 130, 246, 1)',
    MEMORY: 'rgba(16, 185, 129, 1)',
    TEMPERATURE: 'rgba(239, 68, 68, 1)',
    NETWORK: 'rgba(234, 179, 8, 1)',
  },
  API_ENDPOINTS: {
    SYSTEM_INFO_API: '/api/v1/system/metrics',
    DASHBOARD_STATS_API: '/api/v1/dashboard/stats',
    CONTAINER_INFO_API: '/api/v1/system/containers',
    SYSTEM_SERVICES_API: '/api/v1/system/services',
    SYSTEM_SERVICE_CATEGORIES_API: '/api/v1/system/services/categories',
    SYSTEM_NOTIFICATIONS_API: '/api/v1/system/notifications/',
    SYSTEM_STATUS_API: '/api/v1/system/status',
    SYSTEM_DISK_API: "/api/v1/system/disk",
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
    // this.cpuCoresCtx = this.getContext('cpu-usage-core');
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
  async updateSystemInfo() {
    try {
      const systemInfo = await this.fetchData(CONFIG.API_ENDPOINTS.SYSTEM_INFO_API);
      this.updateCharts(systemInfo);
      this.updateMetricsDisplay(systemInfo);
      this.updateProcessGrid(systemInfo.top_processes);
    } catch (error) {
      this.handleError('Failed to update system info', error);
    }
  }

  async updateDashboard() {
    try {
      const dashboardStats = await this.fetchData(CONFIG.API_ENDPOINTS.DASHBOARD_STATS_API);
      this.updateDashboardStats(dashboardStats);
    } catch (error) {
      this.handleError('Failed to update dashboard stats', error);
    }
  }

  async fetchContainerData() {
    try {
      const [containerSystemData] = await Promise.all([
        this.fetchData(CONFIG.API_ENDPOINTS.CONTAINER_INFO_API),
      ]);
      this.populateContainerDetails(containerSystemData);
    } catch (error) {
      this.handleError('Failed to update performance data', error);
    }
  }

  async populateContainerDetails(data) {
    const dockerMetricCard = document.querySelector('.docker.metric-card');

    if (!dockerMetricCard) return;

    let dockerFragment = `
      <div class="card-header">
        <h3>Docker Containers</h3>
        <span class="refresh-indicator" title="Data is up to date"></span>
      </div>
      <div class="card-content">
        <div class="container-grid">
          <div class="loader text-center"></div>
        </div>
      </div>`;
    dockerMetricCard.innerHTML = dockerFragment;

    const containers = data.containers;
    const containerGrid = document.querySelector('.container-grid');
    if (!containerGrid) return;

    if (containers.length === 0) {
      containerGrid.innerHTML = '<div class="no-containers">No Docker containers are currently running.</div>';
      return;
    }

    const fragment = document.createDocumentFragment();
    containers.forEach(container => {
      const item = document.createElement('div');
      item.className = 'container-item';
      item.innerHTML = `
            <div class="container-header">
                <span class="container-name">${this.sanitizeHTML(container.name)}</span>
                <span class="container-status ${container.status === 'running' ? 'running' : 'stopped'}">
                    ${container.status}
                </span>
            </div>
            <div class="container-details">
                <div class="detail-item">
                    <span class="detail-label">Image:</span>
                    <span class="detail-value container-image">${this.sanitizeHTML(container.image)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Created:</span>
                    <span class="detail-value container-created">${this.sanitizeHTML(container.created)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">CPU:</span>
                    <span class="detail-value container-cpu">${container.cpu_percent}%</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Memory:</span>
                    <span class="detail-value container-memory">${container.memory.usage} (${container.memory.percent}%)</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Network Received:</span>
                    <span class="detail-value container-network-received">${container.network.received}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Network Transmitted:</span>
                    <span class="detail-value container-network-transmitted">${container.network.transmitted}</span>
                </div>
            </div>
        `;
      fragment.appendChild(item);
    });

    containerGrid.innerHTML = '';
    containerGrid.appendChild(fragment);
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
      'network-received': data.network_received,
      'network-sent': data.network_sent,
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
      'process-count': data.process_count,
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
    setInterval(() => this.updateSystemInfo(), CONFIG.REFRESH_INTERVAL);
    setInterval(() => this.updateDashboard(), 30000);
    setInterval(() => this.fetchContainerData(), 30000);
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


const categoryFilter = document.getElementById('categoryFilter');
const servicesTable = document.getElementById('servicesTable').getElementsByTagName('tbody')[0];
const rowsPerPageSelect = document.getElementById('rowsPerPage');
let serviceData = {};
let categories = [];
let rowsPerPage = localStorage.getItem('rowsPerPage') || 5;

function getStatusBadgeClass(status) {
  return status.toLowerCase() === 'running' ? 'status-running' : 'status-stopped';
}

// Fetch categories and populate the filter
fetch(CONFIG.API_ENDPOINTS.SYSTEM_SERVICE_CATEGORIES_API)
  .then(response => response.json())
  .then(data => {
    categories = data.categories;
    categories.forEach(category => {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = category;
      categoryFilter.appendChild(option);
    });
  });

// Fetch and display service data
function fetchServices(category = 'all') {
  const url = category === 'all' ? CONFIG.API_ENDPOINTS.SYSTEM_SERVICES_API : `${CONFIG.API_ENDPOINTS.SYSTEM_SERVICES_API}/${category}`;
  fetch(url)
    .then(response => response.json())
    .then(data => {
      serviceData = data;
      displayServices(category);
    });
}

function displayServices(category) {
  servicesTable.innerHTML = '';
  const services = category === 'all' ? Object.values(serviceData.services).flat() : serviceData.processes;
  const startIndex = 0;
  const endIndex = Math.min(parseInt(rowsPerPage), services.length);

  for (let i = startIndex; i < endIndex; i++) {
    const service = services[i];
    const row = servicesTable.insertRow();
    row.innerHTML = `
      <td>${service.pid}</td>
      <td>${service.name}</td>
      <td><span class="status-badge ${getStatusBadgeClass(service.status)}">${service.status}</span></td>
      <td>${service.cpu}%</td>
      <td>${service.memory_mb} MB</td>
  `;
  }
}

categoryFilter.addEventListener('change', (e) => {
  fetchServices(e.target.value);
});

rowsPerPageSelect.value = rowsPerPage;
rowsPerPageSelect.addEventListener('change', (e) => {
  rowsPerPage = e.target.value;
  localStorage.setItem('rowsPerPage', rowsPerPage);
  fetchServices(categoryFilter.value);
});

// Initial data fetch
fetchServices();

// Add this to your homepage.js
class APIMetricsManager {
  constructor() {
    this.histogramChart = null;
    this.metricToEndpoints = {};
    this.initialized = false;

    this.elements = {
      metricSelector: document.getElementById('apiMetricSelector'),
      endpointSelector: document.getElementById('apiEndpointSelector'),
      loading: document.getElementById('apiMetricsLoading'),
      content: document.getElementById('apiMetricsContent'),
      placeholder: document.getElementById('apiMetricsPlaceholder'),
      totalCount: document.getElementById('apiTotalCount'),
      totalSum: document.getElementById('apiTotalSum'),
      avgDuration: document.getElementById('apiAvgDuration')
    };

    this.initializeEventListeners();
  }

  async initialize() {
    if (this.initialized) return;
    await this.fetchEndpoints();
    this.initialized = true;
  }

  async fetchEndpoints() {
    try {
      const response = await fetch('/api/v1/histogram/endpoints');
      const endpoints = await response.json();

      for (const [endpoint, metrics] of Object.entries(endpoints)) {
        metrics.forEach(metric => {
          if (!this.metricToEndpoints[metric]) {
            this.metricToEndpoints[metric] = [];
          }
          this.metricToEndpoints[metric].push(endpoint);
        });
      }

      this.populateMetricSelector();
    } catch (error) {
      console.error('Error fetching endpoints:', error);
    }
  }

  populateMetricSelector() {
    this.elements.metricSelector.innerHTML = '<option value="">Select a metric</option>';
    Object.keys(this.metricToEndpoints).sort().forEach(metric => {
      const option = document.createElement('option');
      option.value = metric;
      option.textContent = metric;
      this.elements.metricSelector.appendChild(option);
    });
  }

  populateEndpointSelector(metric) {
    this.elements.endpointSelector.innerHTML = '<option value="">Select an endpoint</option>';
    const endpoints = this.metricToEndpoints[metric];

    if (endpoints) {
      endpoints.sort().forEach(endpoint => {
        const option = document.createElement('option');
        option.value = endpoint;
        option.textContent = endpoint;
        this.elements.endpointSelector.appendChild(option);
      });
      this.elements.endpointSelector.disabled = false;
    } else {
      this.elements.endpointSelector.disabled = true;
    }
  }

  showLoading(show) {
    this.elements.loading.style.display = show ? 'block' : 'none';
    this.elements.content.style.display = show ? 'none' : 'block';
    this.elements.placeholder.style.display = show ? 'none' : 'none';
  }

  showContent(show) {
    this.elements.content.style.display = show ? 'block' : 'none';
    this.elements.placeholder.style.display = show ? 'none' : 'block';
  }

  updateMetrics(data) {
    this.elements.totalCount.textContent = data.count.toFixed(2);
    this.elements.totalSum.textContent = data.sum.toFixed(2);
    this.elements.avgDuration.textContent = data.average.toFixed(3);
    this.updateHistogramChart(data.buckets);
  }

  updateHistogramChart(buckets) {
    const ctx = document.getElementById('apiHistogramChart').getContext('2d');

    if (this.histogramChart) {
      this.histogramChart.destroy();
    }

    this.histogramChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: buckets.map(b => b.le),
        datasets: [{
          label: 'Request Count',
          data: buckets.map(b => b.value),
          backgroundColor: 'rgba(74, 144, 226, 0.6)',
          borderColor: 'rgba(74, 144, 226, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  }

  async fetchMetrics(endpoint, metricName) {
    this.showLoading(true);

    try {
      if (endpoint === '/') endpoint = 'root';
      const response = await fetch(`/api/v1/histogram/data/${endpoint}/${metricName}`);
      const data = await response.json();

      if (data.error) {
        console.error('Error loading metrics:', data.error);
        return;
      }

      this.updateMetrics(data);
      this.showContent(true);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      this.showLoading(false);
    }
  }

  initializeEventListeners() {
    this.elements.metricSelector.addEventListener('change', (e) => {
      const metric = e.target.value;
      this.populateEndpointSelector(metric);
      this.elements.endpointSelector.value = '';
      this.showContent(false);
    });

    this.elements.endpointSelector.addEventListener('change', (e) => {
      const endpoint = e.target.value;
      const metricName = this.elements.metricSelector.value;

      if (endpoint && metricName) {
        this.fetchMetrics(endpoint, metricName);
      } else {
        this.showContent(false);
      }
    });
  }
}


// Initialize API Metrics when the page loads
document.addEventListener('DOMContentLoaded', () => {
  const apiMetrics = new APIMetricsManager();
  apiMetrics.initialize();
});

// Notification System State Management
const NotificationSystem = {
  count: 0,
  observers: new Set(),

  updateCount(newCount) {
    this.count = newCount;
    this.notifyObservers();
  },

  addObserver(callback) {
    this.observers.add(callback);
  },

  removeObserver(callback) {
    this.observers.delete(callback);
  },

  notifyObservers() {
    this.observers.forEach(callback => callback(this.count));
  }
};

// Handle notification badge updates
class NotificationBadge {
  constructor() {
    this.badges = document.getElementsByClassName('alert-badge');
    this.setupBadgeObserver();
  }

  setupBadgeObserver() {
    NotificationSystem.addObserver((count) => this.updateBadges(count));
  }

  updateBadges(count) {
    const badgeHTML = count > 0 ? this.createBadgeElement() : '';
    Array.from(this.badges).forEach(badge => {
      badge.innerHTML = badgeHTML;
      // Add animation class when adding badge
      if (count > 0) {
        badge.classList.add('notification-badge-enter');
        setTimeout(() => badge.classList.remove('notification-badge-enter'), 300);
      }
    });
  }

  createBadgeElement() {
    return `
      <span class="absolute top-1.5 right-1.5 flex h-2.5 w-2.5">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 ring-2 ring-white"></span>
      </span>
    `;
  }
}

// Toast Message Handler
class ToastMessage {
  constructor() {
    this.container = document.getElementById('message-container');
    this.activeToasts = new Set();
  }

  show(message, type = 'success', duration = 3000) {
    const toast = this.createToastElement(message, type);
    this.container.appendChild(toast);

    // Add entrance animation
    requestAnimationFrame(() => {
      toast.classList.add('toast-enter');
    });

    const toastId = setTimeout(() => {
      this.removeToast(toast);
    }, duration);

    this.activeToasts.add({ element: toast, timeoutId: toastId });
  }

  removeToast(toast) {
    toast.classList.add('toast-exit');
    toast.addEventListener('transitionend', () => {
      if (this.container.contains(toast)) {
        this.container.removeChild(toast);
      }
      this.activeToasts.delete(toast);
    });
  }

  createToastElement(message, type) {
    const toast = document.createElement('div');
    toast.className = `
      p-4 mb-4 text-sm rounded-lg transform translate-y-2 opacity-0 transition-all duration-300
      ${type === 'success'
        ? 'text-green-700 bg-green-100'
        : 'text-red-700 bg-red-100'}
    `;
    toast.innerText = message;
    return toast;
  }

  clearAll() {
    this.activeToasts.forEach(({ element, timeoutId }) => {
      clearTimeout(timeoutId);
      this.removeToast(element);
    });
    this.activeToasts.clear();
  }
}

// Notification Handler
class NotificationHandler {
  constructor() {
    this.container = document.getElementById('notification-container');
    this.toast = new ToastMessage();
    this.badge = new NotificationBadge();
  }

  async fetchNotifications() {
    try {
      const response = await fetch(CONFIG.API_ENDPOINTS.SYSTEM_NOTIFICATIONS_API);
      if (!response.ok) throw new Error('Network response was not ok');

      const notifications = await response.json();
      NotificationSystem.updateCount(notifications.length);
      this.renderNotifications(notifications);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      this.toast.show('Failed to load notifications', 'error');
    }
  }

  renderNotifications(notifications) {
    this.container.innerHTML = '';

    if (notifications.length === 0) {
      this.renderEmptyState();
      return;
    }

    const fragment = document.createDocumentFragment();
    notifications.forEach(notification => {
      fragment.appendChild(this.createNotificationElement(notification));
    });
    
    if (notifications.length > 1) {
      const markAll = document.createElement('button');
      markAll.className = 'mark-all bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4';
      markAll.textContent = 'Mark all as read';
      markAll.addEventListener('click', async () => {
        try {
        const response = await fetch('/api/v1/mark_all_notifications', {
          method: 'POST',
          headers: {
          'Content-Type': 'application/json',
          },
        });

        if (!response.ok) throw new Error('Failed to mark all notifications as read');
        else {
          this.toast.show('All notifications marked as read', 'success');
          this.fetchNotifications();
        }
        } catch (error) {
        console.error('Error marking all notifications as read:', error);
        this.toast.show('Failed to mark all notifications as read', 'error');
        }
      });
      fragment.appendChild(markAll);
    }
    this.container.appendChild(fragment);
    
  }

  createNotificationElement(notification) {
    const element = document.createElement('div');
    element.id = `notification-${notification.id}`;
    element.className = `
      relative flex p-4 space-x-3 hover:bg-slate-50 
      transition-all duration-300 ease-in-out
      ${notification.unread ? 'bg-blue-50/40' : ''}
    `;

    element.innerHTML = `
      <div class="flex-shrink-0">
        <span class="inline-flex items-center justify-center h-10 w-10 rounded-full ${this.getNotificationClass(notification.type)}">
          <i class="fas fa-${notification.icon} w-5 h-5"></i>
        </span>
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-slate-900">${notification.title}</p>
        <p class="text-sm text-slate-500 line-clamp-2">${notification.message}</p>
        <p class="mt-1 text-xs text-slate-400">${notification.time}</p>
      </div>
      <button 
        class="absolute right-0 top-4 text-gray-400 hover:text-gray-600 transition-colors duration-200" 
        onclick="notificationHandler.markAsRead(${notification.id})" 
        aria-label="Mark as read">
        <i class="fas fa-times"></i>
      </button>
    `;

    return element;
  }

  renderEmptyState() {
    this.container.innerHTML = `
      <div class="p-8 text-center">
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 mb-4">
          <i class="fas fa-bell text-slate-400 w-6 h-6"></i>
        </div>
        <p class="text-sm font-medium text-slate-900">No new notifications</p>
        <p class="mt-1 text-sm text-slate-500">We'll notify you when something arrives.</p>
      </div>
    `;
  }

  getNotificationClass(type) {
    const classes = {
      warning: 'bg-amber-100 text-amber-600',
      error: 'bg-red-100 text-red-600',
      success: 'bg-emerald-100 text-emerald-600',
      default: 'bg-blue-100 text-blue-600'
    };
    return classes[type] || classes.default;
  }

  async markAsRead(notificationId) {
    try {
      const response = await fetch(`/api/v1/mark_notification/${notificationId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to mark notification as read');

      const element = document.getElementById(`notification-${notificationId}`);
      if (element) {
        element.classList.add('opacity-0', 'transform', 'translate-x-2');
        setTimeout(() => {
          element.remove();
          NotificationSystem.updateCount(NotificationSystem.count - 1);
          if (this.container.children.length === 0) {
            this.renderEmptyState();
          }
        }, 300);
      }

      this.toast.show('Notification marked as read', 'success');
    } catch (error) {
      console.error('Error marking notification as read:', error);
      this.toast.show('Failed to mark notification as read', 'error');
    }
  }
}

// CSS styles to add to your stylesheet
const styles = `
.notification-badge-enter {
  animation: badge-pop 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes badge-pop {
  0% { transform: scale(0); }
  100% { transform: scale(1); }
}

.toast-enter {
  transform: translateY(0);
  opacity: 1;
}

.toast-exit {
  transform: translateY(-1rem);
  opacity: 0;
}
`;

// Initialize the notification system
const notificationHandler = new NotificationHandler();

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
  notificationHandler.fetchNotifications();

  // Optional: Set up polling for new notifications
  setInterval(() => {
    notificationHandler.fetchNotifications();
  }, 30000); // Poll every 30 seconds
});

// header status
async function fetchStatus() {
  const response = await fetch(CONFIG.API_ENDPOINTS.SYSTEM_STATUS_API);
  const data = await response.json();
  updateStatus(data);
}

function updateStatus(data) {
  const systemStatus = document.getElementById('system-status');

  // {
  //   "service": {
  //     "alert_manager_health": "healthy",
  //     "db_health": "healthy",
  //     "prometheus_health": "healthy",
  //     "running_services": 3,
  //     "status": "3/3 Services Running",
  //     "total_services": 3
  //   },
  //   "timestamp": "2024-11-09T03:48:09.007835"
  // }
  

  systemStatus.innerHTML = `
    <div class="flex items-center space-x-4">
       <div class="flex items-center px-3 py-1.5 ${data.service.running_services === data.service.total_services ? 'bg-green-50' : 'bg-red-50'} rounded-full shadow-sm">
        <svg class="w-4 h-4 ${data.service.running_services === data.service.total_services ? 'text-green-500' : 'text-red-500'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
        <span class="ml-2 text-sm font-medium ${data.service.running_services === data.service.total_services ? 'text-green-700' : 'text-red-700'}">${data.service.status}</span>
      </div>
      <div class="flex items-center px-3 py-1.5 ${data.service.prometheus_health === 'healthy' ? 'bg-green-50' : 'bg-red-50'} rounded-full shadow-sm">
        <svg class="w-4 h-4 ${data.service.prometheus_health === 'healthy' ? 'text-green-500' : 'text-red-500'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
        <span class="ml-2 text-sm font-medium ${data.service.prometheus_health === 'healthy' ? 'text-green-700' : 'text-red-700'}">Prometheus: ${data.service.prometheus_health}</span>
      </div>
      <div class="flex items-center px-3 py-1.5 ${data.service.alert_manager_health === 'healthy' ? 'bg-green-50' : 'bg-red-50'} rounded-full shadow-sm">
        <svg class="w-4 h-4 ${data.service.alert_manager_health === 'healthy' ? 'text-green-500' : 'text-red-500'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
        <span class="ml-2 text-sm font-medium ${data.service.alert_manager_health === 'healthy' ? 'text-green-700' : 'text-red-700'}">Alert Manager: ${data.service.alert_manager_health}</span>
      </div>
      <div class="flex items-center px-3 py-1.5 ${data.service.db_health === 'healthy' ? 'bg-green-50' : 'bg-red-50'} rounded-full shadow-sm">
        <svg class="w-4 h-4 ${data.service.db_health === 'healthy' ? 'text-green-500' : 'text-red-500'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
        <span class="ml-2 text-sm font-medium ${data.service.db_health === 'healthy' ? 'text-green-700' : 'text-red-700'}">DB: ${data.service.db_health}</span>
      </div>
     
    </div>
  `;
      


}

// Call fetchStatus every 2 seconds
window.onload = () => {
  fetchStatus();
  setInterval(fetchStatus, 2000);
};
