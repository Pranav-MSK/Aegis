// Function to fetch data from Alertmanager API
async function fetchAlertmanagerData() {
    try {
        const response = await fetch('/api/v1/alertmanagers');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.status === "success") {
            return data.data.activeAlertmanagers || [];
        } else {
            console.error("API returned unsuccessful status");
            return [];
        }
    } catch (error) {
        console.error("Error fetching alertmanager data:", error);
        document.getElementById('statusIndicator').innerHTML = `
                    <span class="h-3 w-3 bg-red-500 rounded-full mr-2"></span>
                    <span class="text-sm text-red-600">Connection Error</span>
                `;
        return [];
    }
}

// Function to calculate response time
let startTime;
async function measureResponseTime() {
    startTime = performance.now();
    await fetchAlertmanagerData();
    const endTime = performance.now();
    const responseTime = Math.round(endTime - startTime);
    document.getElementById('responseTime').textContent = `${responseTime}ms`;
}

function updateTable(data = []) {
    const tableBody = document.getElementById('alertmanagerTableBody');
    const noAlertmanagers = document.getElementById('noAlertmanagers');

    if (data.length === 0) {
        tableBody.innerHTML = '';
        noAlertmanagers.classList.remove('hidden');
        return;
    }

    noAlertmanagers.classList.add('hidden');
    tableBody.innerHTML = data.map(am => `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            active
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div class="flex items-center">
                            <svg class="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                            </svg>
                            ${am.url}
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${am.cluster || 'Default Cluster'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div class="flex items-center space-x-2">
                            <button onclick="openDashboard('${am.url}')" 
                                    class="text-blue-600 hover:text-blue-800">
                                View Dashboard
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
}

async function updateStats(data) {
    document.getElementById('totalInstances').textContent = data.length;
    const uniqueClusters = new Set(data.map(am => am.cluster || 'Default Cluster'));
    document.getElementById('activeClusters').textContent = uniqueClusters.size;
}

async function refreshData() {
    const refreshButton = document.querySelector('button[onclick="refreshData()"]');
    refreshButton.disabled = true;
    refreshButton.querySelector('svg').classList.add('animate-spin');

    try {
        const data = await fetchAlertmanagerData();
        updateTable(data);
        updateStats(data);
        await measureResponseTime();

        // Update status indicator
        document.getElementById('statusIndicator').innerHTML = `
                    <span class="h-3 w-3 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                    <span class="text-sm text-gray-600">System Operational</span>
                `;
    } catch (error) {
        console.error("Error refreshing data:", error);
    } finally {
        refreshButton.disabled = false;
        refreshButton.querySelector('svg').classList.remove('animate-spin');
    }
}

async function checkHealth(url) {
    try {
        const response = await fetch(`${url}/-/healthy`);
        const isHealthy = response.ok;

        // Show toast notification
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 ${isHealthy ? 'bg-green-500' : 'bg-red-500'} text-white px-6 py-3 rounded-lg shadow-lg`;
        toast.textContent = isHealthy ? 'Instance is healthy' : 'Instance is unhealthy';
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 3000);
    } catch (error) {
        console.error("Error checking health:", error);
    }
}

function exportData() {
    const data = Array.from(document.querySelectorAll('#alertmanagerTableBody tr')).map(row => ({
        status: row.querySelector('td:nth-child(1) span').textContent,
        url: row.querySelector('td:nth-child(2) div').textContent,
        cluster: row.querySelector('td:nth-child(3)').textContent,
    }));
    const csv = [
        ['Status', 'URL', 'Cluster'],
        ...data.map(row => [row.status, row.url, row.cluster])
    ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'alertmanager_data.csv';
    a.click();
    URL.revokeObjectURL(url);
}

function openDashboard(url) {
    window.open(url, '_blank');
}

// Initialize everything
document.addEventListener('DOMContentLoaded', async () => {
    // Initial data fetch
    const data = await fetchAlertmanagerData();
    console.log(data);
    updateTable(data);
    updateStats(data);
    await measureResponseTime();

    // Setup search functionality
    document.getElementById('searchInput').addEventListener('input', async (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const allData = await fetchAlertmanagerData();
        const filtered = allData.filter(am =>
            am.url.toLowerCase().includes(searchTerm) ||
            (am.cluster || 'Default Cluster').toLowerCase().includes(searchTerm)
        );
        updateTable(filtered);
    });

    // Populate cluster filter
    const clusterFilter = document.getElementById('clusterFilter');
    const data2 = await fetchAlertmanagerData();
    const clusters = [...new Set(data2.map(am => am.cluster || 'Default Cluster'))];
    clusters.forEach(cluster => {
        const option = document.createElement('option');
        option.value = cluster;
        option.textContent = cluster;
        clusterFilter.appendChild(option);
    });

    // Setup cluster filter functionality
    clusterFilter.addEventListener('change', async (e) => {
        const selectedCluster = e.target.value;
        const allData = await fetchAlertmanagerData();
        const filtered = selectedCluster
            ? allData.filter(am => (am.cluster || 'Default Cluster') === selectedCluster)
            : allData;
        updateTable(filtered);
    });

    // Set up auto-refresh every 30 seconds
    setInterval(refreshData, 30000);
});