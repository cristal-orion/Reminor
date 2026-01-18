import { writable } from 'svelte/store';

// Current user (will be set after login)
export const currentUser = writable('demo_user');

// Current route/page
export const currentPage = writable('home');

// Menu selection index for keyboard navigation
export const menuIndex = writable(0);

// App settings
export const settings = writable({
  theme: 'dark',
  font: 'JetBrains Mono',
  autoSave: true,
  apiKey: null
});

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
