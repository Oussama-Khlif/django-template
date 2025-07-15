document.addEventListener("DOMContentLoaded", function () {

    const toggleButton = document.getElementById("darkModeToggle");
    const html = document.documentElement;
    const body = document.body;

    if (localStorage.getItem("darkMode") === "enabled") {
        html.classList.add("dark-mode");
        body.classList.add("dark-mode");
        toggleButton.classList.remove("btn-outline-dark");
        toggleButton.classList.add("btn-outline-light");
        toggleButton.innerHTML = '<i class="fas fa-moon"></i>';
    } else {
        toggleButton.innerHTML = '<i class="fas fa-sun"></i>';
    }

    toggleButton.addEventListener("click", function () {
        html.classList.toggle("dark-mode");
        body.classList.toggle("dark-mode");

        if (html.classList.contains("dark-mode")) {
            localStorage.setItem("darkMode", "enabled");
            toggleButton.classList.remove("btn-outline-dark");
            toggleButton.classList.add("btn-outline-light");
            toggleButton.innerHTML = '<i class="fas fa-moon"></i>';
        } else {
            localStorage.setItem("darkMode", "disabled");
            toggleButton.classList.remove("btn-outline-light");
            toggleButton.classList.add("btn-outline-dark");
            toggleButton.innerHTML = '<i class="fas fa-sun"></i>';
        }
    });
});

let titleFlashingInterval = null;
let originalTitle = document.title;
let previousUnreadCount = 0;
let notificationUpdateInterval = null;
let isInitialLoad = true;

const notificationSound = new Audio('/static/sfx/notification.mp3');
notificationSound.volume = 0.5;

function getPreviousUnreadCount() {
    const stored = sessionStorage.getItem('previousUnreadCount');
    return stored ? parseInt(stored, 10) : 0;
}

function setPreviousUnreadCount(count) {
    previousUnreadCount = count;
    sessionStorage.setItem('previousUnreadCount', count.toString());
}

function areSoundsEnabled() {
    console.log('Checking if sounds are enabled...');

    if (typeof userSettings !== 'undefined' && userSettings !== null) {
        console.log('userSettings found:', userSettings);
        if (userSettings.sounds !== undefined) {

            const soundsEnabled = userSettings.sounds === true || userSettings.sounds === 'true' || userSettings.sounds === 'True';
            console.log('Sounds enabled from userSettings:', soundsEnabled);
            return soundsEnabled;
        }
    } else {
        console.log('userSettings not found - variable not defined');
    }

    const soundsSetting = localStorage.getItem('sounds') || sessionStorage.getItem('sounds');
    if (soundsSetting !== null) {
        const soundsEnabled = soundsSetting === 'true';
        console.log('Sounds enabled from storage:', soundsEnabled);
        return soundsEnabled;
    }

    console.log('No sound setting found, defaulting to false');
    return false;
}

function startTitleFlashing() {
    if (!titleFlashingInterval) {
        originalTitle = document.title;
        titleFlashingInterval = setInterval(() => {
            document.title = (document.title === "New notification !")
                ? originalTitle
                : "New notification !";
        }, 1500);
    }
}

function stopTitleFlashing() {
    if (titleFlashingInterval) {
        clearInterval(titleFlashingInterval);
        titleFlashingInterval = null;
        document.title = originalTitle;
    }
}

function getLanguagePrefix() {
    const path = window.location.pathname;
    const pathSegments = path.split('/').filter(segment => segment !== '');

    if (pathSegments.length > 0 && (pathSegments[0] === 'en' || pathSegments[0] === 'fr')) {
        return '/' + pathSegments[0];
    }

    return '/en';
}

