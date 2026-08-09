const HISTORY_PAGE_SIZE = 20;
const TERMINAL_TASK_STATUSES = new Set(['completed', 'failed', 'cancelled']);

let selectedPdfFile = null;
let currentTaskId = null;
let translationStartInProgress = false;
let pageSelectionReady = false;
let historyOffset = 0;
let historyTotal = 0;
let loadedHistoryItems = [];
let pollingGeneration = 0;
let pollingController = null;
let pollingDelayIdentifier = null;
let historyGeneration = 0;
let historyController = null;
let uploadController = null;

function element(elementId) {
    return document.getElementById(elementId);
}

function setHidden(elementId, hidden) {
    element(elementId).hidden = hidden;
}

function setProgress(progress, message, detail = '') {
    const boundedProgress = Math.max(0, Math.min(100, Number(progress) || 0));
    element('progress-fill').style.width = `${boundedProgress}%`;
    element('progress-bar').setAttribute('aria-valuenow', String(Math.round(boundedProgress)));
    element('progress-text').textContent = message;
    element('progress-detail').textContent = detail;
}

function stopStatusPolling() {
    pollingGeneration += 1;
    if (pollingController) {
        pollingController.abort();
        pollingController = null;
    }
    if (pollingDelayIdentifier) {
        window.clearTimeout(pollingDelayIdentifier);
        pollingDelayIdentifier = null;
    }
}

function waitForNextPoll(generation) {
    return new Promise(resolve => {
        pollingDelayIdentifier = window.setTimeout(() => {
            pollingDelayIdentifier = null;
            resolve(generation === pollingGeneration);
        }, 2000);
    });
}

function normalizeCustomPages(pageExpression, pageCount = null) {
    if (typeof pageExpression !== 'string' || pageExpression.length > 200) {
        throw new Error(i18n.t('upload.error.page_range.invalid'));
    }
    const selectedPages = new Set();
    const normalizedSegments = [];
    for (const rawSegment of pageExpression.split(',')) {
        const segment = rawSegment.trim();
        const rangeMatch = segment.match(/^([1-9]\d*)(?:\s*-\s*([1-9]\d*))?$/);
        if (!rangeMatch) {
            throw new Error(i18n.t('upload.error.page_range.invalid'));
        }
        const firstPage = Number(rangeMatch[1]);
        const lastPage = Number(rangeMatch[2] || rangeMatch[1]);
        if (firstPage > lastPage) {
            throw new Error(i18n.t('upload.error.page_range.order'));
        }
        if (pageCount !== null && lastPage > pageCount) {
            throw new Error(i18n.format('upload.error.page_range.out_of_bounds', {
                count: pageCount,
            }));
        }
        for (let pageNumber = firstPage; pageNumber <= lastPage; pageNumber += 1) {
            if (selectedPages.has(pageNumber)) {
                throw new Error(i18n.t('upload.error.page_range.overlap'));
            }
            selectedPages.add(pageNumber);
        }
        normalizedSegments.push(firstPage === lastPage
            ? String(firstPage)
            : `${firstPage}-${lastPage}`);
    }
    if (!normalizedSegments.length) {
        throw new Error(i18n.t('upload.error.page_range.required'));
    }
    return normalizedSegments.join(',');
}

function selectedPageExpression(pageCount = null) {
    const pageSelection = element('page-range-select').value;
    if (pageSelection === 'all') {
        return 'all';
    }
    if (pageSelection === 'first') {
        return '1';
    }
    if (pageSelection === 'first5') {
        if (pageCount === null || pageCount >= 5) {
            return '1-5';
        }
        return pageCount === 1 ? '1' : `1-${pageCount}`;
    }
    return normalizeCustomPages(element('custom-pages-input').value.trim(), pageCount);
}

function isPdfFile(candidateFile) {
    return Boolean(candidateFile) && (
        candidateFile.type === 'application/pdf'
        || candidateFile.name.toLowerCase().endsWith('.pdf')
    );
}

function selectPdfFile(candidateFile) {
    if (!isPdfFile(candidateFile)) {
        showAlert(i18n.t('upload.error.invalid_file'), 'error');
        return;
    }
    selectedPdfFile = candidateFile;
    element('translate-btn').disabled = !pageSelectionReady;
    element('upload-zone').querySelector('.upload-text').textContent = candidateFile.name;
    element('select-file-btn').textContent = i18n.t('upload.change.button');
    element('upload-hint').textContent = `${formatFileSize(candidateFile.size)} - ${i18n.t('upload.change')}`;
}

