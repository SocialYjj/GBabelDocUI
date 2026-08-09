const EDITABLE_SERVICES = new Set(['OpenAI', 'AzureOpenAI', 'GoogleGemini']);
const EDITABLE_TERM_SERVICES = new Set(['same', ...EDITABLE_SERVICES]);

let settingsPageUser = null;
let loadedSettings = {};
let configuredCredentials = new Set();
let settingsLoadCompleted = false;
let loadedUsers = [];
let registrationEnabled = false;

function settingsElement(elementId) {
    return document.getElementById(elementId);
}

function setFieldValue(elementId, value, fallback = '') {
    const field = settingsElement(elementId);
    field.value = value === null || value === undefined ? fallback : value;
}

function setCheckboxValue(elementId, value, fallback = false) {
    settingsElement(elementId).checked = value === null || value === undefined
        ? fallback
        : Boolean(value);
}

function finiteNumber(elementId, minimum, maximum, fieldLabel) {
    const numericValue = Number(settingsElement(elementId).value);
    if (!Number.isFinite(numericValue) || numericValue < minimum || numericValue > maximum) {
        throw new Error(i18n.format('settings.validation.range', {
            field: fieldLabel,
            minimum,
            maximum,
        }));
    }
    return numericValue;
}

function integerValue(elementId, minimum, maximum, fieldLabel) {
    const numericValue = finiteNumber(elementId, minimum, maximum, fieldLabel);
    if (!Number.isInteger(numericValue)) {
        throw new Error(i18n.format('settings.validation.integer', { field: fieldLabel }));
    }
    return numericValue;
}

function optionalCredential(settingsPayload, settingName, elementId) {
    const credentialValue = settingsElement(elementId).value.trim();
    if (credentialValue) {
        settingsPayload[settingName] = credentialValue;
    }
}

function customPageExpression(pageExpression) {
    if (!pageExpression) {
        throw new Error(i18n.t('settings.validation.custom_pages.required'));
    }
    if (pageExpression.length > 200) {
        throw new Error(i18n.t('settings.validation.custom_pages.too_long'));
    }
    const selectedPages = new Set();
    const normalizedSegments = [];
    for (const rawSegment of pageExpression.split(',')) {
        const segment = rawSegment.trim();
        const rangeMatch = segment.match(/^([1-9]\d*)(?:\s*-\s*([1-9]\d*))?$/);
        if (!rangeMatch) {
            throw new Error(i18n.t('settings.validation.custom_pages.invalid'));
        }
        const firstPage = Number(rangeMatch[1]);
        const lastPage = Number(rangeMatch[2] || rangeMatch[1]);
        if (firstPage > lastPage) {
            throw new Error(i18n.t('settings.validation.custom_pages.order'));
        }
        for (let pageNumber = firstPage; pageNumber <= lastPage; pageNumber += 1) {
            if (selectedPages.has(pageNumber)) {
                throw new Error(i18n.t('settings.validation.custom_pages.overlap'));
            }
            selectedPages.add(pageNumber);
        }
        normalizedSegments.push(firstPage === lastPage
            ? String(firstPage)
            : `${firstPage}-${lastPage}`);
    }
    return normalizedSegments.join(',');
}

