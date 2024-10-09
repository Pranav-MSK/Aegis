const maxDataPoints = 500;  // Number of data points to show on the chart

// Generalized function to create and update a line chart
function createLineChart(canvasId, label, dataStorageKey, borderColor, updateFunc, percentageUsage) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // Retrieve data from localStorage or initialize an empty array
    let dataStorage = JSON.parse(localStorage.getItem(dataStorageKey)) || [];

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(maxDataPoints).fill(''),  // Empty labels for time intervals
            datasets: [{
                label: label,
                data: dataStorage,
                borderColor: borderColor,
                borderWidth: 2,
                fill: true,
                opacity: 0.5,
                tension: 0.6,  // Smooth line
                pointRadius: 0  // Removes the round tip (data points) on the line
            }]
        },
        options: {
            scales: {
                x: {
                    display: false  // Hide the x-axis labels and grid
                },
                y: {
                    display: false,  // Hide the y-axis labels and grid
                    beginAtZero: true,
                    max: 100  // Assuming max value is 100 for CPU and memory usage
                }
            },
            plugins: {
                tooltip: {
                    enabled: true,  // Enable tooltips for interactivity
                    mode: 'nearest',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += Math.round(context.raw * 100) / 100 + '%';
                            return label;
                        }
                    }
                },
                legend: { display: false }  // Show legend on hover for better clarity
            },
            hover: {
                mode: 'nearest',
                intersect: false,
                onHover: (e, elements) => {
                    if (elements.length) {
                        e.target.style.cursor = 'pointer';
                    } else {
                        e.target.style.cursor = 'default';
                    }
                }
            },
            animation: false,  // Disable animation for smooth updates
            responsive: true
        }
    });

    // Function to update the chart with new data
    function updateChart(newUsage) {
        // Add the new data point
        dataStorage.push(newUsage);

        // Keep the data array length within the maxDataPoints
        if (dataStorage.length > maxDataPoints) {
            dataStorage.shift();  // Remove the oldest data point
        }

        // Store the updated data in localStorage under the unique key
        localStorage.setItem(dataStorageKey, JSON.stringify(dataStorage));

        // Update the chart
        chart.update();
    }

    // Set interval to fetch and update data every 2 seconds
    setInterval(() => {
        const newUsage = updateFunc();  // Call the update function to get the current usage
        
        if (percentageUsage) {
            let percentageUsageValue = percentageUsage.style.width;
            percentageUsageValue = parseFloat(percentageUsageValue.replace('%', ''));
            console.log('percentageUsage', percentageUsageValue);
            
            // Find existing span or create a new one
            let span = document.querySelector(`#${canvasId} + span`);
            if (!span) {
            span = document.createElement('span');
            const canvas = document.getElementById(canvasId);
            canvas.parentNode.insertBefore(span, canvas.nextSibling);
            }

            if (percentageUsageValue > 80) {
            span.innerHTML = 'High Usage';
            span.style.color = 'white';
            span.className = 'badge bg-danger position-absolute top-0 end-0 m-3 p-2';
            } else {
            span.innerHTML = 'Normal Usage';
            span.style.color = 'white';
            span.className = 'badge bg-success position-absolute top-0 end-0 m-3 p-2';
            }
        }

        updateChart(newUsage);
    }, 300);
}