function resetTranslationForm() {
    stopStatusPolling();
    if (uploadController) {
        uploadController.abort();
        uploadController = null;
    }
    selectedPdfFile = null;
    currentTaskId = null;
    translationStartInProgress = false;
    element('file-input').value = '';
    element('translate-btn').disabled = true;
    setHidden('cancel-upload-btn', true);
    setHidden('result-card', true);
    setHidden('progress-card', true);
    setHidden('download-mono-btn', true);
    setHidden('download-dual-btn', true);
    element('upload-zone').querySelector('.upload-text').textContent = i18n.t('upload.drag');
    element('select-file-btn').textContent = i18n.t('upload.select');
    element('upload-hint').textContent = i18n.t('upload.select.help');
}

function startDownload(fileType, taskId) {
    if (!taskId) {
        showAlert(i18n.t('upload.error.missing_task'), 'error');
        return;
    }
    const downloadLink = document.createElement('a');
    downloadLink.href = api.getDownloadUrl(taskId, fileType);
    downloadLink.hidden = true;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    downloadLink.remove();
}

function showTranslationOutput(taskStatus, taskId) {
    setHidden('progress-card', true);
    setHidden('result-card', false);
    const outputFiles = taskStatus.output_files || {};
    const monoButton = element('download-mono-btn');
    const dualButton = element('download-dual-btn');
    monoButton.hidden = !outputFiles.mono;
    dualButton.hidden = !outputFiles.dual;
    monoButton.onclick = outputFiles.mono ? () => startDownload('mono', taskId) : null;
    dualButton.onclick = outputFiles.dual ? () => startDownload('dual', taskId) : null;
}

function showActiveTaskProgress() {
    setProgress(0, i18n.t('upload.progress.processing'));
    setHidden('progress-card', false);
    setHidden('result-card', true);
}

function updateCurrentTaskStatus(taskStatus, taskId, pendingTaskIds) {
    if (taskId !== currentTaskId) {
        return;
    }
    setProgress(
        taskStatus.progress,
        taskStatus.message || taskStatus.status || i18n.t('upload.progress.processing'),
        taskStatus.detail || '',
    );
    if (!TERMINAL_TASK_STATUSES.has(taskStatus.status)) {
        return;
    }
    if (taskStatus.status === 'completed') {
        showTranslationOutput(taskStatus, taskId);
    } else if (taskStatus.status === 'failed') {
        showAlert(
            taskStatus.error || taskStatus.message || i18n.t('upload.error.failed'),
            'error',
        );
        setHidden('progress-card', true);
    } else {
        setHidden('progress-card', true);
    }
    currentTaskId = [...pendingTaskIds][0] || null;
    if (currentTaskId) {
        showActiveTaskProgress();
    } else {
        element('translate-btn').disabled = !selectedPdfFile || !pageSelectionReady;
    }
}

async function startStatusPolling(taskIds) {
    stopStatusPolling();
    const generation = pollingGeneration;
    const pendingTaskIds = new Set(taskIds.filter(Boolean));
    const failureCounts = new Map();

    while (generation === pollingGeneration && pendingTaskIds.size) {
        pollingController = new AbortController();
        for (const taskId of [...pendingTaskIds]) {
            if (generation !== pollingGeneration) {
                return;
            }
            try {
                const statusResponse = await api.getTranslationStatus(taskId, {
                    signal: pollingController.signal,
                });
                const taskStatus = statusResponse.task || statusResponse;
                failureCounts.delete(taskId);
                if (TERMINAL_TASK_STATUSES.has(taskStatus.status)) {
                    pendingTaskIds.delete(taskId);
                }
                updateCurrentTaskStatus(taskStatus, taskId, pendingTaskIds);
            } catch (statusError) {
                if (generation !== pollingGeneration || statusError.message === '请求已取消') {
                    return;
                }
                if (statusError.status === 404) {
                    pendingTaskIds.delete(taskId);
                    continue;
                }
                const failureCount = (failureCounts.get(taskId) || 0) + 1;
                failureCounts.set(taskId, failureCount);
                if (failureCount >= 5) {
                    showAlert(statusError.message || i18n.t('upload.error.status'), 'error');
                    failureCounts.set(taskId, 0);
                }
            }
        }
        if (generation === pollingGeneration) {
            await loadHistory(historyOffset, false);
        }
        if (pendingTaskIds.size && !(await waitForNextPoll(generation))) {
            return;
        }
    }
}