function basicSettingsPayload() {
    const service = settingsElement('service').value;
    const settingsPayload = {
        service,
        lang_from: settingsElement('lang-from').value,
        lang_to: settingsElement('lang-to').value,
        page_range: settingsElement('page-range').value,
        ignore_cache: settingsElement('ignore-cache').checked,
    };
    if (settingsPayload.page_range === 'custom') {
        settingsPayload.custom_pages = customPageExpression(
            settingsElement('custom-pages').value.trim(),
        );
    }

    if (service === 'OpenAI') {
        Object.assign(settingsPayload, {
            openai_model: settingsElement('openai-model').value.trim(),
            openai_base_url: settingsElement('openai-base-url').value.trim() || null,
            openai_timeout: settingsElement('openai-timeout').value || null,
            openai_temperature: settingsElement('openai-temperature').value || null,
            openai_send_temprature: settingsElement('openai-send-temperature').checked,
            openai_reasoning_effort: settingsElement('openai-reasoning-effort').value || null,
            openai_send_reasoning_effort: settingsElement('openai-send-reasoning-effort').checked,
            openai_enable_json_mode: settingsElement('openai-enable-json-mode').checked,
        });
        optionalCredential(settingsPayload, 'openai_api_key', 'openai-api-key');
    } else if (service === 'AzureOpenAI') {
        Object.assign(settingsPayload, {
            azure_openai_model: settingsElement('azure-openai-model').value.trim(),
            azure_openai_base_url: settingsElement('azure-openai-base-url').value.trim(),
            azure_openai_api_version: settingsElement('azure-openai-api-version').value.trim(),
        });
        optionalCredential(settingsPayload, 'azure_openai_api_key', 'azure-openai-api-key');
    } else if (service === 'GoogleGemini') {
        Object.assign(settingsPayload, {
            gemini_model: settingsElement('gemini-model').value.trim(),
            gemini_enable_json_mode: settingsElement('gemini-enable-json-mode').checked,
        });
        optionalCredential(settingsPayload, 'gemini_api_key', 'gemini-api-key');
    }
    return settingsPayload;
}

function pdfOutputSettingsPayload() {
    return {
        no_mono: settingsElement('no-mono').checked,
        no_dual: settingsElement('no-dual').checked,
        dual_translate_first: settingsElement('dual-translate-first').checked,
        use_alternating_pages: settingsElement('use-alternating-pages').checked,
        watermark_mode: settingsElement('watermark-mode').value,
        only_translated_pages: settingsElement('only-translated-pages').checked,
    };
}

function advancedSettingsPayload() {
    const maximumPagesPerPart = integerValue(
        'max-pages-per-part', 0, 5000, i18n.t('settings.advanced.max_pages'),
    );
    if (maximumPagesPerPart > 0 && maximumPagesPerPart < 50) {
        throw new Error(i18n.t('settings.validation.max_pages.minimum'));
    }
    const settingsPayload = {
        custom_system_prompt: settingsElement('custom-system-prompt').value,
        min_text_length: integerValue(
            'min-text-length', 0, 10000, i18n.t('settings.advanced.min_length'),
        ),
        primary_font: settingsElement('primary-font').value,
        enable_term_extraction: settingsElement('enable-term-extraction').checked,
        save_glossary: settingsElement('save-glossary').checked,
        skip_clean: settingsElement('skip-clean').checked,
        disable_rich_text: settingsElement('disable-rich-text').checked,
        enhance_compatibility: settingsElement('enhance-compatibility').checked,
        split_short_lines: settingsElement('split-short-lines').checked,
        split_factor: finiteNumber(
            'split-factor', 0.1, 1, i18n.t('settings.advanced.split_factor'),
        ),
        translate_tables: settingsElement('translate-tables').checked,
        skip_scanned_detection: settingsElement('skip-scanned-detection').checked,
        ocr_workaround: settingsElement('ocr-workaround').checked,
        auto_ocr: settingsElement('auto-ocr').checked,
        max_pages_per_part: maximumPagesPerPart,
        formula_font_pattern: settingsElement('formula-font-pattern').value,
        formula_char_pattern: settingsElement('formula-char-pattern').value,
    };
    if (settingsPageUser && settingsPageUser.is_admin) {
        settingsPayload.rpc_doclayout = settingsElement('rpc-doclayout').value.trim();
    }
    return settingsPayload;
}

