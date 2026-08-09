function showFormError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    errorElement.textContent = message;
    errorElement.hidden = !message;
}

async function initializeLoginPage() {
    if (await redirectIfAuthenticated()) {
        return;
    }

    const authStatus = await api.checkAuthStatus();
    if (authStatus.version) {
        document.getElementById('app-version').textContent = `GBabelDocUI v${authStatus.version}`;
    }
    const setupForm = document.getElementById('setup-form');
    const loginForm = document.getElementById('login-form');
    setupForm.hidden = !authStatus.setup_required;
    loginForm.hidden = Boolean(authStatus.setup_required);
    document.getElementById('setup-token-group').hidden = !authStatus.setup_token_required;
    document.getElementById('setup-token').required = Boolean(authStatus.setup_token_required);
    if (authStatus.setup_required) {
        document.getElementById('subtitle').textContent = 'First-time setup - create the administrator account';
        return;
    }

    const registrationStatus = await api.checkRegistrationStatus();
    document.getElementById('registration-link').hidden = !registrationStatus.enabled;
}

document.getElementById('setup-form').addEventListener('submit', async submitEvent => {
    submitEvent.preventDefault();
    const username = document.getElementById('setup-username').value.trim();
    const password = document.getElementById('setup-password').value;
    const passwordConfirmation = document.getElementById('setup-password-confirm').value;
    const setupToken = document.getElementById('setup-token').value;
    if (password !== passwordConfirmation) {
        showFormError('setup-error', 'Passwords do not match');
        return;
    }

    showFormError('setup-error', '');
    showLoading('Creating administrator account...');
    try {
        await api.setup(username, password, setupToken);
        showSuccess('Administrator account created');
        window.setTimeout(() => window.location.assign('/upload.html'), 500);
    } catch (setupError) {
        showFormError('setup-error', setupError.message);
    } finally {
        hideLoading();
    }
});

document.getElementById('login-form').addEventListener('submit', async submitEvent => {
    submitEvent.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    showFormError('login-error', '');
    showLoading('Logging in...');
    try {
        await api.login(username, password);
        showSuccess('Login successful');
        window.setTimeout(() => window.location.assign('/upload.html'), 300);
    } catch (loginError) {
        showFormError('login-error', loginError.message);
    } finally {
        hideLoading();
    }
});

initializeLoginPage().catch(initializationError => {
    showFormError('login-error', initializationError.message);
    document.getElementById('login-form').hidden = false;
});
