/**
 * API Module for Reminor Frontend
 * All API calls include JWT authentication automatically.
 */

import { getAccessToken, refreshAccessToken, logout } from './auth.js';

// API configuration
const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE = isDev ? 'http://127.0.0.1:8000' : '';
const API_TIMEOUT = isDev ? 15000 : 30000;

// Track backend availability
let backendAvailable = null;
let lastBackendCheck = 0;
const BACKEND_CHECK_INTERVAL = 30000;

// Quick backend availability check
async function checkBackendAvailable() {
  const now = Date.now();
  if (backendAvailable !== null && (now - lastBackendCheck) < BACKEND_CHECK_INTERVAL) {
    return backendAvailable;
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1000);
    const response = await fetch(`${API_BASE}/health`, { signal: controller.signal });
    clearTimeout(timeoutId);
    backendAvailable = response.ok;
  } catch {
    backendAvailable = false;
  }
  lastBackendCheck = now;
  return backendAvailable;
}

/**
 * Get authorization headers
 */
function getAuthHeaders() {
  const token = getAccessToken();
  if (token) {
    return { 'Authorization': `Bearer ${token}` };
  }
  return {};
}

/**
 * Helper function for API calls with timeout and auth
 */
async function apiCall(endpoint, options = {}, requireAuth = true) {
  // Skip API call if backend is known to be offline
  const isAvailable = await checkBackendAvailable();
  if (!isAvailable) {
    throw new Error('Backend offline');
  }

  const url = `${API_BASE}${endpoint}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  // Remove Content-Type for FormData (browser will set it with boundary)
  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  }

  const defaultOptions = {
    headers,
    signal: controller.signal,
  };

  try {
    const response = await fetch(url, { ...defaultOptions, ...options });
    clearTimeout(timeoutId);

    // Handle 401 Unauthorized - try refresh token
    if (response.status === 401 && requireAuth) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        // Retry with new token
        const retryHeaders = {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
          ...(options.headers || {}),
        };
        if (options.body instanceof FormData) {
          delete retryHeaders['Content-Type'];
        }
        const retryResponse = await fetch(url, {
          ...options,
          headers: retryHeaders,
        });
        if (!retryResponse.ok) {
          if (retryResponse.status === 401) {
            logout();
          }
          throw new Error(`API Error: ${retryResponse.status} ${retryResponse.statusText}`);
        }
        return retryResponse.json();
      } else {
        logout();
        throw new Error('Session expired. Please login again.');
      }
    }

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError' || error.message.includes('fetch')) {
      backendAvailable = false;
      lastBackendCheck = Date.now();
    }
    throw error;
  }
}

// ==================== JOURNAL API ====================

export async function getEntries(startDate = null, endDate = null) {
  let url = `/journal/entries`;
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (params.toString()) url += `?${params}`;

  return apiCall(url);
}

export async function getEntry(date) {
  return apiCall(`/journal/entries/${date}`);
}

export async function saveEntry(date, content) {
  return apiCall(`/journal/entries`, {
    method: 'POST',
    body: JSON.stringify({ date, content }),
  });
}

// ==================== SEARCH API ====================

export async function searchEntries(query, limit = 10) {
  return apiCall(`/journal/search`, {
    method: 'POST',
    body: JSON.stringify({ query, limit }),
  });
}

// ==================== EMOTIONS API ====================

export async function analyzeEmotions(date) {
  return apiCall(`/journal/entries/${date}/analyze`, {
    method: 'POST',
  });
}

export async function getEmotions(date) {
  return apiCall(`/journal/entries/${date}/emotions`);
}

export async function getWeeklyEmotions(startDate = null) {
  const url = startDate
    ? `/journal/emotions/weekly?start_date=${startDate}`
    : `/journal/emotions/weekly`;
  return apiCall(url);
}

// ==================== CHAT API ====================

/**
 * Get current user ID from localStorage
 */
function getCurrentUserId() {
  try {
    const userData = localStorage.getItem('reminor_user');
    if (userData) {
      const user = JSON.parse(userData);
      return user?.id || 'default';
    }
  } catch {
    // Ignore errors
  }
  return 'default';
}

/**
 * Get LLM configuration from localStorage (user-specific)
 */
function getLLMConfig() {
  try {
    const userId = getCurrentUserId();
    const storageKey = `reminor_llm_config_${userId}`;
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error('Error loading LLM config:', e);
  }
  return { provider: 'groq', model: null, apiKey: null };
}

export async function sendChatMessage(message, includeContext = true) {
  const llmConfig = getLLMConfig();

  const payload = {
    message,
    include_context: includeContext,
    provider: llmConfig.provider || 'groq',
    model: llmConfig.model || null,
    api_key: llmConfig.apiKey || null,
  };

  return apiCall(`/chat`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function clearChatHistory() {
  return apiCall(`/chat/history`, {
    method: 'DELETE',
  });
}

// ==================== STATS API ====================

export async function getStats() {
  return apiCall(`/journal/stats`);
}

export async function triggerKnowledgeAnalysis() {
  return apiCall(`/journal/knowledge/analyze`, {
    method: 'POST',
  });
}

// ==================== BACKUP API ====================

export async function downloadBackupJson() {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE}/journal/backup/json`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return response.blob();
}

export async function downloadBackupZip() {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE}/journal/backup/zip`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  return response.blob();
}

// ==================== IMPORT API ====================

export async function importDiaryFiles(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }

  const isAvailable = await checkBackendAvailable();
  if (!isAvailable) {
    throw new Error('Backend offline');
  }

  const token = getAccessToken();
  const response = await fetch(`${API_BASE}/journal/import/files?rebuild_vectors=true`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    if (response.status === 401) {
      logout();
      throw new Error('Session expired. Please login again.');
    }
    throw new Error(`Import failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function rebuildMemory() {
  return apiCall(`/journal/rebuild-vectors`, {
    method: 'POST',
  });
}

// ==================== HEALTH CHECK ====================

export async function healthCheck() {
  return apiCall('/health', {}, false);
}