function rateLimitSettingsPayload() {
    const settingsPayload = {
        rate_limit_mode: settingsElement('rate-limit-mode').value,
        term_service: settingsElement('term-service').value,
        term_rate_mode: settingsElement('term-rate-mode').value,
    };
    if (settingsPayload.rate_limit_mode === 'rpm') {
        settingsPayload.rpm = integerValue(
            'rpm-input', 60, 1200, i18n.t('settings.rate.rpm'),
        );
    } else if (settingsPayload.rate_limit_mode === 'concurrent') {
        settingsPayload.concurrent_threads = integerValue(
            'concurrent-threads', 1, 64, i18n.t('settings.rate.concurrent'),
        );
    } else {
        settingsPayload.custom_qps = integerValue(
            'custom-qps', 1, 20, i18n.t('settings.rate.qps'),
        );
        settingsPayload.custom_workers = integerValue(
            'custom-workers', 0, 64, i18n.t('settings.rate.workers'),
        );
    }

    if (settingsPayload.term_rate_mode === 'rpm') {
        settingsPayload.term_rpm = integerValue(
            'term-rpm', 60, 1200, i18n.t('settings.rate.term.rpm'),
        );
    } else if (settingsPayload.term_rate_mode === 'concurrent') {
        settingsPayload.term_concurrent = integerValue(
            'term-concurrent', 1, 64, i18n.t('settings.rate.term.concurrent'),
        );
    } else {
        settingsPayload.term_qps = integerValue(
            'term-qps', 1, 20, i18n.t('settings.rate.term.qps'),
        );
        settingsPayload.term_workers = integerValue(
            'term-workers', 0, 64, i18n.t('settings.rate.term.workers'),
        );
    }
    return settingsPayload;
}

function babeldocSettingsPayload() {
    return {
        merge_line_numbers: settingsElement('merge-line-numbers').checked,
        remove_formula_lines: settingsElement('remove-formula-lines').checked,
        iou_threshold: finiteNumber(
            'iou-threshold', 0, 1, i18n.t('settings.babeldoc.iou_threshold'),
        ),
        protection_threshold: finiteNumber(
            'protection-threshold', 0, 1,
            i18n.t('settings.babeldoc.protection_threshold'),
        ),
        skip_formula_offset: settingsElement('skip-formula-offset').checked,
    };
}

function allSettingsPayload() {
    return {
        ...basicSettingsPayload(),
        ...pdfOutputSettingsPayload(),
        ...advancedSettingsPayload(),
        ...rateLimitSettingsPayload(),
        ...babeldocSettingsPayload(),
    };
}

function setCredentialStatus(settingName, statusElementId) {
    settingsElement(statusElementId).textContent = configuredCredentials.has(settingName)
        ? i18n.t('settings.basic.apikey.status.configured')
        : i18n.t('settings.basic.apikey.status.none');
}