function historyStatusColor(taskStatus) {
    if (taskStatus === 'completed') {
        return 'var(--accent-success)';
    }
    if (taskStatus === 'failed' || taskStatus === 'cancelled') {
        return 'var(--accent-error)';
    }
    return 'var(--accent-warning)';
}

function createHistoryAction(buttonClass, label, buttonText, action) {
    const actionButton = document.createElement('button');
    actionButton.className = `btn-icon ${buttonClass}`;
    actionButton.type = 'button';
    actionButton.title = label;
    actionButton.setAttribute('aria-label', label);
    actionButton.textContent = buttonText;
    actionButton.addEventListener('click', action);
    return actionButton;
}

function historyDisplayName(historyItem) {
    const rawDisplayName = String(
        historyItem.original_filename || historyItem.filename || '',
    ).trim();
    const displayName = rawDisplayName.replace(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_/i,
        '',
    ).replace(/_+/g, ' ').trim();
    return displayName && displayName !== '_'
        ? displayName
        : i18n.t('upload.filename.untitled');
}

function historyStatusLabel(taskStatus) {
    const translationKey = `upload.history.status.${taskStatus}`;
    const translatedStatus = i18n.t(translationKey);
    return translatedStatus === translationKey ? taskStatus : translatedStatus;
}

function renderHistoryItem(historyItem) {
    const historyRow = document.createElement('article');
    historyRow.className = 'history-item';

    const statusBar = document.createElement('div');
    statusBar.className = 'history-status-bar';
    statusBar.style.backgroundColor = historyStatusColor(historyItem.status);
    statusBar.setAttribute('aria-hidden', 'true');

    const historyContent = document.createElement('div');
    historyContent.className = 'history-item-content';
    const filenameContainer = document.createElement('div');
    filenameContainer.className = 'history-filename';
    filenameContainer.textContent = historyDisplayName(historyItem);
    filenameContainer.title = historyItem.original_filename
        || historyItem.filename
        || filenameContainer.textContent;

    const statusText = document.createElement('div');
    statusText.className = 'history-status';
    statusText.textContent = historyStatusLabel(historyItem.status);

    const historyActions = document.createElement('div');
    historyActions.className = 'history-actions';
    if (historyItem.status === 'completed' && historyItem.mono_path) {
        historyActions.appendChild(createHistoryAction(
            'btn-icon-primary',
            i18n.t('upload.result.mono'),
            '↓',
            () => startDownload('mono', historyItem.task_id),
        ));
    }
    if (historyItem.status === 'completed' && historyItem.dual_path) {
        historyActions.appendChild(createHistoryAction(
            'btn-icon-secondary',
            i18n.t('upload.result.dual'),
            '⇄',
            () => startDownload('dual', historyItem.task_id),
        ));
    }
    historyActions.appendChild(createHistoryAction(
        'btn-icon-danger',
        i18n.t('common.delete'),
        '×',
        () => deleteHistoryItem(historyItem.task_id),
    ));

    const timestamp = document.createElement('time');
    timestamp.className = 'history-timestamp';
    timestamp.textContent = formatDate(historyItem.created_at);
    if (historyItem.created_at) {
        timestamp.dateTime = historyItem.created_at;
    }

    const historyDetails = document.createElement('div');
    historyDetails.className = 'history-details';
    const historyMeta = document.createElement('div');
    historyMeta.className = 'history-meta';
    historyMeta.append(statusText, timestamp);
    historyDetails.append(filenameContainer, historyMeta);
    historyContent.append(historyDetails, historyActions);
    historyRow.append(statusBar, historyContent);
    return historyRow;
}

function renderHistoryList() {
    const historyList = element('history-list');
    historyList.replaceChildren();
    if (!loadedHistoryItems.length) {
        const emptyMessage = document.createElement('p');
        emptyMessage.className = 'history-empty text-center text-muted';
        emptyMessage.textContent = i18n.t('upload.history.empty');
        historyList.appendChild(emptyMessage);
        return;
    }
    loadedHistoryItems.forEach(historyItem => {
        historyList.appendChild(renderHistoryItem(historyItem));
    });
}