function updateNotifications() {
    const languagePrefix = getLanguagePrefix();

    fetch(`${languagePrefix}/notifications/get/`)
        .then(response => response.json())
        .then(data => {
            console.log('Notifications data received:', data);

            const desktopDropdownMenu = document.querySelector('#desktopNotifications + .dropdown-menu');
            const mobileDropdownMenu = document.querySelector('#mobileNotifications + .dropdown-menu');

            const notificationBadge = document.getElementById('notification-count');
            let mobileNotificationBadge = document.getElementById('mobile-notification-count');

            if (!mobileNotificationBadge) {
                const mobileNotificationLink = document.getElementById('mobileNotifications');
                if (mobileNotificationLink) {
                    mobileNotificationBadge = document.createElement('span');
                    mobileNotificationBadge.id = 'mobile-notification-count';
                    mobileNotificationBadge.className = 'badge notification-badge';
                    mobileNotificationLink.appendChild(mobileNotificationBadge);
                    console.log('Created mobile notification badge');
                }
            }

            const currentUnreadCount = data.unread_count;
            const storedPreviousCount = getPreviousUnreadCount();

            if (currentUnreadCount > 0) {
                if (!isInitialLoad && currentUnreadCount > storedPreviousCount) {
                    console.log(`New notifications: ${currentUnreadCount} > ${storedPreviousCount}`);

                    if (areSoundsEnabled()) {
                        notificationSound.play().catch(err => console.log("Sound playback error:", err));
                    } else {
                        console.log("Sound disabled by user settings");
                    }
                }

                if (notificationBadge) {
                    notificationBadge.textContent = currentUnreadCount;
                    notificationBadge.style.display = '';
                }

                if (mobileNotificationBadge) {
                    mobileNotificationBadge.textContent = currentUnreadCount;
                    mobileNotificationBadge.style.display = '';
                    console.log('Updated mobile badge:', currentUnreadCount);
                }

                startTitleFlashing();
            } else {
                if (notificationBadge) {
                    notificationBadge.style.display = 'none';
                }
                if (mobileNotificationBadge) {
                    mobileNotificationBadge.style.display = 'none';
                }
                stopTitleFlashing();
            }

            setPreviousUnreadCount(currentUnreadCount);

            if (isInitialLoad) {
                isInitialLoad = false;
            }

            let notificationsHtml = '';

            if (data.notifications.length === 0) {
                notificationsHtml += `
                    <li>
                        <a class="dropdown-item" href="#">${window.translations.no_notifications}</a>
                    </li>
                `;
            } else {
                data.notifications.forEach(notification => {
                    notificationsHtml += `
                        <li>
                            <a 
                                class="dropdown-item notification-item" 
                                href="${languagePrefix}/notifications/redirect/${notification.id}/"
                                data-type="${notification.type}"
                                data-notification-id="${notification.id}"
                                data-message="${notification.message}">
                                <div class="notification-text">${notification.message}</div>
                                <small class="text-muted d-block">${notification.created_at}</small>
                            </a>
                        </li>
                    `;
                });
            }

            notificationsHtml += `
                <li><hr class="dropdown-divider"></li>
                <li>
                    <a class="dropdown-item text-center" href="#" id="mark-all-read">
                        ${window.translations.mark_all_read}
                    </a>
                </li>
            `;

            if (desktopDropdownMenu) {
                desktopDropdownMenu.innerHTML = notificationsHtml;
            }
            if (mobileDropdownMenu) {
                mobileDropdownMenu.innerHTML = notificationsHtml;
            }

            document.querySelectorAll('.notification-item').forEach(item => {
                item.addEventListener('click', function (e) {
                    e.preventDefault(); 
                    e.stopPropagation(); 

                    const type = this.getAttribute('data-type');
                    const notificationId = this.getAttribute('data-notification-id');
                    const redirectUrl = this.getAttribute('href');
                    const message = this.getAttribute('data-message');

                    console.log(`Notification clicked - type: ${type}, id: ${notificationId}, message: ${message}`);

                    if (type === 'chat') {
                        console.log('Opening chat bubble');

                        const chatBubble = document.getElementById('chat-bubble');
                        if (chatBubble) {
                            chatBubble.click();

                            setTimeout(() => {

                                fetch(redirectUrl, {
                                    method: 'GET',
                                    credentials: 'same-origin'
                                }).then(() => {
                                    console.log('Notification marked as read');

                                    updateNotifications();
                                }).catch(err => {
                                    console.error('Error marking notification as read:', err);
                                });
                            }, 500); 
                        }
                    } else if (type === 'admin') {
                        console.log('Opening admin chat');

                        const username = extractUsernameFromMessage(message);
                        console.log('Extracted username:', username);

                        fetch(redirectUrl, {
                            method: 'GET',
                            credentials: 'same-origin'
                        }).then(() => {
                            console.log('Notification marked as read');

                            const adminChatUrl = `${languagePrefix}/chat/admin/${username ? `?user=${encodeURIComponent(username)}` : ''}`;
                            window.location.href = adminChatUrl;

                            updateNotifications();
                        }).catch(err => {
                            console.error('Error marking notification as read:', err);

                            const adminChatUrl = `${languagePrefix}/chat/admin/${username ? `?user=${encodeURIComponent(username)}` : ''}`;
                            window.location.href = adminChatUrl;
                        });
                    } else {

                        window.location.href = redirectUrl;
                    }
                });
            });

            document.querySelectorAll('#mark-all-read').forEach(button => {
                button.addEventListener('click', function(e) {
                    e.preventDefault();

                    console.log('Mark all as read clicked');
                });
            });
        })
        .catch(error => console.error('Error fetching notifications:', error));
}