function displayLoadedSettings(settingsPayload) {
    loadedSettings = settingsPayload;
    const rawSavedService = settingsPayload.service || 'OpenAI';
    const savedService = rawSavedService === 'Gemini' ? 'GoogleGemini' : rawSavedService;
    const providerWarning = settingsElement('unsupported-provider-warning');
    if (EDITABLE_SERVICES.has(savedService)) {
        settingsElement('service').value = savedService;
        providerWarning.hidden = true;
    } else {
        settingsElement('service').value = 'OpenAI';
        providerWarning.textContent = i18n.format(
            'settings.message.provider.unsupported',
            { provider: rawSavedService },
        );
        providerWarning.hidden = false;
    }

    setFieldValue('openai-model', settingsPayload.openai_model, 'gpt-4o-mini');
    setFieldValue('openai-base-url', settingsPayload.openai_base_url, '');
    setFieldValue('openai-timeout', settingsPayload.openai_timeout, '60');
    setFieldValue('openai-temperature', settingsPayload.openai_temperature, '0.7');
    setCheckboxValue('openai-send-temperature', settingsPayload.openai_send_temprature);
    setFieldValue('openai-reasoning-effort', settingsPayload.openai_reasoning_effort, '');
    setCheckboxValue('openai-send-reasoning-effort', settingsPayload.openai_send_reasoning_effort);
    setCheckboxValue('openai-enable-json-mode', settingsPayload.openai_enable_json_mode);
    setFieldValue('azure-openai-model', settingsPayload.azure_openai_model, '');
    setFieldValue('azure-openai-base-url', settingsPayload.azure_openai_base_url, '');
    setFieldValue('azure-openai-api-version', settingsPayload.azure_openai_api_version, '2024-06-01');
    setFieldValue('gemini-model', settingsPayload.gemini_model, 'gemini-2.5-flash');
    setCheckboxValue('gemini-enable-json-mode', settingsPayload.gemini_enable_json_mode);
    setCredentialStatus('openai_api_key', 'openai-api-key-status');
    setCredentialStatus('azure_openai_api_key', 'azure-openai-api-key-status');
    setCredentialStatus('gemini_api_key', 'gemini-api-key-status');

    setFieldValue('lang-from', settingsPayload.lang_from, 'auto');
    setFieldValue('lang-to', settingsPayload.lang_to, 'zh');
    setFieldValue('page-range', settingsPayload.page_range, 'all');
    setFieldValue('custom-pages', settingsPayload.custom_pages, '');
    setCheckboxValue('ignore-cache', settingsPayload.ignore_cache);
    setCheckboxValue('no-mono', settingsPayload.no_mono);
    setCheckboxValue('no-dual', settingsPayload.no_dual);
    setCheckboxValue('dual-translate-first', settingsPayload.dual_translate_first);
    setCheckboxValue('use-alternating-pages', settingsPayload.use_alternating_pages);
    setFieldValue('watermark-mode', settingsPayload.watermark_mode, 'watermarked');
    setCheckboxValue('only-translated-pages', settingsPayload.only_translated_pages);
    setFieldValue('custom-system-prompt', settingsPayload.custom_system_prompt, '');
    setFieldValue('min-text-length', settingsPayload.min_text_length, 5);
    setFieldValue('primary-font', settingsPayload.primary_font, 'auto');
    setCheckboxValue('enable-term-extraction', settingsPayload.enable_term_extraction);
    setCheckboxValue('save-glossary', settingsPayload.save_glossary);
    setFieldValue('rpc-doclayout', settingsPayload.rpc_doclayout, '');
    setCheckboxValue('skip-clean', settingsPayload.skip_clean);
    setCheckboxValue('disable-rich-text', settingsPayload.disable_rich_text);
    setCheckboxValue('enhance-compatibility', settingsPayload.enhance_compatibility);
    setCheckboxValue('split-short-lines', settingsPayload.split_short_lines);
    setFieldValue('split-factor', settingsPayload.split_factor, 0.8);
    setCheckboxValue('translate-tables', settingsPayload.translate_tables ?? settingsPayload.translate_table_text, true);
    setCheckboxValue('skip-scanned-detection', settingsPayload.skip_scanned_detection);
    setCheckboxValue('ocr-workaround', settingsPayload.ocr_workaround);
    setCheckboxValue('auto-ocr', settingsPayload.auto_ocr);
    setFieldValue('max-pages-per-part', settingsPayload.max_pages_per_part, 0);
    setFieldValue('formula-font-pattern', settingsPayload.formula_font_pattern, '');
    setFieldValue('formula-char-pattern', settingsPayload.formula_char_pattern, '');
    setFieldValue('rate-limit-mode', settingsPayload.rate_limit_mode, 'rpm');
    setFieldValue('rpm-input', settingsPayload.rpm, 240);
    setFieldValue('concurrent-threads', settingsPayload.concurrent_threads, 40);
    setFieldValue('custom-qps', settingsPayload.custom_qps, 4);
    setFieldValue('custom-workers', settingsPayload.custom_workers, 40);
    const rawTermService = settingsPayload.term_service || 'same';
    const editableTermService = rawTermService === 'Gemini'
        ? 'GoogleGemini'
        : rawTermService;
    setFieldValue('term-service', EDITABLE_TERM_SERVICES.has(editableTermService)
        ? editableTermService
        : 'same', 'same');
    setFieldValue('term-rate-mode', settingsPayload.term_rate_mode, 'rpm');
    setFieldValue('term-rpm', settingsPayload.term_rpm, 240);
    setFieldValue('term-concurrent', settingsPayload.term_concurrent, 40);
    setFieldValue('term-qps', settingsPayload.term_qps, 4);
    setFieldValue('term-workers', settingsPayload.term_workers, 40);
    setCheckboxValue('merge-line-numbers', settingsPayload.merge_line_numbers, true);
    setCheckboxValue('remove-formula-lines', settingsPayload.remove_formula_lines, true);
    setFieldValue('iou-threshold', settingsPayload.iou_threshold, 0.9);
    setFieldValue('protection-threshold', settingsPayload.protection_threshold, 0.9);
    setCheckboxValue('skip-formula-offset', settingsPayload.skip_formula_offset);

    ['service', 'page-range', 'split-short-lines', 'split-factor', 'rate-limit-mode',
        'term-rate-mode', 'iou-threshold', 'protection-threshold'].forEach(elementId => {
        settingsElement(elementId).dispatchEvent(new Event('change'));
        settingsElement(elementId).dispatchEvent(new Event('input'));
    });
}

