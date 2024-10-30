// let refreshInterval = {{ user_dashboard_settings.refresh_interval * 1000 }}; // Multiply by 1000 initially

// Fetch the refresh interval from the server
fetch('/api/v1/refresh-interval')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            refreshInterval = data.refresh_interval * 1000; // Multiply by 1000 to convert to milliseconds
            // Start refreshing after fetching the interval
        } else {
            // Handle error
        }
    })
    .catch(error => console.error('Error:', error));
    
let refreshTimeout;

// Event listener for select input change
document.getElementById('refresh-interval').addEventListener('change', function () {
    // Clear the existing timeout
    clearTimeout(refreshTimeout);

    // Update the interval based on the selected value
    refreshInterval = parseInt(this.value) * 1000;  // Convert to milliseconds

    // refresh the page once
    refreshTimeout = setTimeout(() => {
        window.location.reload();
    }, refreshInterval);

    // Send the updated refresh interval to the server
    fetch('/api/v1/refresh-interval', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_interval: parseInt(this.value) })  // Send in seconds, not milliseconds
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Refresh interval updated successfully
            } else {
                // Handle error
            }
        })
        .catch(error => console.error('Error:', error));
});
