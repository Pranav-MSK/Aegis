// State management
const state = {
    currentPage: 1,
    pageSize: parseInt(localStorage.getItem('processPageSize')) || 15,
    serviceData: {},
    filteredServices: [],
    category: 'all'
};

// Initialize UI elements
const elements = {
    categoryFilter: document.getElementById('categoryFilter'),
    pageSizeSelect: document.getElementById('pageSizeSelect'),
    servicesTable: document.getElementById('servicesTable').getElementsByTagName('tbody')[0],
    prevButton: document.getElementById('prevPage'),
    nextButton: document.getElementById('nextPage'),
    startRange: document.getElementById('startRange'),
    endRange: document.getElementById('endRange'),
    totalItems: document.getElementById('totalItems')
};

// Set initial page size from localStorage
elements.pageSizeSelect.value = state.pageSize;

function getStatusBadgeClass(status) {
    return status.toLowerCase() === 'running' ? 'status-running' : 'status-stopped';
}

function updatePagination() {
    const totalPages = Math.ceil(state.filteredServices.length / state.pageSize);
    const start = (state.currentPage - 1) * state.pageSize + 1;
    const end = Math.min(start + state.pageSize - 1, state.filteredServices.length);

    elements.prevButton.disabled = state.currentPage === 1;
    elements.nextButton.disabled = state.currentPage >= totalPages;
    elements.startRange.textContent = start;
    elements.endRange.textContent = end;
    elements.totalItems.textContent = state.filteredServices.length;
}

function displayServices() {
    const start = (state.currentPage - 1) * state.pageSize;
    const end = start + state.pageSize;
    const pageServices = state.filteredServices.slice(start, end);

    elements.servicesTable.innerHTML = '';
    pageServices.forEach(service => {
        const row = elements.servicesTable.insertRow();
        row.innerHTML = `
            <td>${service.pid}</td>
            <td>${service.name}</td>
            <td><span class="status-badge ${getStatusBadgeClass(service.status)}">${service.status}</span></td>
            <td>${service.cpu}%</td>
            <td>${service.memory_mb} MB</td>
            <td>${service.ports.join(', ') || '-'}</td>
            <td>${service.uptime_human}</td>
            <td>${service.cmd}</td>
            {% if session.get('sudo_password') %}
            <td>
                <button onclick="killProcess(${service.pid}, '${service.name}')" class="kill-button">
                    Kill Process
                </button>
            </td>
            {% endif %}
        `;
    });

    updatePagination();
}


async function fetchServices() {
    try {
        const url = state.category === 'all' ? '/api/v1/system/services' : `/api/v1/system/services/${state.category}`;
        const response = await fetch(url);
        state.serviceData = await response.json();
        state.filteredServices = state.category === 'all' 
            ? Object.values(state.serviceData.services).flat() 
            : state.serviceData.processes;
        displayServices();
    } catch (error) {
        console.error('Error fetching services:', error);
    }
}

// Event Listeners
elements.categoryFilter.addEventListener('change', (e) => {
    state.category = e.target.value;
    state.currentPage = 1;
    fetchServices();
});

elements.pageSizeSelect.addEventListener('change', (e) => {
    state.pageSize = parseInt(e.target.value);
    state.currentPage = 1;
    localStorage.setItem('processPageSize', state.pageSize);
    displayServices();
});

elements.prevButton.addEventListener('click', () => {
    if (state.currentPage > 1) {
        state.currentPage--;
        displayServices();
    }
});

elements.nextButton.addEventListener('click', () => {
    const totalPages = Math.ceil(state.filteredServices.length / state.pageSize);
    if (state.currentPage < totalPages) {
        state.currentPage++;
        displayServices();
    }
});

// Auto-refresh every 30 seconds
setInterval(fetchServices, 30000);

// Initial fetch
fetchServices();