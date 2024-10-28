class PageLoader {
    constructor() {
        this.loader = document.getElementById('loader');
        this.progressBar = document.getElementById('progressBar');
        this.loadingText = document.getElementById('loadingText');
        this.progress = 0;
        this.isLoading = true;
        this.boundHandleNavigation = this.handleNavigation.bind(this);
        
        this.init();
    }

    init() {
        // Show loader immediately
        this.show();
        
        // Start progress animation
        this.animateProgress();
        
        // Add event listeners
        window.addEventListener('load', () => this.hide());
        window.addEventListener('popstate', this.boundHandleNavigation);
        window.addEventListener('beforeunload', () => this.show());
        
        // Simulate minimum loading time
        setTimeout(() => {
            if (document.readyState === 'complete') {
                this.hide();
            }
        }, 800);
    }

    show() {
        this.isLoading = true;
        this.loader.classList.remove('fade-out');
        this.loader.style.display = 'flex';
        this.progress = 0;
        this.updateProgress();
    }

    hide() {
        if (!this.isLoading) return;
        
        this.isLoading = false;
        this.progress = 100;
        this.updateProgress();
        
        setTimeout(() => {
            this.loader.classList.add('fade-out');
            setTimeout(() => {
                this.loader.style.display = 'none';
            }, 500);
        }, 200);
    }

    updateProgress() {
        this.progressBar.style.width = `${this.progress}%`;
    }

    animateProgress() {
        if (!this.isLoading) return;

        const increment = (100 - this.progress) / 50;
        this.progress = Math.min(this.progress + increment, 90);
        this.updateProgress();

        setTimeout(() => this.animateProgress(), 100);
    }

    handleNavigation(event) {
        // Show loader when navigating
        this.show();

        // Update loading text
        this.loadingText.textContent = 'Navigating back...';

        // Hide after a short delay if the page is already loaded
        setTimeout(() => {
            if (document.readyState === 'complete') {
                this.hide();
            }
        }, 500);
    }
}

// Initialize loader
const pageLoader = new PageLoader();

class NavigationController {
    constructor() {
        this.warningDialog = document.getElementById('warningDialog');
        this.isDialogVisible = false;
        this.setupEventListeners();
        this.pushInitialState();
    }

    setupEventListeners() {
        // Prevent back/forward navigation
        window.addEventListener('popstate', (e) => {
            this.handleNavigation(e);
        });

        // Prevent keyboard navigation
        window.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });
    }

    pushInitialState() {
        // Push initial state to prevent immediate back navigation
        history.pushState({ page: 'initial' }, '', window.location.href);
    }

    handleNavigation(event) {
        // Prevent the navigation
        history.pushState(null, '', window.location.href);
        // Show warning
        // this.showWarning();
    }

    handleKeyboardNavigation(event) {
        // Prevent Alt + Left/Right (browser back/forward)
        if (event.altKey && (event.key === 'ArrowLeft' || event.key === 'ArrowRight')) {
            event.preventDefault();
            // this.showWarning();
        }

        // Prevent Backspace navigation when not in an input field
        if (event.key === 'Backspace' && 
            !event.target.matches('input, textarea, [contenteditable]')) {
            event.preventDefault();
            // this.showWarning();
        }
    }

    handleBeforeUnload(event) {
        // Optional: Show confirmation dialog when trying to leave the page
        event.preventDefault();
        return event.returnValue = "Are you sure you want to leave?";
    }

    showWarning() {
        if (!this.isDialogVisible) {
            this.isDialogVisible = true;
            this.warningDialog.classList.remove('hidden');
            // Add animation classes
            this.warningDialog.classList.add('animate-fade-in');
        }
    }

    hideWarning() {
        this.isDialogVisible = false;
        this.warningDialog.classList.add('hidden');
    }
}

// Initialize the navigation controller
const navigationController = new NavigationController();

// Global function to hide warning
function hideWarning() {
    navigationController.hideWarning();
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    sidebar.classList.toggle('-translate-x-full');
    overlay.classList.toggle('hidden');
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function (event) {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (window.innerWidth < 1024 &&
        !sidebar.contains(event.target) &&
        !event.target.closest('button')) {
        sidebar.classList.add('-translate-x-full');
        overlay.classList.add('hidden');
    }
});