function updateHistoryPagination() {
    const pagination = element('history-pagination');
    pagination.hidden = historyTotal <= HISTORY_PAGE_SIZE;
    const currentPage = Math.floor(historyOffset / HISTORY_PAGE_SIZE) + 1;
    const pageCount = Math.max(1, Math.ceil(historyTotal / HISTORY_PAGE_SIZE));
    element('history-page-status').textContent = `${currentPage} / ${pageCount}`;
    element('history-previous-btn').disabled = historyOffset === 0;
    element('history-next-btn').disabled = historyOffset + HISTORY_PAGE_SIZE >= historyTotal;
}

async function loadHistory(offset = historyOffset, restartPolling = true) {
    const generation = ++historyGeneration;
    if (historyController) {
        historyController.abort();
    }
    historyController = new AbortController();
    try {
        const historyResponse = await api.getTranslationHistory(
            HISTORY_PAGE_SIZE,
            offset,
            { signal: historyController.signal },
        );
        if (generation !== historyGeneration) {
            return;
        }
        historyOffset = offset;
        historyTotal = Number(historyResponse.total) || 0;
        loadedHistoryItems = Array.isArray(historyResponse.history)
            ? historyResponse.history
            : [];
        renderHistoryList();
        updateHistoryPagination();

        if (restartPolling) {
            const activeTaskIds = loadedHistoryItems
                .filter(historyItem => ['queued', 'processing'].includes(historyItem.status))
                .map(historyItem => historyItem.task_id);
            if (activeTaskIds.length) {
                if (!currentTaskId || !activeTaskIds.includes(currentTaskId)) {
                    currentTaskId = activeTaskIds[0];
                }
                showActiveTaskProgress();
                startStatusPolling(activeTaskIds);
            }
        }
    } catch (historyError) {
        if (generation === historyGeneration && historyError.message !== '请求已取消') {
            showAlert(historyError.message || i18n.t('upload.error.history'), 'error');
        }
    }
}

async function deleteHistoryItem(taskId) {
    if (!window.confirm(i18n.t('upload.history.delete.confirm'))) {
        return;
    }
    try {
        await api.deleteHistoryItem(taskId);
        if (taskId === currentTaskId) {
            currentTaskId = null;
            stopStatusPolling();
            setHidden('progress-card', true);
            setHidden('result-card', true);
        }
        showSuccess(i18n.t('upload.history.delete.success'));
        const nextOffset = historyOffset >= historyTotal - 1
            ? Math.max(0, historyOffset - HISTORY_PAGE_SIZE)
            : historyOffset;
        await loadHistory(nextOffset);
    } catch (deleteError) {
        showAlert(`${i18n.t('upload.history.delete.failed')}${deleteError.message}`, 'error');
    }
}

async function loadSavedPageSelection() {
    try {
        const settingsResponse = await api.getSettings();
        const savedSettings = settingsResponse.settings || {};
        const savedPageRange = ['all', 'first', 'first5', 'custom'].includes(savedSettings.page_range)
            ? savedSettings.page_range
            : 'all';
        element('page-range-select').value = savedPageRange;
        element('custom-pages-input').value = typeof savedSettings.custom_pages === 'string'
            ? savedSettings.custom_pages
            : '';
        element('page-range-select').dispatchEvent(new Event('change'));
    } catch (_settingsError) {
        element('page-range-select').value = 'all';
    }
}

