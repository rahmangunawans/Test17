// Real-time notifications with Socket.IO
class NotificationManager {
    constructor() {
        this.socket = null;
        this.notifications = [];
        this.unreadCount = 0;
        this.notificationContainer = null;
        this.notificationBell = null;
        this.notificationBadge = null;
        this.isConnected = false;
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupUI());
        } else {
            this.setupUI();
        }
        
        // Initialize Socket.IO connection
        this.initSocket();
        
        // Load existing notifications
        this.loadNotifications();
    }
    
    setupUI() {
        // Create notification bell in navigation
        this.createNotificationBell();
        
        // Create notification container
        this.createNotificationContainer();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    createNotificationBell() {
        // Find navigation area to add notification bell
        const nav = document.querySelector('nav .flex.items-center');
        if (!nav) return;
        
        // Create notification bell button
        const bellContainer = document.createElement('div');
        bellContainer.className = 'relative mr-4';
        bellContainer.innerHTML = `
            <button id="notification-bell" 
                    class="relative p-2 text-gray-300 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800 rounded-lg">
                <i class="fas fa-bell text-lg"></i>
                <span id="notification-badge" 
                      class="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center hidden">0</span>
            </button>
        `;
        
        nav.appendChild(bellContainer);
        
        this.notificationBell = document.getElementById('notification-bell');
        this.notificationBadge = document.getElementById('notification-badge');
    }
    
    createNotificationContainer() {
        // Create notification dropdown container
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'fixed top-16 right-4 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50 hidden max-h-96 overflow-hidden';
        container.innerHTML = `
            <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Notifikasi</h3>
                <button id="mark-all-read" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">
                    Tandai semua dibaca
                </button>
            </div>
            <div id="notifications-list" class="max-h-80 overflow-y-auto">
                <div class="p-4 text-center text-gray-500 dark:text-gray-400">
                    <i class="fas fa-bell-slash text-2xl mb-2"></i>
                    <p>Tidak ada notifikasi</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(container);
        this.notificationContainer = container;
    }
    
    setupEventListeners() {
        // Toggle notification dropdown
        if (this.notificationBell) {
            this.notificationBell.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleNotificationDropdown();
            });
        }
        
        // Mark all as read
        const markAllReadBtn = document.getElementById('mark-all-read');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (this.notificationContainer && !this.notificationContainer.contains(e.target)) {
                this.notificationContainer.classList.add('hidden');
            }
        });
        
        // Keyboard shortcut for notifications (Ctrl/Cmd + Shift + N)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'N') {
                e.preventDefault();
                this.toggleNotificationDropdown();
            }
        });
    }
    
    initSocket() {
        // Initialize Socket.IO connection
        if (typeof io !== 'undefined') {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to notification server');
                this.isConnected = true;
                this.socket.emit('join_notifications');
            });
            
            this.socket.on('disconnect', () => {
                console.log('Disconnected from notification server');
                this.isConnected = false;
            });
            
            this.socket.on('new_notification', (notification) => {
                this.addNotification(notification);
                this.showNotificationToast(notification);
            });
            
            this.socket.on('notification_status', (data) => {
                console.log('Notification status:', data.status);
            });
            
            this.socket.on('notification_marked_read', (data) => {
                this.markNotificationAsRead(data.notification_id);
            });
        } else {
            console.warn('Socket.IO not loaded, real-time notifications disabled');
        }
    }
    
    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const data = await response.json();
            
            if (data.success) {
                this.notifications = data.notifications;
                this.unreadCount = data.unread_count;
                this.updateUI();
            }
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    }
    
    addNotification(notification) {
        // Add to beginning of array
        this.notifications.unshift(notification);
        
        // Keep only latest 50 notifications
        if (this.notifications.length > 50) {
            this.notifications = this.notifications.slice(0, 50);
        }
        
        // Update unread count
        if (!notification.is_read) {
            this.unreadCount++;
        }
        
        this.updateUI();
    }
    
    updateUI() {
        this.updateNotificationBadge();
        this.updateNotificationList();
    }
    
    updateNotificationBadge() {
        if (this.notificationBadge) {
            if (this.unreadCount > 0) {
                this.notificationBadge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount.toString();
                this.notificationBadge.classList.remove('hidden');
                
                // Add pulse animation for new notifications
                this.notificationBell.classList.add('animate-pulse');
                setTimeout(() => {
                    this.notificationBell.classList.remove('animate-pulse');
                }, 2000);
            } else {
                this.notificationBadge.classList.add('hidden');
            }
        }
    }
    
    updateNotificationList() {
        const notificationsList = document.getElementById('notifications-list');
        if (!notificationsList) return;
        
        if (this.notifications.length === 0) {
            notificationsList.innerHTML = `
                <div class="p-4 text-center text-gray-500 dark:text-gray-400">
                    <i class="fas fa-bell-slash text-2xl mb-2"></i>
                    <p>Tidak ada notifikasi</p>
                </div>
            `;
            return;
        }
        
        notificationsList.innerHTML = this.notifications.map(notification => 
            this.createNotificationHTML(notification)
        ).join('');
        
        // Add event listeners to notification items
        notificationsList.querySelectorAll('[data-notification-id]').forEach(item => {
            item.addEventListener('click', () => {
                const notificationId = parseInt(item.dataset.notificationId);
                this.handleNotificationClick(notificationId);
            });
        });
    }
    
    createNotificationHTML(notification) {
        const timeAgo = this.getTimeAgo(notification.created_at);
        const isUnread = !notification.is_read;
        const typeClass = this.getNotificationTypeClass(notification.type);
        
        return `
            <div class="notification-item p-3 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors duration-150 ${isUnread ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
                 data-notification-id="${notification.id}">
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                        <i class="fas fa-${notification.icon} ${typeClass} text-lg"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center justify-between">
                            <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                                ${notification.title}
                            </p>
                            ${isUnread ? '<div class="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0"></div>' : ''}
                        </div>
                        <p class="text-sm text-gray-600 dark:text-gray-300 mt-1 line-clamp-2">
                            ${notification.message}
                        </p>
                        <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
                            ${timeAgo}
                        </p>
                    </div>
                </div>
            </div>
        `;
    }
    
    getNotificationTypeClass(type) {
        const typeClasses = {
            'info': 'text-blue-500',
            'success': 'text-green-500',
            'warning': 'text-yellow-500',
            'error': 'text-red-500',
            'episode': 'text-purple-500',
            'content': 'text-indigo-500'
        };
        return typeClasses[type] || 'text-gray-500';
    }
    
    getTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) return 'Baru saja';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} menit yang lalu`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} jam yang lalu`;
        if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} hari yang lalu`;
        
        return date.toLocaleDateString('id-ID');
    }
    
    toggleNotificationDropdown() {
        if (this.notificationContainer) {
            this.notificationContainer.classList.toggle('hidden');
        }
    }
    
    async handleNotificationClick(notificationId) {
        // Mark as read
        await this.markNotificationAsRead(notificationId);
        
        // Find the notification
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification && notification.action_url) {
            // Navigate to the action URL
            window.location.href = notification.action_url;
        }
    }
    
    async markNotificationAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/mark_read/${notificationId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Update local state
                const notification = this.notifications.find(n => n.id === notificationId);
                if (notification && !notification.is_read) {
                    notification.is_read = true;
                    this.unreadCount = Math.max(0, this.unreadCount - 1);
                    this.updateUI();
                }
                
                // Emit to socket for real-time update
                if (this.socket) {
                    this.socket.emit('mark_notification_read', { notification_id: notificationId });
                }
            }
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
        }
    }
    
    async markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/mark_all_read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Update local state
                this.notifications.forEach(notification => {
                    notification.is_read = true;
                });
                this.unreadCount = 0;
                this.updateUI();
            }
        } catch (error) {
            console.error('Failed to mark all notifications as read:', error);
        }
    }
    
    showNotificationToast(notification) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'fixed top-20 right-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4 max-w-sm z-50 transform translate-x-full transition-transform duration-300';
        
        const typeClass = this.getNotificationTypeClass(notification.type);
        
        toast.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                    <i class="fas fa-${notification.icon} ${typeClass} text-lg"></i>
                </div>
                <div class="flex-1">
                    <h4 class="text-sm font-medium text-gray-900 dark:text-white">
                        ${notification.title}
                    </h4>
                    <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">
                        ${notification.message}
                    </p>
                </div>
                <button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add close functionality
        const closeBtn = toast.querySelector('button');
        closeBtn.addEventListener('click', () => {
            this.removeToast(toast);
        });
        
        // Add click to view functionality
        toast.addEventListener('click', (e) => {
            if (e.target === closeBtn || closeBtn.contains(e.target)) return;
            
            if (notification.action_url) {
                window.location.href = notification.action_url;
            }
            this.removeToast(toast);
        });
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            this.removeToast(toast);
        }, 5000);
    }
    
    removeToast(toast) {
        toast.classList.add('translate-x-full');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

// Initialize notification manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if user is logged in
    if (document.querySelector('nav')) {
        window.notificationManager = new NotificationManager();
    }
});

// Global functions for triggering notifications (for testing/admin use)
function testNotification() {
    if (window.notificationManager) {
        window.notificationManager.showNotificationToast({
            id: Date.now(),
            title: 'Test Notification',
            message: 'This is a test notification to check the system.',
            type: 'info',
            icon: 'bell',
            action_url: null
        });
    }
}

function createTestNotification(title, message, type = 'info') {
    fetch('/api/notifications', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title: title,
            message: message,
            type: type
        })
    });
}