function extractUsernameFromMessage(message) {

    const match = message.match(/New message from (.+)/);
    return match ? match[1].trim() : null;
}

function initializeAdminChatPage() {

    if (!window.location.pathname.includes('/chat/admin')) {
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const targetUsername = urlParams.get('user');

    if (targetUsername) {
        console.log('Auto-selecting user from URL parameter:', targetUsername);

        setTimeout(() => {

            if (typeof loadUserMessages === 'function') {
                loadUserMessages(targetUsername);

                const userButtons = document.querySelectorAll('.user-btn');
                userButtons.forEach(button => {
                    if (button.textContent.trim() === targetUsername) {
                        button.classList.add('active');
                        button.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                });
            } else {
                console.error('loadUserMessages function not found. Make sure this script is loaded after the admin chat page scripts.');
            }
        }, 100);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initializeAdminChatPage();
});

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAdminChatPage);
} else {
    initializeAdminChatPage();
}

function cleanup() {
    if (notificationUpdateInterval) {
        clearInterval(notificationUpdateInterval);
        notificationUpdateInterval = null;
    }
    stopTitleFlashing();
}

document.addEventListener('DOMContentLoaded', function () {
    cleanup();

    updateNotifications();

    notificationUpdateInterval = setInterval(updateNotifications, 10000);
});

window.addEventListener('beforeunload', cleanup);

document.addEventListener('click', function (e) {
    if (e.target && e.target.id === 'mark-all-read') {
        e.preventDefault();

        const languagePrefix = getLanguagePrefix();

        fetch(`${languagePrefix}/notifications/mark-read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: '' 
        })
        .then(response => response.json())
        .then(() => {
            stopTitleFlashing();
            setPreviousUnreadCount(0);
            updateNotifications();
        })
        .catch(error => console.error('Error marking notifications as read:', error));
    }
});

document.addEventListener('click', function(e) {
    if (e.target && e.target.id === 'mark-all-read') {
        e.preventDefault();

        fetch('/notifications/mark-read/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateNotifications();  
            }
        })
        .catch(error => console.error('Error marking notifications as read:', error));
    }
});

document.addEventListener('DOMContentLoaded', function() {

    updateNotifications();

    setInterval(updateNotifications, 1000);
});

        (function() {
            const cookieBanner = document.getElementById('cookieBanner');
            if (!cookieBanner) return; 

            const cookiesAccepted = localStorage.getItem('cookiesAccepted') === 'true';

            if (!cookiesAccepted) {
                cookieBanner.style.display = 'block';
            }
        })();

        function acceptCookies() {
            const cookieBanner = document.getElementById('cookieBanner');
            if (!cookieBanner) return;

            localStorage.setItem('cookiesAccepted', 'true');
            cookieBanner.style.display = 'none';
        }

        document.addEventListener('DOMContentLoaded', function() {
            const cookieBanner = document.getElementById('cookieBanner');
            if (!cookieBanner) return;

            if (localStorage.getItem('cookiesAccepted') === 'true') {
                cookieBanner.style.display = 'none';
            }
        });

        let observer = new MutationObserver(function(mutations) {
            if (localStorage.getItem('cookiesAccepted') === 'true') {
                const cookieBanner = document.getElementById('cookieBanner');
                if (cookieBanner) {
                    cookieBanner.style.display = 'none';
                }
            }
        });

        observer.observe(document.body, { 
            childList: true,
            subtree: true 
        });