async function loadSettings() {
    settingsLoadCompleted = false;
    document.querySelectorAll('.settings-save-button').forEach(saveButton => {
        saveButton.disabled = true;
    });
    const settingsResponse = await api.getSettings();
    configuredCredentials = new Set(settingsResponse.configured_credentials || []);
    displayLoadedSettings(settingsResponse.settings || {});
    settingsLoadCompleted = true;
    document.querySelectorAll('.settings-save-button').forEach(saveButton => {
        saveButton.disabled = false;
    });
}

async function saveSettingsPayload(settingsPayload) {
    if (!settingsLoadCompleted) {
        throw new Error(i18n.t('settings.message.loading'));
    }
    await api.updateSettings(settingsPayload);
    showSuccess(i18n.t('settings.message.saved'));
    await loadSettings();
}

async function saveSelectedSection(payloadFactory) {
    try {
        await saveSettingsPayload(payloadFactory());
    } catch (saveError) {
        showError(saveError);
    }
}

function activateSettingsTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(tabButton => {
        const active = tabButton.dataset.tab === tabName;
        tabButton.classList.toggle('active', active);
        tabButton.setAttribute('aria-selected', String(active));
    });
    document.querySelectorAll('.tab-content').forEach(tabPanel => {
        const active = tabPanel.id === `tab-${tabName}`;
        tabPanel.classList.toggle('active', active);
        tabPanel.hidden = !active;
    });
}

function updateProviderPanel() {
    const selectedService = settingsElement('service').value;
    settingsElement('openai-settings').hidden = selectedService !== 'OpenAI';
    settingsElement('azureopenai-settings').hidden = selectedService !== 'AzureOpenAI';
    settingsElement('googlegemini-settings').hidden = selectedService !== 'GoogleGemini';
}

function updateRateLimitFields(prefix = '') {
    const modeElementId = prefix ? `${prefix}-rate-mode` : 'rate-limit-mode';
    const mode = settingsElement(modeElementId).value;
    const groupPrefix = prefix ? `${prefix}-` : '';
    settingsElement(`${groupPrefix}rpm-group`).hidden = mode !== 'rpm';
    settingsElement(`${groupPrefix}concurrent-group`).hidden = mode !== 'concurrent';
    settingsElement(`${groupPrefix}custom${prefix ? '' : '-rate'}-group`).hidden = mode !== 'custom';
}

function createUserRow(userRecord) {
    const userRow = document.createElement('div');
    userRow.className = 'user-list-row';
    const userDescription = document.createElement('div');
    const username = document.createElement('strong');
    username.textContent = userRecord.username;
    userDescription.appendChild(username);
    if (userRecord.is_admin) {
        const adminBadge = document.createElement('span');
        adminBadge.className = 'badge';
        adminBadge.textContent = i18n.t('settings.users.admin');
        userDescription.appendChild(adminBadge);
    }
    const createdAt = document.createElement('small');
    createdAt.className = 'text-muted block';
    createdAt.textContent = i18n.format('settings.users.created', {
        date: formatDate(userRecord.created_at),
    });
    userDescription.appendChild(createdAt);
    userRow.appendChild(userDescription);
    if (!userRecord.is_admin) {
        const deleteButton = document.createElement('button');
        deleteButton.type = 'button';
        deleteButton.className = 'btn btn-danger btn-sm';
        deleteButton.textContent = i18n.t('common.delete');
        deleteButton.addEventListener('click', () => deleteUser(userRecord.username));
        userRow.appendChild(deleteButton);
    }
    return userRow;
}

