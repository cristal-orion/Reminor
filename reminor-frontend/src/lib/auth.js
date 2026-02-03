/**
 * Authentication Module for Reminor Frontend
 * Handles login, registration, token management, and session persistence.
 */

import { currentUser, authToken, isAuthenticated, currentPage, entriesCache, diaryCache, statsCache, chatMessages } from './stores.js';
import { locale } from './i18n.js';

// API configuration
const isDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE = isDev ? 'http://127.0.0.1:8000' : '';

// Local storage keys
const TOKEN_KEY = 'reminor_access_token';
const REFRESH_TOKEN_KEY = 'reminor_refresh_token';
const USER_KEY = 'reminor_user';

/**
 * Save tokens to localStorage
 */
export function saveTokens(accessToken, refreshToken) {
  localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

/**
 * Get access token from localStorage
 */
export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Get refresh token from localStorage
 */
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Remove all auth data from localStorage
 */
export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Save user data to localStorage
 */
export function saveUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * Get user data from localStorage
 */
export function getStoredUser() {
  try {
    const userData = localStorage.getItem(USER_KEY);
    return userData ? JSON.parse(userData) : null;
  } catch {
    return null;
  }
}

/**
 * Check if token is expired (simple check)
 */
function isTokenExpired(token) {
  if (!token) return true;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // Convert to milliseconds
    return Date.now() >= exp;
  } catch {
    return true;
  }
}

/**
 * Register a new user
 * @param {string} email - User email
 * @param {string} password - User password
 * @param {string} name - User name (optional)
 * @returns {Promise<object>} - Token response
 */
export async function register(email, password, name = null) {
  // Read current language from localStorage
  const language = localStorage.getItem('reminor_language') || 'it';

  const response = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password, name, language }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  const tokens = await response.json();

  // Save tokens
  saveTokens(tokens.access_token, tokens.refresh_token);
  authToken.set(tokens.access_token);

  // Load user info
  await loadCurrentUser();

  return tokens;
}

/**
 * Login with email and password
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise<object>} - Token response
 */
export async function login(email, password) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  const tokens = await response.json();

  // Save tokens
  saveTokens(tokens.access_token, tokens.refresh_token);
  authToken.set(tokens.access_token);

  // Load user info
  await loadCurrentUser();

  return tokens;
}

/**
 * Refresh the access token using refresh token
 * @returns {Promise<boolean>} - True if refresh successful
 */
export async function refreshAccessToken() {
  const refreshToken = getRefreshToken();

  if (!refreshToken || isTokenExpired(refreshToken)) {
    return false;
  }

  try {
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(refreshToken),
    });

    if (!response.ok) {
      return false;
    }

    const tokens = await response.json();
    saveTokens(tokens.access_token, tokens.refresh_token);
    authToken.set(tokens.access_token);

    return true;
  } catch {
    return false;
  }
}

/**
 * Load current user info from API
 * @returns {Promise<object|null>} - User data or null
 */
export async function loadCurrentUser() {
  const token = getAccessToken();

  if (!token) {
    isAuthenticated.set(false);
    currentUser.set(null);
    return null;
  }

  // Check if token is expired
  if (isTokenExpired(token)) {
    // Try to refresh
    const refreshed = await refreshAccessToken();
    if (!refreshed) {
      logout();
      return null;
    }
  }

  try {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Try refresh token
        const refreshed = await refreshAccessToken();
        if (refreshed) {
          return loadCurrentUser();
        }
        logout();
        return null;
      }
      throw new Error('Failed to load user');
    }

    const user = await response.json();

    // Update stores
    saveUser(user);
    currentUser.set(user);
    isAuthenticated.set(true);

    // Sync locale from user profile
    if (user.language && (user.language === 'it' || user.language === 'en')) {
      locale.set(user.language);
    }

    return user;
  } catch (error) {
    console.error('Error loading user:', error);
    logout();
    return null;
  }
}

/**
 * Logout - clear all auth state
 */
export function logout() {
  // Clear auth tokens
  clearTokens();

  // Reset auth state
  currentUser.set(null);
  authToken.set(null);
  isAuthenticated.set(false);

  // Clear all data caches
  entriesCache.set({});
  diaryCache.set({});
  statsCache.set(null);
  chatMessages.set([]);

  // Redirect to login
  currentPage.set('login');
}

/**
 * Initialize auth state from localStorage
 * Call this on app startup
 * @returns {Promise<boolean>} - True if user is authenticated
 */
export async function initAuth() {
  const token = getAccessToken();

  if (!token) {
    isAuthenticated.set(false);
    currentUser.set(null);
    return false;
  }

  // Set token in store
  authToken.set(token);

  // Try to load stored user first (for faster UI)
  const storedUser = getStoredUser();
  if (storedUser) {
    currentUser.set(storedUser);
    isAuthenticated.set(true);
  }

  // Verify token is still valid by loading user from API
  const user = await loadCurrentUser();

  return user !== null;
}

/**
 * Check if user is currently authenticated
 * @returns {boolean}
 */
export function checkAuth() {
  const token = getAccessToken();
  return token && !isTokenExpired(token);
}
