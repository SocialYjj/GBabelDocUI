/**
 * API Client for PDFMathTranslate Web UI
 * Handles all HTTP requests to the backend API
 */

const API_BASE_URL = window.location.origin;

class APIClient {
  constructor() {
    this.token = localStorage.getItem('auth_token');
  }

  /**
   * Get authorization headers
   */
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    return headers;
  }

  /**
   * Make an API request
   */
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (this.handleUnauthorized(response)) {
        throw new Error('Unauthorized');
      }

      const data = await this.parseResponseBody(response);

      if (!response.ok) {
        const error = new Error(this.responseErrorMessage(data, 'Request failed'));
        error.status = response.status;
        throw error;
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  handleUnauthorized(response) {
    if (response.status !== 401) {
      return false;
    }
    this.clearToken();
    if (!window.location.pathname.endsWith('/login.html')) {
      window.location.href = '/login.html';
    }
    return true;
  }

  getDownloadFilename(contentDisposition, fallback) {
    if (!contentDisposition) {
      return fallback;
    }
    const encodedMatch = contentDisposition.match(/filename\*=(?:UTF-8''|utf-8'')([^;]+)/i);
    if (encodedMatch) {
      try {
        return decodeURIComponent(encodedMatch[1].trim().replace(/^"|"$/g, ''));
      } catch (error) {
        console.warn('Failed to decode response filename:', error);
      }
    }
    const plainMatch = contentDisposition.match(/filename="?([^";\n]+)"?/i);
    return plainMatch ? plainMatch[1] : fallback;
  }

  async parseResponseBody(response) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        return await response.json();
      } catch (error) {
        return { detail: '服务器返回了无效响应' };
      }
    }
    return { detail: await response.text() };
  }

  responseErrorMessage(data, fallback) {
    if (data && typeof data.detail === 'string' && data.detail.trim()) {
      return data.detail;
    }
    if (data && typeof data.message === 'string' && data.message.trim()) {
      return data.message;
    }
    return fallback;
  }

  /**
   * Set authentication token
   */
  setToken(token) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  /**
   * Clear authentication token
   */
  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  }

  /**
   * Check authentication status
   */
  async checkAuthStatus() {
    return this.request('/api/auth/status');
  }

  /**
   * Initial setup (create first admin user)
   */
  async setup(username, password) {
    const response = await this.request('/api/auth/setup', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    if (response.success) {
      this.setToken(response.token);
      localStorage.setItem('user_info', JSON.stringify({
        username: response.username,
        is_admin: response.is_admin,
      }));
    }

    return response;
  }

  /**
   * Login
   */
  async login(username, password) {
    const response = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    if (response.success) {
      this.setToken(response.token);
      localStorage.setItem('user_info', JSON.stringify({
        username: response.username,
        is_admin: response.is_admin,
      }));
    }

    return response;
  }

  /**
   * Logout
   */
  async logout() {
    try {
      await this.request('/api/auth/logout', { method: 'POST' });
    } finally {
      this.clearToken();
      window.location.href = '/login.html';
    }
  }

  /**
   * Register new user (admin only)
   */
  async register(username, password) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  /**
   * List all users (admin only)
   */
  async listUsers() {
    return this.request('/api/auth/users');
  }

  /**
   * Delete user (admin only)
   */
  async deleteUser(username) {
    return this.request(`/api/auth/users/${encodeURIComponent(username)}`, {
      method: 'DELETE',
    });
  }

  /**
   * Check if registration is enabled (public)
   */
  async checkRegistrationStatus() {
    return this.request('/api/auth/registration-status');
  }

  /**
   * Toggle registration setting (admin only)
   */
  async toggleRegistration(enabled) {
    return this.request('/api/auth/registration-toggle', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    });
  }

  /**
   * Public user registration
   */
  async registerPublic(username, password) {
    const response = await this.request('/api/auth/register/public', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    if (response.success && response.token) {
      this.setToken(response.token);
      localStorage.setItem('user_info', JSON.stringify({
        username: response.username,
        is_admin: response.is_admin,
      }));
    }

    return response;
  }

  /**
   * Get user settings
   */
  async getSettings() {
    return this.request('/api/settings');
  }

  /**
   * Update user settings
   */
  async updateSettings(settings) {
    return this.request('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }

  /**
   * Change password
   */
  async changePassword(oldPassword, newPassword) {
    return this.request('/api/settings/password', {
      method: 'POST',
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword,
      }),
    });
  }

  /**
   * Reset settings to default
   */
  async resetSettings() {
    return this.request('/api/settings/reset', {
      method: 'POST',
    });
  }

  /**
   * Export settings as JSON file
   */
  async exportSettings() {
    const response = await fetch(`${API_BASE_URL}/api/settings/export`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
    });

    if (this.handleUnauthorized(response)) {
      throw new Error('Unauthorized');
    }
    if (!response.ok) {
      const error = await this.parseResponseBody(response);
      throw new Error(this.responseErrorMessage(error, 'Failed to export settings'));
    }

    const contentDisposition = response.headers.get('Content-Disposition');
    const filename = this.getDownloadFilename(contentDisposition, 'translation_config.json');

    // Download file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    return { success: true, filename };
  }

  /**
   * Import settings from JSON file
   */
  async importSettings(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/settings/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
      body: formData,
    });

    if (this.handleUnauthorized(response)) {
      throw new Error('Unauthorized');
    }
    if (!response.ok) {
      const error = await this.parseResponseBody(response);
      throw new Error(this.responseErrorMessage(error, 'Failed to import settings'));
    }

    return response.json();
  }

  /**
   * Upload file
   */
  async uploadFile(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();

    return new Promise((resolve, reject) => {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = (e.loaded / e.total) * 100;
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 401) {
          this.clearToken();
          window.location.href = '/login.html';
          reject(new Error('Unauthorized'));
          return;
        }
        let data = {};
        try {
          data = JSON.parse(xhr.responseText || '{}');
        } catch (error) {
          reject(new Error('服务器返回了无效响应'));
          return;
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(data);
          return;
        }
        reject(new Error(this.responseErrorMessage(data, 'Upload failed')));
      });

      xhr.addEventListener('error', () => reject(new Error('Upload failed')));

      xhr.open('POST', `${API_BASE_URL}/api/upload`);
      xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
      xhr.send(formData);
    });
  }

  /**
   * Start translation
   */
  async startTranslation(fileId, settings) {
    const formData = new FormData();
    formData.append('file_id', fileId);
    formData.append('settings', JSON.stringify(settings));

    const response = await fetch(`${API_BASE_URL}/api/translate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
      body: formData,
    });

    if (this.handleUnauthorized(response)) {
      throw new Error('Unauthorized');
    }
    if (!response.ok) {
      const data = await this.parseResponseBody(response);
      throw new Error(this.responseErrorMessage(data, 'Translation failed to start'));
    }

    return response.json();
  }

  /**
   * Get translation status
   */
  async getTranslationStatus(taskId) {
    return this.request(`/api/translate/status/${taskId}`);
  }

  /**
   * Get translation history
   */
  async getTranslationHistory(limit = 200, offset = 0) {
    return this.request(`/api/translate/history?limit=${limit}&offset=${offset}`);
  }

  /**
   * Get download URL for translated file
   */
  getDownloadUrl(taskId, fileType = 'mono') {
    return `${API_BASE_URL}/api/translate/download/${taskId}?file_type=${fileType}`;
  }

  /**
   * Delete a history item and its files
   */
  async deleteHistoryItem(taskId) {
    return this.request(`/api/translate/history/${taskId}`, {
      method: 'DELETE'
    });
  }

  async deleteUploadedFile(fileId) {
    return this.request(`/api/upload/${encodeURIComponent(fileId)}`, {
      method: 'DELETE',
    });
  }
}

// Export singleton instance
const api = new APIClient();