function renderUsers() {
    const usersList = settingsElement('users-list');
    usersList.replaceChildren();
    for (const userRecord of loadedUsers) {
        usersList.appendChild(createUserRow(userRecord));
    }
}

async function loadUsers() {
    const usersResponse = await api.listUsers();
    loadedUsers = usersResponse.users || [];
    renderUsers();
}

async function deleteUser(username) {
    if (!window.confirm(i18n.format('settings.message.user.delete.confirm', { username }))) {
        return;
    }
    try {
        await api.deleteUser(username);
        showSuccess(i18n.t('settings.message.user.deleted'));
        await loadUsers();
    } catch (deleteError) {
        showError(deleteError);
    }
}

async function loadRegistrationSetting() {
    const registrationResponse = await api.checkRegistrationStatus();
    registrationEnabled = Boolean(registrationResponse.enabled);
    settingsElement('allow-registration').checked = registrationEnabled;
    settingsElement('registration-status').hidden = false;
    settingsElement('registration-status-text').textContent = registrationEnabled
        ? i18n.t('settings.users.registration.enabled')
        : i18n.t('settings.users.registration.disabled');
}

function refreshLocalizedSettingsContent() {
    setCredentialStatus('openai_api_key', 'openai-api-key-status');
    setCredentialStatus('azure_openai_api_key', 'azure-openai-api-key-status');
    setCredentialStatus('gemini_api_key', 'gemini-api-key-status');
    if (loadedUsers.length) {
        renderUsers();
    }
    if (!settingsElement('registration-status').hidden) {
        settingsElement('registration-status-text').textContent = registrationEnabled
            ? i18n.t('settings.users.registration.enabled')
            : i18n.t('settings.users.registration.disabled');
    }
    const rawSavedService = loadedSettings.service || 'OpenAI';
    const normalizedService = rawSavedService === 'Gemini'
        ? 'GoogleGemini'
        : rawSavedService;
    const providerWarning = settingsElement('unsupported-provider-warning');
    if (!EDITABLE_SERVICES.has(normalizedService)) {
        providerWarning.textContent = i18n.format(
            'settings.message.provider.unsupported',
            { provider: rawSavedService },
        );
    }
}

window.addEventListener('i18n:language-changed', refreshLocalizedSettingsContent);

