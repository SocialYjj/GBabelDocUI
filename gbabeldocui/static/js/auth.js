/**
 * Browser authentication state backed by the server-side session cookie.
 */

let authenticatedUser = null;
let currentUserRequest = null;

window.addEventListener('auth:unauthorized', () => {
    authenticatedUser = null;
    currentUserRequest = null;
});

async function loadCurrentUser(forceRefresh = false) {
    if (authenticatedUser && !forceRefresh) {
        return authenticatedUser;
    }
    if (currentUserRequest && !forceRefresh) {
        return currentUserRequest;
    }

    currentUserRequest = api.getCurrentUser()
        .then(userResponse => {
            authenticatedUser = {
                username: userResponse.username,
                is_admin: Boolean(userResponse.is_admin),
            };
            return authenticatedUser;
        })
        .catch(() => {
            authenticatedUser = null;
            return null;
        })
        .finally(() => {
            currentUserRequest = null;
        });
    return currentUserRequest;
}

function getCurrentUser() {
    return authenticatedUser;
}

async function isAuthenticated() {
    return Boolean(await loadCurrentUser());
}

async function requireAuth() {
    const currentUser = await loadCurrentUser();
    if (!currentUser) {
        window.location.assign('/login.html');
        return false;
    }
    return true;
}

async function redirectIfAuthenticated() {
    if (await isAuthenticated()) {
        window.location.assign('/upload.html');
        return true;
    }
    return false;
}

function updateAdminUI() {
    const currentUser = getCurrentUser();
    const isAdmin = Boolean(currentUser && currentUser.is_admin);
    document.querySelectorAll('[data-admin-only]').forEach(adminElement => {
        adminElement.style.display = isAdmin ? '' : 'none';
    });
}

function displayUserInfo() {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        return;
    }
    document.querySelectorAll('[data-username]').forEach(usernameElement => {
        usernameElement.textContent = currentUser.username;
    });
    updateAdminUI();
}

function showLoading(message = 'Loading...') {
    let loadingOverlay = document.getElementById('loading-overlay');
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loading-overlay';
        loadingOverlay.className = 'loading-overlay';

        const loadingContent = document.createElement('div');
        loadingContent.className = 'loading-content';
        const spinner = document.createElement('div');
        spinner.className = 'spinner';
        spinner.setAttribute('aria-hidden', 'true');
        const loadingText = document.createElement('div');
        loadingText.className = 'loading-text';
        loadingContent.append(spinner, loadingText);
        loadingOverlay.appendChild(loadingContent);
        document.body.appendChild(loadingOverlay);
    }

    const loadingText = loadingOverlay.querySelector('.loading-text');
    if (loadingText) {
        loadingText.textContent = message;
    }
    loadingOverlay.setAttribute('role', 'status');
    loadingOverlay.setAttribute('aria-live', 'polite');
    loadingOverlay.hidden = false;
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.hidden = true;
    }
}

function showAlert(message, type = 'info') {
    let alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.className = 'alert-container';
        alertContainer.setAttribute('aria-live', 'polite');
        document.body.appendChild(alertContainer);
    }

    const alertMessage = document.createElement('div');
    alertMessage.className = `alert alert-${type} fade-in`;
    alertMessage.textContent = String(message);
    alertMessage.setAttribute('role', type === 'error' ? 'alert' : 'status');
    alertContainer.appendChild(alertMessage);

    window.setTimeout(() => {
        alertMessage.classList.add('fade-out');
        window.setTimeout(() => alertMessage.remove(), 300);
    }, 3000);
}

function showError(error) {
    const errorMessage = error && (error.message || error.detail)
        ? error.message || error.detail
        : 'An error occurred';
    showAlert(errorMessage, 'error');
}

function showSuccess(message) {
    showAlert(message, 'success');
}

function formatFileSize(bytes) {
    if (!Number.isFinite(bytes) || bytes <= 0) {
        return '0 Bytes';
    }
    const units = ['Bytes', 'KB', 'MB', 'GB'];
    const unitIndex = Math.min(
        units.length - 1,
        Math.floor(Math.log(bytes) / Math.log(1024)),
    );
    const normalizedSize = bytes / (1024 ** unitIndex);
    return `${Math.round(normalizedSize * 100) / 100} ${units[unitIndex]}`;
}

function formatDate(dateString) {
    if (!dateString) {
        return '';
    }
    const normalizedDateString = typeof dateString === 'string'
        && !/(?:Z|[+-]\d{2}:?\d{2})$/i.test(dateString)
        ? `${dateString}Z`
        : dateString;
    const dateValue = new Date(normalizedDateString);
    return Number.isNaN(dateValue.getTime())
        ? String(dateString)
        : dateValue.toLocaleString();
}

function debounce(callback, waitMs) {
    let timeoutIdentifier;
    return function debouncedCallback(...callbackArguments) {
        window.clearTimeout(timeoutIdentifier);
        timeoutIdentifier = window.setTimeout(
            () => callback(...callbackArguments),
            waitMs,
        );
    };
}

async function logout() {
    showLoading('Logging out...');
    try {
        await api.logout();
    } catch (_logoutError) {
        // The browser session is treated as ended even if the server is unavailable.
    } finally {
        authenticatedUser = null;
        currentUserRequest = null;
        hideLoading();
        window.location.assign('/login.html');
    }
}

async function updateUserInfo() {
    const currentUser = await loadCurrentUser();
    if (!currentUser) {
        return null;
    }

    const userInfoElement = document.getElementById('user-info');
    if (userInfoElement) {
        userInfoElement.textContent = currentUser.username;
    }
    displayUserInfo();

    const logoutButton = document.getElementById('logout-btn');
    if (logoutButton && logoutButton.dataset.logoutBound !== 'true') {
        logoutButton.dataset.logoutBound = 'true';
        logoutButton.addEventListener('click', logoutEvent => {
            logoutEvent.preventDefault();
            logout();
        });
    }

    return currentUser;
}
