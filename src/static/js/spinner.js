const spinnerOverlay = document.getElementById('spinnerOverlay');

function showSpinner() {
    spinnerOverlay.classList.add('show');
}

function hideSpinner() {
    spinnerOverlay.classList.remove('show');
}

// Show spinner when starting to navigate away from the page
window.addEventListener('beforeunload', showSpinner);

// Show spinner when clicking on links
document.addEventListener('click', function (event) {
    const target = event.target.closest('a');
    if (target && target.href && !target.target && target.href.indexOf(location.hostname) !== -1) {
        showSpinner();
    }
});

// Hide spinner when the page has finished loading
window.addEventListener('load', hideSpinner);