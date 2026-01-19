import { writable, derived } from 'svelte/store';

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
export const selectedDate = writable(new Date().toISOString().split('T')[0]);

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
