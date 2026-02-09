import { writable, derived } from 'svelte/store';

// Re-export locale from i18n
export { locale } from './i18n.js';

// ==================== AUTHENTICATION STORES ====================

// Current authenticated user (null = not logged in)
export const currentUser = writable(null);

// JWT access token
export const authToken = writable(null);

// Authentication status
export const isAuthenticated = writable(false);

// Derived store for user ID (for API calls)
export const userId = derived(currentUser, ($currentUser) => {
  return $currentUser?.id || null;
});

// ==================== NAVIGATION STORES ====================

// Current route/page
export const currentPage = writable('home');

// Menu selection index for keyboard navigation
export const menuIndex = writable(0);

// ==================== APP SETTINGS ====================

export const settings = writable({
  theme: 'dark',
  font: 'JetBrains Mono',
  autoSave: true,
  apiKey: null
});

// ==================== DIARY STORES ====================

// Current date for diary
// Format today as YYYY-MM-DD in local timezone (not UTC)
export const selectedDate = writable((() => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
})());

// Loading state
export const isLoading = writable(false);

// Chat messages
export const chatMessages = writable([]);

// Journal entries cache (for calendar month view)
export const entriesCache = writable({});

// Individual diary entry cache (for diary page)
export const diaryCache = writable({});

// Stats cache
export const statsCache = writable(null);
