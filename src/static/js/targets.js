// Function to fetch and populate target data
async function fetchTargetData() {
    const targetTableBody = document.getElementById('target-table-body');
    targetTableBody.innerHTML = '<tr><td colspan="8" class="loading-message">Loading targets...</td></tr>'; // Show loading message

    try {
        const response = await fetch('/api/v1/targets'); // Replace with the actual URL if different
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        targetTableBody.innerHTML = ''; // Clear loading message

        if (data.active_targets && data.active_targets.length > 0) {
            data.active_targets.forEach(target => {
                const row = createTargetRow(target);
                targetTableBody.appendChild(row);
            });
        } else {
            targetTableBody.innerHTML = '<tr><td colspan="8" class="error-message">No active targets found</td></tr>';
        }
    } catch (error) {
        console.error('Error fetching target data:', error);
        targetTableBody.innerHTML = '<tr><td colspan="8" class="error-message">Failed to fetch targets. Please try again later.</td></tr>';
    }
}

// Helper function to create a row for a target
function createTargetRow(target) {
    const row = document.createElement('tr');

    const jobCell = createCell(target.labels.job);
    const instanceCell = createCell(target.labels.instance);
    const healthCell = createCell(target.health, target.health === 'up' ? 'health-up' : 'health-down');
    const lastScrapeCell = createCell(new Date(target.lastScrape).toLocaleString());
    const lastErrorCell = createCell(target.lastError ? target.lastError : 'No Errors');
    const scrapeUrlCell = createCell(target.scrapeUrl);
    const scrapeDurationCell = createCell(target.lastScrapeDuration.toFixed(3));
    const scrapeIntervalCell = createCell(target.discoveredLabels.__scrape_interval__);

    row.appendChild(jobCell);
    row.appendChild(instanceCell);
    row.appendChild(healthCell);
    row.appendChild(lastScrapeCell);
    row.appendChild(lastErrorCell);
    row.appendChild(scrapeUrlCell);
    row.appendChild(scrapeDurationCell);
    row.appendChild(scrapeIntervalCell);

    const dashboardCell = createDashboardCell(target);
    row.appendChild(dashboardCell);


    return row;
}

// Helper function to create a table cell
function createCell(content, className = '') {
    const cell = document.createElement('td');
    cell.textContent = content;
    if (className) {
        cell.className = className;
    }
    return cell;
}

// Helper function to create a dashboard link cell
function createDashboardCell(target) {
    const cell = document.createElement('td');
    if (target.health === 'up') {
        const dashboardLink = document.createElement('a');
        dashboardLink.href = target.scrapeUrl.replace(/\/metrics$/, '');
        dashboardLink.textContent = 'View Dashboard';
        dashboardLink.target = '_blank'; // Open link in a new tab
        dashboardLink.rel = 'noopener noreferrer'; // Security measure for external links
        cell.appendChild(dashboardLink);
    }
    return cell;
}

// Helper function to create a remove target cell
function createRemoveCell(target) {
    const cell = document.createElement('td');
    const removeForm = document.createElement('form');
    removeForm.action = '/targets/remove_target'; // Replace with actual endpoint if needed
    removeForm.method = 'POST';
    removeForm.style.display = 'inline';

    const jobNameInput = createHiddenInput('job_name', target.labels.job);
    const targetInput = createHiddenInput('target_to_remove', target.labels.instance);
    removeForm.appendChild(jobNameInput);
    removeForm.appendChild(targetInput);

    const removeButton = document.createElement('button');
    removeButton.type = 'submit';
    removeButton.className = 'btn btn-danger btn-sm';
    removeButton.innerHTML = '<i class="fas fa-times"></i> Remove';
    removeForm.appendChild(removeButton);

    cell.appendChild(removeForm);
    return cell;
}

// Helper function to create a hidden input
function createHiddenInput(name, value) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    return input;
}

// Fetch the data when the page loads
document.addEventListener('DOMContentLoaded', fetchTargetData);
