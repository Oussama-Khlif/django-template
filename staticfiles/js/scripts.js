// Dark mode
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

// Flashing notification
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

function startTitleFlashing() {
    if (!titleFlashingInterval) {
        originalTitle = document.title;
        titleFlashingInterval = setInterval(() => {
            document.title = (document.title === "Nouvelle notification !")
                ? originalTitle
                : "Nouvelle notification !";
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

// Update notifications
function updateNotifications() {
    fetch('/notifications/get/')
        .then(response => response.json())
        .then(data => {
            console.log('Notifications data received:', data);

            const dropdownMenu = document.querySelector('.dropdown-menu[aria-labelledby="navbarDropdown"]');
            const notificationBadge = document.getElementById('notification-count');

            if (notificationBadge) {
                const currentUnreadCount = data.unread_count;
                const storedPreviousCount = getPreviousUnreadCount();

                if (currentUnreadCount > 0) {
                    if (!isInitialLoad && currentUnreadCount > storedPreviousCount) {
                        console.log(`New notifications: ${currentUnreadCount} > ${storedPreviousCount}`);
                        notificationSound.play().catch(err => console.log("Sound playback error:", err));
                    }

                    notificationBadge.textContent = currentUnreadCount;
                    notificationBadge.style.display = '';
                    startTitleFlashing();
                } else {
                    notificationBadge.style.display = 'none';
                    stopTitleFlashing();
                }

                setPreviousUnreadCount(currentUnreadCount);
                
                if (isInitialLoad) {
                    isInitialLoad = false;
                }
            }

            let notificationsHtml = '';

            if (data.notifications.length === 0) {
                notificationsHtml += `
                    <li>
                        <a class="dropdown-item" href="#">Aucune notification</a>
                    </li>
                `;
            } else {
                data.notifications.forEach(notification => {
                    notificationsHtml += `
                        <li>
                            <a class="dropdown-item notification-item" href="/notifications/redirect/${notification.id}/">
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
                        Marquer tout comme lu
                    </a>
                </li>
            `;

            dropdownMenu.innerHTML = notificationsHtml;
        })
        .catch(error => console.error('Error fetching notifications:', error));
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
        
        fetch('/notifications/mark-all-read/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value,
                'Content-Type': 'application/json',
            },
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

// Delete Notifications
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

// Cookie Banner
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