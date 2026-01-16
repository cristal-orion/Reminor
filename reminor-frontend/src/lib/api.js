// API configuration
// In production (Docker), use empty string - nginx proxies to backend
// In development, use localhost:8001
const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE = isDev ? 'http://127.0.0.1:8001' : '';
const API_TIMEOUT = isDev ? 15000 : 30000; // 15s dev, 30s production

// Track backend availability
let backendAvailable = null; // null = unknown, true = online, false = offline
let lastBackendCheck = 0;
const BACKEND_CHECK_INTERVAL = 30000; // Recheck every 30 seconds

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

// Helper function for API calls with timeout
async function apiCall(endpoint, options = {}) {
  // Skip API call if backend is known to be offline
  const isAvailable = await checkBackendAvailable();
  if (!isAvailable) {
    throw new Error('Backend offline');
  }

  const url = `${API_BASE}${endpoint}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
    signal: controller.signal,
  };

  try {
    const response = await fetch(url, { ...defaultOptions, ...options });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    // Mark backend as offline on connection errors
    if (error.name === 'AbortError' || error.message.includes('fetch')) {
      backendAvailable = false;
      lastBackendCheck = Date.now();
    }
    throw error;
  }
}

// ==================== JOURNAL API ====================

export async function getEntries(userId, startDate = null, endDate = null) {
  let url = `/journal/${userId}/entries`;
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (params.toString()) url += `?${params}`;

  return apiCall(url);
}

export async function getEntry(userId, date) {
  return apiCall(`/journal/${userId}/entries/${date}`);
}

export async function saveEntry(userId, date, content) {
  return apiCall(`/journal/${userId}/entries`, {
    method: 'POST',
    body: JSON.stringify({ date, content }),
  });
}

// ==================== SEARCH API ====================

export async function searchEntries(userId, query, limit = 10) {
  return apiCall(`/journal/${userId}/search`, {
    method: 'POST',
    body: JSON.stringify({ query, limit }),
  });
}

// ==================== EMOTIONS API ====================

export async function analyzeEmotions(userId, date) {
  return apiCall(`/journal/${userId}/entries/${date}/analyze`, {
    method: 'POST',
  });
}

export async function getEmotions(userId, date) {
  return apiCall(`/journal/${userId}/entries/${date}/emotions`);
}

export async function getWeeklyEmotions(userId) {
  return apiCall(`/journal/${userId}/emotions/weekly`);
}

// ==================== CHAT API ====================

/**
 * Get LLM configuration from localStorage
 * @returns {Object} LLM config with provider, model, apiKey
 */
function getLLMConfig() {
  try {
    const saved = localStorage.getItem('reminor_llm_config');
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.error('Error loading LLM config:', e);
  }
  // Default to Groq (uses env API key on backend)
  return { provider: 'groq', model: null, apiKey: null };
}

export async function sendChatMessage(userId, message, includeContext = true) {
  const llmConfig = getLLMConfig();

  const payload = {
    message,
    include_context: includeContext,
    provider: llmConfig.provider || 'groq',
    model: llmConfig.model || null,
    api_key: llmConfig.apiKey || null,
  };

  return apiCall(`/chat/${userId}`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function clearChatHistory(userId) {
  return apiCall(`/chat/${userId}/history`, {
    method: 'DELETE',
  });
}

// ==================== STATS API ====================

export async function getStats(userId) {
  return apiCall(`/journal/${userId}/stats`);
}

// ==================== BACKUP API ====================

export async function downloadBackupJson(userId) {
  const response = await fetch(`${API_BASE}/journal/${userId}/backup/json`);
  return response.blob();
}

export async function downloadBackupZip(userId) {
  const response = await fetch(`${API_BASE}/journal/${userId}/backup/zip`);
  return response.blob();
}

// ==================== IMPORT API ====================

export async function importDiaryFiles(userId, files) {
  // Use FormData for file upload
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }

  const isAvailable = await checkBackendAvailable();
  if (!isAvailable) {
    throw new Error('Backend offline');
  }

  const response = await fetch(`${API_BASE}/journal/${userId}/import/files?rebuild_vectors=true`, {
    method: 'POST',
    body: formData,
    // Don't set Content-Type - browser will set it with boundary for multipart
  });

  if (!response.ok) {
    throw new Error(`Import failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function rebuildMemory(userId) {
  return apiCall(`/journal/${userId}/rebuild-vectors`, {
    method: 'POST',
  });
}

// ==================== HEALTH CHECK ====================

export async function healthCheck() {
  return apiCall('/health');
}
