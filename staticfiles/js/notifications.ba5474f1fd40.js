// Show confirmation modal
function showConfirmationModal(title, message, onConfirm, confirmText = 'Confirm', cancelText = 'Cancel') {
    const modal = document.getElementById('confirmationModal');
    const modalData = modal.__x.$data;
    
    modalData.title = title;
    modalData.message = message;
    modalData.confirmText = confirmText;
    modalData.cancelText = cancelText;
    modalData.onConfirm = onConfirm;
    modalData.show = true;
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    
    // Set toast classes based on type
    const typeClasses = {
        success: 'bg-green-50 border-green-200 text-green-800',
        error: 'bg-red-50 border-red-200 text-red-800',
        warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
        info: 'bg-blue-50 border-blue-200 text-blue-800'
    };
    
    // Set icon based on type
    const icons = {
        success: '<svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>',
        error: '<svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>',
        warning: '<svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>',
        info: '<svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>'
    };
    
    toast.className = `toast-notification ${typeClasses[type]} border rounded-lg shadow-lg p-4 flex items-start space-x-3 max-w-md transform transition-all duration-300 translate-x-full`;
    toast.innerHTML = `
        <div class="flex-shrink-0">
            ${icons[type]}
        </div>
        <div class="flex-1">
            <p class="text-sm font-medium">${message}</p>
        </div>
        <button class="flex-shrink-0 text-gray-400 hover:text-gray-500" onclick="this.parentElement.remove()">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    `;
    
    container.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.transform = 'translateX(full)';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 5000);
}

// Initialize Alpine.js data for confirmation modal
document.addEventListener('alpine:init', () => {
    Alpine.data('confirmationModal', () => ({
        show: false,
        title: '',
        message: '',
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        onConfirm: null
    }));
});

// Add delete confirmation handlers
document.addEventListener('DOMContentLoaded', () => {
    // Handle delete buttons
    document.querySelectorAll('[data-confirm-delete]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const url = button.getAttribute('href');
            const name = button.getAttribute('data-name') || 'this item';
            
            showConfirmationModal(
                'Confirm Deletion',
                `Are you sure you want to delete ${name}? This action cannot be undone.`,
                () => {
                    window.location.href = url;
                },
                'Delete',
                'Cancel'
            );
        });
    });
}); 