async function startTranslation() {
    if (translationStartInProgress) {
        return;
    }
    translationStartInProgress = true;
    element('translate-btn').disabled = true;
    let uploadedFileId = null;
    try {
        if (!selectedPdfFile) {
            throw new Error(i18n.t('upload.error.invalid_file'));
        }
        selectedPageExpression();
        uploadController = new AbortController();
        setHidden('cancel-upload-btn', false);
        setHidden('progress-card', false);
        setProgress(0, i18n.t('upload.progress.uploading'));
        const uploadResponse = await api.uploadFile(
            selectedPdfFile,
            uploadProgress => setProgress(
                uploadProgress,
                i18n.t('upload.progress.uploading'),
            ),
            { signal: uploadController.signal },
        );
        uploadedFileId = uploadResponse.file_id;
        const pages = selectedPageExpression(uploadResponse.page_count);
        setProgress(0, i18n.t('upload.progress.starting'));
        const startResponse = await api.startTranslation(uploadedFileId, { pages });
        currentTaskId = startResponse.task_id;
        showActiveTaskProgress();
        startStatusPolling([currentTaskId]);
        await loadHistory(0, false);
    } catch (startError) {
        if (uploadedFileId && !currentTaskId) {
            try {
                await api.deleteUploadedFile(uploadedFileId);
            } catch (_cleanupError) {
                // The server also performs orphan cleanup; do not hide the original error.
            }
        }
        setHidden('progress-card', true);
        showAlert(startError.message || i18n.t('upload.error.start'), 'error');
    } finally {
        uploadController = null;
        setHidden('cancel-upload-btn', true);
        translationStartInProgress = false;
        if (!currentTaskId) {
            element('translate-btn').disabled = !selectedPdfFile || !pageSelectionReady;
        }
    }
}

function bindPageEvents() {
    const uploadZone = element('upload-zone');
    const fileInput = element('file-input');
    const selectFileButton = element('select-file-btn');
    const openFilePicker = () => {
        fileInput.value = '';
        fileInput.click();
    };
    const uploadNavigationLink = element('upload-nav-link');
    if (uploadNavigationLink) {
        uploadNavigationLink.addEventListener('click', clickEvent => {
            if (window.location.pathname.endsWith('upload.html')) {
                clickEvent.preventDefault();
                openFilePicker();
            }
        });
    }
    uploadZone.addEventListener('click', clickEvent => {
        if (!clickEvent.target.closest('#select-file-btn')) {
            openFilePicker();
        }
    });
    selectFileButton.addEventListener('click', clickEvent => {
        clickEvent.stopPropagation();
        openFilePicker();
    });
    uploadZone.addEventListener('dragover', dragEvent => {
        dragEvent.preventDefault();
        uploadZone.classList.add('drag-over');
    });
    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
    uploadZone.addEventListener('drop', dropEvent => {
        dropEvent.preventDefault();
        uploadZone.classList.remove('drag-over');
        selectPdfFile(dropEvent.dataTransfer.files[0]);
    });
    fileInput.addEventListener('change', changeEvent => {
        if (changeEvent.target.files.length) {
            selectPdfFile(changeEvent.target.files[0]);
        }
    });
    element('page-range-select').addEventListener('change', changeEvent => {
        element('custom-pages-group').hidden = changeEvent.target.value !== 'custom';
    });
    element('translate-btn').addEventListener('click', startTranslation);
    element('cancel-upload-btn').addEventListener('click', () => {
        if (uploadController) {
            uploadController.abort();
        }
    });
    element('new-translation-btn').addEventListener('click', resetTranslationForm);
    element('history-previous-btn').addEventListener('click', () => {
        loadHistory(Math.max(0, historyOffset - HISTORY_PAGE_SIZE));
    });
    element('history-next-btn').addEventListener('click', () => {
        if (historyOffset + HISTORY_PAGE_SIZE < historyTotal) {
            loadHistory(historyOffset + HISTORY_PAGE_SIZE);
        }
    });
}

function refreshLocalizedUploadContent() {
    if (selectedPdfFile) {
        element('select-file-btn').textContent = i18n.t('upload.change.button');
        element('upload-hint').textContent = `${formatFileSize(selectedPdfFile.size)} - ${i18n.t('upload.change')}`;
    }
    renderHistoryList();
}

window.addEventListener('i18n:language-changed', refreshLocalizedUploadContent);

async function initializeUploadPage() {
    bindPageEvents();
    if (!(await requireAuth())) {
        return;
    }
    await updateUserInfo();
    const statusResponse = await api.checkAuthStatus();
    if (statusResponse.version) {
        element('app-version-footer').textContent = `GBabelDocUI v${statusResponse.version}`;
    }
    await loadSavedPageSelection();
    pageSelectionReady = true;
    element('translate-btn').disabled = !selectedPdfFile;
    await loadHistory(0);
}

window.addEventListener('beforeunload', () => {
    stopStatusPolling();
    if (historyController) {
        historyController.abort();
    }
    if (uploadController) {
        uploadController.abort();
    }
});

initializeUploadPage().catch(initializationError => {
    showError(initializationError);
});
