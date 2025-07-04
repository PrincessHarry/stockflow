// Toast notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg transform transition-all duration-300 ease-in-out ${
        type === 'success' ? 'bg-success text-white' :
        type === 'error' ? 'bg-error text-white' :
        'bg-card text-text'
    }`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Handle HTMX notifications
document.body.addEventListener('htmx:afterRequest', function(evt) {
    const response = evt.detail.xhr.response;
    try {
        const data = JSON.parse(response);
        if (data.message) {
            showNotification(data.message, data.type || 'info');
        }
    } catch (e) {
        // Not a JSON response, ignore
    }
}); 