function bindSettingsEvents() {
    document.querySelectorAll('.tab-button').forEach(tabButton => {
        tabButton.addEventListener('click', () => activateSettingsTab(tabButton.dataset.tab));
    });
    settingsElement('service').addEventListener('change', updateProviderPanel);
    settingsElement('page-range').addEventListener('change', () => {
        settingsElement('custom-pages-group').hidden = settingsElement('page-range').value !== 'custom';
    });
    settingsElement('split-short-lines').addEventListener('change', () => {
        settingsElement('split-factor-group').hidden = !settingsElement('split-short-lines').checked;
    });
    settingsElement('split-factor').addEventListener('input', () => {
        settingsElement('split-factor-value').value = settingsElement('split-factor').value;
    });
    settingsElement('iou-threshold').addEventListener('input', () => {
        settingsElement('iou-threshold-value').value = settingsElement('iou-threshold').value;
    });
    settingsElement('protection-threshold').addEventListener('input', () => {
        settingsElement('protection-threshold-value').value = settingsElement('protection-threshold').value;
    });
    settingsElement('rate-limit-mode').addEventListener('change', () => updateRateLimitFields());
    settingsElement('term-rate-mode').addEventListener('change', () => updateRateLimitFields('term'));

    settingsElement('save-basic-btn').addEventListener('click', () => saveSelectedSection(basicSettingsPayload));
    settingsElement('save-pdf-output-btn').addEventListener('click', () => saveSelectedSection(pdfOutputSettingsPayload));
    settingsElement('save-advanced-btn').addEventListener('click', () => saveSelectedSection(advancedSettingsPayload));
    settingsElement('save-rate-limit-btn').addEventListener('click', () => saveSelectedSection(rateLimitSettingsPayload));
    settingsElement('save-babeldoc-btn').addEventListener('click', () => saveSelectedSection(babeldocSettingsPayload));
    settingsElement('save-all-btn').addEventListener('click', () => saveSelectedSection(allSettingsPayload));

    settingsElement('change-password-btn').addEventListener('click', async () => {
        const currentPassword = settingsElement('current-password').value;
        const newPassword = settingsElement('new-password').value;
        const passwordConfirmation = settingsElement('confirm-password').value;
        if (!currentPassword || !newPassword || !passwordConfirmation) {
            showAlert(i18n.t('settings.message.password.required'), 'error');
            return;
        }
        if (newPassword !== passwordConfirmation) {
            showAlert(i18n.t('settings.message.password.mismatch'), 'error');
            return;
        }
        try {
            await api.changePassword(currentPassword, newPassword);
            window.location.assign('/login.html?password_changed=1');
        } catch (passwordError) {
            showError(passwordError);
        }
    });

    settingsElement('export-config-btn').addEventListener('click', () => api.exportSettings());
    settingsElement('import-config-btn').addEventListener('click', () => settingsElement('import-config-file').click());
    settingsElement('import-config-file').addEventListener('change', async changeEvent => {
        const settingsFile = changeEvent.target.files[0];
        if (!settingsFile) {
            return;
        }
        try {
            showLoading(i18n.t('settings.message.importing'));
            const importResponse = await api.importSettings(settingsFile);
            showSuccess(i18n.format('settings.message.imported_count', {
                count: importResponse.imported_count,
            }));
            await loadSettings();
        } catch (importError) {
            showError(importError);
        } finally {
            hideLoading();
            changeEvent.target.value = '';
        }
    });

    settingsElement('reset-btn').addEventListener('click', async () => {
        if (!window.confirm(i18n.t('settings.message.reset.confirm'))) {
            return;
        }
        try {
            await api.resetSettings();
            showSuccess(i18n.t('settings.message.reset'));
            await loadSettings();
        } catch (resetError) {
            showError(resetError);
        }
    });
    settingsElement('save-registration-btn').addEventListener('click', async () => {
        try {
            await api.toggleRegistration(settingsElement('allow-registration').checked);
            showSuccess(i18n.t('settings.message.registration.saved'));
            await loadRegistrationSetting();
        } catch (registrationError) {
            showError(registrationError);
        }
    });
    settingsElement('add-user-btn').addEventListener('click', async () => {
        const username = settingsElement('new-user-username').value.trim();
        const password = settingsElement('new-user-password').value;
        if (!username || !password) {
            showAlert(i18n.t('settings.message.user.enter'), 'error');
            return;
        }
        try {
            await api.register(username, password);
            settingsElement('new-user-username').value = '';
            settingsElement('new-user-password').value = '';
            showSuccess(i18n.t('settings.message.user.added'));
            await loadUsers();
        } catch (userCreationError) {
            showError(userCreationError);
        }
    });
}

async function initializeSettingsPage() {
    bindSettingsEvents();
    if (!(await requireAuth())) {
        return;
    }
    settingsPageUser = await updateUserInfo();
    settingsElement('current-username').value = settingsPageUser.username;
    updateAdminUI();
    if (settingsPageUser.is_admin) {
        settingsElement('user-mgmt-tab').hidden = false;
        await Promise.all([loadUsers(), loadRegistrationSetting()]);
    }
    const authStatus = await api.checkAuthStatus();
    if (authStatus.version) {
        settingsElement('app-version-footer').textContent = `GBabelDocUI v${authStatus.version}`;
    }
    await loadSettings();
}

initializeSettingsPage().catch(initializationError => {
    showError(initializationError);
});
