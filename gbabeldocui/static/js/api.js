/**
 * Same-origin API client for GBabelDocUI.
 * Authentication is carried only by the HttpOnly session cookie.
 */

const API_BASE_URL = window.location.origin;
const CSRF_COOKIE_NAME = 'gbabeldocui_csrf';
const CSRF_HEADER_NAME = 'X-CSRF-Token';
const DEFAULT_REQUEST_TIMEOUT_MS = 30000;
const DEFAULT_UPLOAD_TIMEOUT_MS = 10 * 60 * 1000;

class APIClient {
  getCookie(cookieName) {
    const encodedName = `${encodeURIComponent(cookieName)}=`;
    const cookieParts = document.cookie ? document.cookie.split(';') : [];
    for (const rawCookiePart of cookieParts) {
      const cookiePart = rawCookiePart.trim();
      if (cookiePart.startsWith(encodedName)) {
        return decodeURIComponent(cookiePart.slice(encodedName.length));
      }
    }
    return '';
  }

  csrfToken() {
    return this.getCookie(CSRF_COOKIE_NAME);
  }

  isMutatingMethod(method) {
    return ['POST', 'PUT', 'PATCH', 'DELETE'].includes(String(method).toUpperCase());
  }

  requestHeaders(method, body, additionalHeaders = {}) {
    const requestHeaders = { ...additionalHeaders };
    if (body !== undefined && body !== null && !(body instanceof FormData)
      && !Object.keys(requestHeaders).some(name => name.toLowerCase() === 'content-type')) {
      requestHeaders['Content-Type'] = 'application/json';
    }
    if (this.isMutatingMethod(method)) {
      const csrfToken = this.csrfToken();
      if (!csrfToken) {
        throw new Error('请求验证信息尚未初始化，请刷新页面后重试');
      }
      requestHeaders[CSRF_HEADER_NAME] = csrfToken;
    }
    return requestHeaders;
  }

  createAbortController(externalSignal, timeoutMs) {
    const requestController = new AbortController();
    let externalAbortListener = null;
    if (externalSignal) {
      if (externalSignal.aborted) {
        requestController.abort(externalSignal.reason);
      } else {
        externalAbortListener = () => requestController.abort(externalSignal.reason);
        externalSignal.addEventListener('abort', externalAbortListener, { once: true });
      }
    }
    const timeoutIdentifier = window.setTimeout(() => {
      requestController.abort(new DOMException('Request timed out', 'TimeoutError'));
    }, timeoutMs);
    return {
      requestController,
      cleanup: () => {
        window.clearTimeout(timeoutIdentifier);
        if (externalSignal && externalAbortListener) {
          externalSignal.removeEventListener('abort', externalAbortListener);
        }
      },
    };
  }

