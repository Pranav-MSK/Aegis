// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap pills
    const pills = [].slice.call(document.querySelectorAll('[data-bs-toggle="pill"]'));
    pills.forEach(pill => {
        pill.addEventListener('click', function(event) {
            event.preventDefault();
            const target = document.querySelector(this.getAttribute('data-bs-target'));
            
            // Remove active class from all pills and panes
            pills.forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('show', 'active');
            });
            
            // Add active class to clicked pill and its target pane
            this.classList.add('active');
            target.classList.add('show', 'active');
        });
    });

    // Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;
    
    themeToggle.addEventListener('click', () => {
        body.setAttribute('data-theme', 
            body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark'
        );
        
        // Update icon
        const icon = themeToggle.querySelector('i');
        icon.classList.toggle('fa-moon');
        icon.classList.toggle('fa-sun');
        
        // Save preference
        localStorage.setItem('theme', body.getAttribute('data-theme'));
    });

    // Load saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        body.setAttribute('data-theme', savedTheme);
        const icon = themeToggle.querySelector('i');
        if (savedTheme === 'dark') {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        }
    }

    // Sidebar Toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    const dashboardWrapper = document.querySelector('.dashboard-wrapper');
    
    sidebarToggle.addEventListener('click', () => {
        dashboardWrapper.classList.toggle('sidebar-open');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (event) => {
        if (dashboardWrapper.classList.contains('sidebar-open') &&
            !event.target.closest('.dashboard-sidebar') &&
            !event.target.closest('.sidebar-toggle')) {
            dashboardWrapper.classList.remove('sidebar-open');
        }
    });
});