function showRegistrationError(message) {
    const errorElement = document.getElementById('register-error');
    errorElement.textContent = message;
    errorElement.hidden = !message;
}

async function initializeRegistrationPage() {
    if (await redirectIfAuthenticated()) {
        return;
    }
    const registrationStatus = await api.checkRegistrationStatus();
    document.getElementById('register-form').hidden = !registrationStatus.enabled;
    document.getElementById('disabled-message').hidden = Boolean(registrationStatus.enabled);
}

document.getElementById('register-form').addEventListener('submit', async submitEvent => {
    submitEvent.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const passwordConfirmation = document.getElementById('password-confirm').value;
    if (password !== passwordConfirmation) {
        showRegistrationError(i18n.t('register.error.mismatch'));
        return;
    }

    showRegistrationError('');
    showLoading('Creating account...');
    try {
        await api.registerPublic(username, password);
        showSuccess(i18n.t('register.success'));
        window.setTimeout(() => window.location.assign('/upload.html'), 500);
    } catch (registrationError) {
        showRegistrationError(registrationError.message);
    } finally {
        hideLoading();
    }
});

initializeRegistrationPage().catch(initializationError => {
    document.getElementById('register-form').hidden = true;
    document.getElementById('disabled-message').hidden = false;
    showRegistrationError(initializationError.message);
});