  async request(endpoint, options = {}) {
    const requestMethod = String(options.method || 'GET').toUpperCase();
    const timeoutMs = Number.isFinite(options.timeoutMs)
      ? Math.max(1, options.timeoutMs)
      : DEFAULT_REQUEST_TIMEOUT_MS;
    const { requestController, cleanup } = this.createAbortController(
      options.signal,
      timeoutMs,
    );
    const requestOptions = {
      ...options,
      method: requestMethod,
      credentials: 'same-origin',
      signal: requestController.signal,
      headers: this.requestHeaders(requestMethod, options.body, options.headers),
    };
    delete requestOptions.timeoutMs;

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, requestOptions);
      if (this.handleUnauthorized(response)) {
        throw new Error('登录状态已失效');
      }
      const responsePayload = await this.parseResponseBody(response);
      if (!response.ok) {
        const requestError = new Error(
          this.responseErrorMessage(responsePayload, '请求失败'),
        );
        requestError.status = response.status;
        throw requestError;
      }
      return responsePayload;
    } catch (requestError) {
      if (requestError && requestError.name === 'AbortError') {
        throw new Error('请求已取消');
      }
      if (requestError && requestError.name === 'TimeoutError') {
        throw new Error('请求超时');
      }
      throw requestError;
    } finally {
      cleanup();
    }
  }

  handleUnauthorized(response) {
    if (response.status !== 401) {
      return false;
    }
    window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    const publicPages = ['/login.html', '/register.html'];
    if (!publicPages.some(page => window.location.pathname.endsWith(page))) {
      window.location.assign('/login.html');
    }
    return true;
  }

  async parseResponseBody(response) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        return await response.json();
      } catch (_parseError) {
        return { detail: '服务器返回了无效响应' };
      }
    }
    return { detail: await response.text() };
  }

  responseErrorMessage(responsePayload, fallbackMessage) {
    if (responsePayload && typeof responsePayload.detail === 'string'
      && responsePayload.detail.trim()) {
      return responsePayload.detail;
    }
    if (responsePayload && typeof responsePayload.message === 'string'
      && responsePayload.message.trim()) {
      return responsePayload.message;
    }
    return fallbackMessage;
  }

  checkAuthStatus() {
    return this.request('/api/auth/status');
  }

  getCurrentUser() {
    return this.request('/api/auth/me');
  }

  setup(username, password, setupToken = '') {
    return this.request('/api/auth/setup', {
      method: 'POST',
      body: JSON.stringify({
        username,
        password,
        setup_token: setupToken || null,
      }),
    });
  }

  login(username, password) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async logout() {
    await this.request('/api/auth/logout', { method: 'POST' });
  }

  register(username, password) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  listUsers() {
    return this.request('/api/auth/users');
  }

  deleteUser(username) {
    return this.request(`/api/auth/users/${encodeURIComponent(username)}`, {
      method: 'DELETE',
    });
  }

  checkRegistrationStatus() {
    return this.request('/api/auth/registration-status');
  }

  toggleRegistration(enabled) {
    return this.request('/api/auth/registration-toggle', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    });
  }

  registerPublic(username, password) {
    return this.request('/api/auth/register/public', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  getSettings() {
    return this.request('/api/settings');
  }

  updateSettings(settingsPayload) {
    return this.request('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settingsPayload),
    });
  }

  changePassword(oldPassword, newPassword) {
    return this.request('/api/settings/password', {
      method: 'POST',
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword,
      }),
    });
  }

  resetSettings() {
    return this.request('/api/settings/reset', { method: 'POST' });
  }

  exportSettings() {
    const downloadLink = document.createElement('a');
    downloadLink.href = `${API_BASE_URL}/api/settings/export`;
    downloadLink.hidden = true;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    downloadLink.remove();
    return Promise.resolve({ success: true });
  }

  importSettings(settingsFile, options = {}) {
    const importBody = new FormData();
    importBody.append('file', settingsFile);
    return this.request('/api/settings/import', {
      method: 'POST',
      body: importBody,
      signal: options.signal,
      timeoutMs: options.timeoutMs || DEFAULT_REQUEST_TIMEOUT_MS,
    });
  }

  uploadFile(pdfFile, onProgress, options = {}) {
    const uploadBody = new FormData();
    uploadBody.append('file', pdfFile);
    const uploadRequest = new XMLHttpRequest();
    const timeoutMs = Number.isFinite(options.timeoutMs)
      ? Math.max(1, options.timeoutMs)
      : DEFAULT_UPLOAD_TIMEOUT_MS;

    return new Promise((resolve, reject) => {
      let settled = false;
      const finish = (callback) => {
        if (settled) {
          return;
        }
        settled = true;
        if (options.signal) {
          options.signal.removeEventListener('abort', abortUpload);
        }
        callback();
      };
      const abortUpload = () => uploadRequest.abort();

      uploadRequest.upload.addEventListener('progress', uploadEvent => {
        if (uploadEvent.lengthComputable && typeof onProgress === 'function') {
          onProgress((uploadEvent.loaded / uploadEvent.total) * 100);
        }
      });
      uploadRequest.addEventListener('load', () => {
        if (uploadRequest.status === 401) {
          this.handleUnauthorized({ status: 401 });
          finish(() => reject(new Error('登录状态已失效')));
          return;
        }
        let responsePayload = {};
        try {
          responsePayload = JSON.parse(uploadRequest.responseText || '{}');
        } catch (_parseError) {
          finish(() => reject(new Error('服务器返回了无效响应')));
          return;
        }
        if (uploadRequest.status >= 200 && uploadRequest.status < 300) {
          finish(() => resolve(responsePayload));
          return;
        }
        finish(() => reject(new Error(
          this.responseErrorMessage(responsePayload, '上传失败'),
        )));
      });
      uploadRequest.addEventListener('error', () => {
        finish(() => reject(new Error('上传失败')));
      });
      uploadRequest.addEventListener('timeout', () => {
        finish(() => reject(new Error('上传超时')));
      });
      uploadRequest.addEventListener('abort', () => {
        finish(() => reject(new Error('上传已取消')));
      });

      if (options.signal) {
        if (options.signal.aborted) {
          reject(new Error('上传已取消'));
          return;
        }
        options.signal.addEventListener('abort', abortUpload, { once: true });
      }

      uploadRequest.open('POST', `${API_BASE_URL}/api/upload`);
      uploadRequest.withCredentials = true;
      uploadRequest.timeout = timeoutMs;
      const csrfToken = this.csrfToken();
      if (!csrfToken) {
        finish(() => reject(new Error('请求验证信息尚未初始化，请刷新页面后重试')));
        return;
      }
      uploadRequest.setRequestHeader(CSRF_HEADER_NAME, csrfToken);
      uploadRequest.send(uploadBody);
    });
  }

  startTranslation(fileId, translationSettings, options = {}) {
    const translationBody = new FormData();
    translationBody.append('file_id', fileId);
    translationBody.append('settings', JSON.stringify(translationSettings));
    return this.request('/api/translate', {
      method: 'POST',
      body: translationBody,
      signal: options.signal,
      timeoutMs: options.timeoutMs || DEFAULT_REQUEST_TIMEOUT_MS,
    });
  }

  getTranslationStatus(taskId, options = {}) {
    return this.request(`/api/translate/status/${encodeURIComponent(taskId)}`, options);
  }

  getTranslationHistory(limit = 50, offset = 0, options = {}) {
    const query = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    return this.request(`/api/translate/history?${query}`, options);
  }

  getDownloadUrl(taskId, fileType = 'mono') {
    const query = new URLSearchParams({ file_type: fileType });
    return `${API_BASE_URL}/api/translate/download/${encodeURIComponent(taskId)}?${query}`;
  }

  deleteHistoryItem(taskId) {
    return this.request(`/api/translate/history/${encodeURIComponent(taskId)}`, {
      method: 'DELETE',
    });
  }

  deleteUploadedFile(fileId) {
    return this.request(`/api/upload/${encodeURIComponent(fileId)}`, {
      method: 'DELETE',
    });
  }
}

const api = new APIClient();
