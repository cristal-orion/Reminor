<script>
  import { onMount, onDestroy } from 'svelte';
  import { get } from 'svelte/store';
  import { currentUser, currentPage, selectedDate, entriesCache } from '../stores.js';
  import { getEntries } from '../api.js';
  import { t, locale } from '../i18n.js';

  let currentMonth = new Date();
  let days = [];
  let entries = {};
  let isLoading = false;

  $: monthName = currentMonth.toLocaleDateString($locale === 'en' ? 'en-US' : 'it-IT', { month: 'long', year: 'numeric' }).toUpperCase();

  $: weekDays = $t('calendar.weekdays');

  function generateCalendar() {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    let startOffset = firstDay.getDay() - 1;
    if (startOffset < 0) startOffset = 6;

    days = [];

    for (let i = 0; i < startOffset; i++) {
      days.push({ day: null, date: null });
    }

    for (let d = 1; d <= lastDay.getDate(); d++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const isToday = dateStr === new Date().toISOString().split('T')[0];
      const hasEntry = entries[dateStr] !== undefined;

      days.push({
        day: d,
        date: dateStr,
        isToday,
        hasEntry
      });
    }
  }

  async function loadEntries() {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const user = get(currentUser);
    const userId = user?.id || 'anon';
    const cacheKey = `${userId}-${year}-${String(month + 1).padStart(2, '0')}`;

    // Check cache first (use get() for synchronous access)
    const cache = get(entriesCache);
    if (cache[cacheKey]) {
      entries = cache[cacheKey];
      generateCalendar();
      return;
    }

    // Not in cache, fetch from API
    isLoading = true;
    try {
      const startDate = `${year}-${String(month + 1).padStart(2, '0')}-01`;
      const lastDay = new Date(year, month + 1, 0).getDate();
      const endDate = `${year}-${String(month + 1).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;

      const data = await getEntries(startDate, endDate);
      entries = {};
      data.forEach(e => {
        entries[e.date] = e;
      });

      // Store in cache
      entriesCache.update(c => {
        c[cacheKey] = entries;
        return c;
      });

      generateCalendar();
    } catch (e) {
      console.error('Failed to load entries:', e);
      generateCalendar();
    } finally {
      isLoading = false;
    }
  }

  function prevMonth() {
    currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
    loadEntries();
  }

  function nextMonth() {
    currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
    loadEntries();
  }

  function selectDay(date) {
    if (!date) return;
    selectedDate.set(date);
    currentPage.set('diario');
  }

  function handleKeydown(e) {
    if (e.key === 'ArrowLeft') {
      prevMonth();
    } else if (e.key === 'ArrowRight') {
      nextMonth();
    }
  }

  onMount(() => {
    loadEntries();
    window.addEventListener('keydown', handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener('keydown', handleKeydown);
  });
</script>

<div class="calendario-container">
  <!-- Page Header -->
  <div class="page-header">
    <div class="title-row">
      <span class="icon">calendar_month</span>
      <h1 class="title">{$t('calendar.title')}</h1>
    </div>

    <div class="month-nav">
      <button class="nav-btn" on:click={prevMonth}>
        <span class="arrow">◀</span> {$t('calendar.prev')}
      </button>
      <span class="month-name">{monthName}</span>
      <button class="nav-btn" on:click={nextMonth}>
        {$t('calendar.next')} <span class="arrow">▶</span>
      </button>
    </div>
  </div>

  <!-- Calendar -->
  <div class="calendar-wrapper">
    <!-- Week days header -->
    <div class="week-header">
      {#each weekDays as day}
        <div class="week-day">{day}</div>
      {/each}
    </div>

    <!-- Calendar grid -->
    <div class="calendar-grid">
      {#each days as cell}
        <button
          class="day-cell"
          class:today={cell.isToday}
          class:has-entry={cell.hasEntry}
          class:empty={!cell.day}
          disabled={!cell.day}
          on:click={() => selectDay(cell.date)}
        >
          {#if cell.day}
            {cell.day}
          {/if}
        </button>
      {/each}
    </div>
  </div>
</div>

<style>
  .calendario-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 32px 48px;
    overflow: auto;
  }

  .page-header {
    text-align: center;
    margin-bottom: 32px;
  }

  .title-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-bottom: 24px;
  }

  .icon {
    font-family: 'Material Symbols Outlined';
    font-size: 28px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }

  .title {
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 0.2em;
    margin: 0;
  }

  .month-nav {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 32px;
  }

  .nav-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border: 1px solid white;
    background: transparent;
    color: white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.1em;
    cursor: pointer;
    transition: background-color 0.1s, color 0.1s;
  }

  .nav-btn:hover {
    background: white;
    color: black;
  }

  .month-name {
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 0.15em;
    min-width: 200px;
    text-align: center;
  }

  .calendar-wrapper {
    max-width: 600px;
    width: 100%;
    margin: 0 auto;
  }

  .week-header {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    margin-bottom: 8px;
  }

  .week-day {
    text-align: center;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.1em;
    opacity: 0.5;
    padding: 8px;
  }

  .calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .day-cell {
    aspect-ratio: 1.2;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: bold;
    border: none;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: transparent;
    color: white;
    cursor: pointer;
    font-family: 'JetBrains Mono', monospace;
    transition: background-color 0.1s, color 0.1s;
  }

  .day-cell:nth-child(7n) {
    border-right: none;
  }

  .day-cell:hover:not(.empty) {
    background: rgba(255, 255, 255, 0.1);
  }

  .day-cell.empty {
    cursor: default;
    opacity: 0.2;
  }

  .day-cell.today {
    background: white;
    color: black;
  }

  .day-cell.has-entry {
    color: #00ff00;
  }

  .day-cell.has-entry.today {
    color: black;
  }
</style>
