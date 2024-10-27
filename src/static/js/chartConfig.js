document.getElementById('addConfigBtn').addEventListener('click', function () {
    document.getElementById('addModal').style.display = 'block';
});

document.querySelectorAll('.btn-delete').forEach(button => {
    button.addEventListener('click', function () {
        const id = this.getAttribute('data-id');
        if (confirm('Are you sure you want to delete this configuration?')) {
            fetch(`/chart_configurations/${id}`, { method: 'DELETE' })
                .then(response => {
                    if (response.ok) {
                        location.reload();
                    } else {
                        return response.json().then(err => {
                            alert('Error deleting configuration: ' + err.message);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while trying to delete the configuration.');
                });
        }
    });
});

document.querySelectorAll('.btn-edit').forEach(button => {
    button.addEventListener('click', function () {
        document.getElementById('configId').value = this.getAttribute('data-id');
        document.getElementById('metricName').value = this.getAttribute('data-metric-name');
        document.getElementById('title').value = this.getAttribute('data-title');
        document.getElementById('xlabel').value = this.getAttribute('data-xlabel');
        document.getElementById('ylabel').value = this.getAttribute('data-ylabel');
        document.getElementById('tension').value = this.getAttribute('data-tension');
        document.getElementById('pointRadius').value = this.getAttribute('data-point-radius');
        document.getElementById('pointHoverRadius').value = this.getAttribute('data-point-hover-radius');

        // Update outputs to reflect current values
        document.querySelector('#tension + output').value = document.getElementById('tension').value;
        document.querySelector('#pointRadius + output').value = document.getElementById('pointRadius').value;
        document.querySelector('#pointHoverRadius + output').value = document.getElementById('pointHoverRadius').value;

        document.getElementById('chartType').value = this.getAttribute('data-chart-type');

        document.getElementById('editModal').style.display = 'block';
    });
});


const closeButton = document.querySelector('.close');
if (closeButton) {
    closeButton.onclick = function () {
        document.getElementById('editModal').style.display = 'none';
    };
}

document.querySelectorAll('.is-active').forEach(checkbox => {
    checkbox.addEventListener('change', function () {
        const id = this.getAttribute('data-id');
        const isActive = this.checked;
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
    
        fetch(`/chart_configurations/${id}/activate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({ is_active: isActive })
        }).then(response => {
            if (response.ok) {
                // Configuration updated successfully
            } else {
                // Error updating configuration
            }
        });
    });
});