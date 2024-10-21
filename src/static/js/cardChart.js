const maxDataPoints = 500;  // Number of data points to show on the chart

// Generalized function to create and update a line chart
function createLineChart(canvasId, label, dataStorageKey, borderColor, updateFunc, percentageUsage) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    // Retrieve data from localStorage or initialize an empty array
    let dataStorage;
    try {
        dataStorage = JSON.parse(localStorage.getItem(dataStorageKey)) || [];
    } catch (error) {
        console.error('Error retrieving data from localStorage:', error);
        dataStorage = [];
    }

    // Create a gradient color for the line
    const gradient = ctx.createLinearGradient(0, 0, 0, 400); // Adjust height as needed
    gradient.addColorStop(0, 'rgba(154, 62, 35, 1)'); // Start color
    gradient.addColorStop(1, 'rgba(154, 162, 35, 0.2)'); // End color

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(maxDataPoints).fill(''),  // Empty labels for time intervals
            datasets: [{
                label: label,
                data: dataStorage,
                borderColor: gradient, // Use the gradient for the line color
                backgroundColor: 'rgba(154, 162, 35, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.2,  // Smooth line
                pointRadius: 0,  // Use small points for visibility
            }]
        },
        options: {
            scales: {
                x: { display: false },  // Hide the x-axis labels and grid
                y: {
                    display: false,  // Show the y-axis
                    beginAtZero: true,
                    max: 100,  // Assuming max value is 100 for CPU and memory usage
                    grid: {
                        color: 'rgba(200, 200, 200, 0.3)',  // Subtle grid lines
                    },
                }
            },
            plugins: {
                tooltip: {
                    enabled: true,  // Enable tooltips for interactivity
                    callbacks: {
                        label: (context) => {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += Math.round(context.raw * 100) / 100 + '%';
                            return label;
                        }
                    }
                },
                legend: { display: false }  // Hide legend
            },
            hover: {
                mode: 'nearest',
                intersect: false,
                onHover: (e, elements) => {
                    e.target.style.cursor = elements.length ? 'pointer' : 'default';
                }
            },
            animation: false,  // Disable animation for smooth updates
            responsive: true,
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
        try {
            localStorage.setItem(dataStorageKey, JSON.stringify(dataStorage));
        } catch (error) {
            console.error('Error saving data to localStorage:', error);
        }

        // Update the chart
        chart.update();
    }

    // Set interval to fetch and update data every 2 seconds
    setInterval(() => {
        const newUsage = updateFunc();  // Call the update function to get the current usage

        if (percentageUsage) {
            const percentageUsageValue = parseFloat(percentageUsage.style.width.replace('%', ''));
            
            // Find existing span or create a new one
            let span = document.querySelector(`#${canvasId} + span`);
            if (!span) {
                span = document.createElement('span');
                const canvas = document.getElementById(canvasId);
                canvas.parentNode.insertBefore(span, canvas.nextSibling);
            }

            span.innerHTML = percentageUsageValue > 80 ? 'High Usage' : 'Normal Usage';
            span.style.color = 'white';
            span.className = percentageUsageValue > 80 ? 'badge bg-danger position-absolute top-0 end-0 m-3 p-2' : 'badge bg-success position-absolute top-0 end-0 m-3 p-2';
        }

        updateChart(newUsage);
    }, 100); // Change interval to 2 seconds
}
