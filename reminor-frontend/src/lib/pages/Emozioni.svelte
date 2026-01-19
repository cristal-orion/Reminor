<script>
  import { onMount } from 'svelte';
  import { currentUser, currentPage } from '../stores.js';
  import { getStats, getWeeklyEmotions } from '../api.js';

  let weekDays = [];
  let isLoading = true;
  let weekNumber = 1;
  let weekYear = new Date().getFullYear();
  let weekOffset = 0; // 0 = current week, -1 = last week, etc.
  let stats = {
    stabilityIndex: 0,
    totalEntries: 0,
    entriesThisMonth: 0,
    daysInMonth: 21,
    dominantMood: '-',
    avgIntensity: 0,
    streak: 0
  };

  // Emotion icons
  const emotionIcons = {
    'felice': 'sentiment_very_satisfied',
    'triste': 'sentiment_dissatisfied',
    'arrabbiato': 'sentiment_very_dissatisfied',
    'ansioso': 'psychology_alt',
    'sereno': 'sentiment_neutral',
    'stressato': 'mood_bad',
    'grato': 'favorite',
    'motivato': 'auto_awesome'
  };

  const emotionLabels = {
    'felice': 'JOY',
    'triste': 'SAD',
    'arrabbiato': 'ANGRY',
    'ansioso': 'ANXIOUS',
    'sereno': 'NEUTRAL',
    'stressato': 'STRESSED',
    'grato': 'GRATEFUL',
    'motivato': 'INSPIRED'
  };

  // Energy level categories
  function getEnergyInfo(level) {
    if (level < 0.35) {
      return { label: 'TIRED', icon: 'bedtime' };
    } else if (level < 0.65) {
      return { label: 'CALM', icon: 'self_improvement' };
    } else {
      return { label: 'ENERGY', icon: 'bolt' };
    }
  }

  function getWeekNumber(date) {
    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
    const pastDaysOfYear = (date - firstDayOfYear) / 86400000;
    return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
  }

  function initWeekDays(offset = 0) {
    const today = new Date();

    // Calculate Monday of the target week
    const monday = new Date(today);
    const dayOfWeek = today.getDay();
    const daysFromMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    monday.setDate(today.getDate() - daysFromMonday + (offset * 7));

    weekNumber = getWeekNumber(monday);
    weekYear = monday.getFullYear();

    const dayNames = ['LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB', 'DOM'];
    const days = [];

    for (let i = 0; i < 7; i++) {
      const d = new Date(monday);
      d.setDate(monday.getDate() + i);
      const dateStr = d.toISOString().split('T')[0];
      const isToday = d.toDateString() === today.toDateString();
      const isFuture = d > today;
      const isPast = d < today && !isToday;

      days.push({
        name: dayNames[i],
        day: d.getDate(),
        date: dateStr,
        isToday,
        isFuture,
        isPast,
        hasData: false,
        dominant: null,
        dominantIcon: null,
        dominantLabel: null,
        emotionIntensity: 0,
        energyLevel: 0.5,
        energyInfo: null
      });
    }
    return days;
  }

  function getDaysInMonth() {
    const today = new Date();
    return new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
  }

  async function loadData() {
    isLoading = true;
    weekDays = initWeekDays(weekOffset);
    stats.daysInMonth = getDaysInMonth();

    // Get start date for API call (Monday of the week)
    const startDate = weekDays.length > 0 ? weekDays[0].date : null;

    try {
      const statsData = await getStats();
      if (statsData && statsData.stats) {
        stats.totalEntries = statsData.stats.total_entries || 0;
        stats.streak = statsData.stats.current_streak || 0;
      }

      const emotionsData = await getWeeklyEmotions(startDate);
      if (emotionsData && emotionsData.weekly_emotions) {
        let totalIntensity = 0;
        let emotionCounts = {};
        let daysWithEmotions = 0;

        weekDays = weekDays.map(day => {
          const dayData = emotionsData.weekly_emotions[day.date];
          if (dayData && dayData.emotions) {
            daysWithEmotions++;
            const intensity = dayData.intensity || 0.5;
            totalIntensity += intensity;

            const dominant = dayData.dominant;
            if (dominant) {
              emotionCounts[dominant] = (emotionCounts[dominant] || 0) + 1;
            }

            // Get dominant emotion value for card height
            const emotionValue = dayData.emotions[dominant] || 0.5;
            const energyLevel = dayData.energy_level || 0.5;

            return {
              ...day,
              hasData: true,
              dominant,
              dominantIcon: emotionIcons[dominant] || 'sentiment_neutral',
              dominantLabel: emotionLabels[dominant] || dominant?.toUpperCase(),
              emotionIntensity: emotionValue,
              energyLevel,
              energyInfo: getEnergyInfo(energyLevel)
            };
          }
          return day;
        });

        stats.entriesThisMonth = daysWithEmotions;

        if (daysWithEmotions > 0) {
          stats.avgIntensity = (totalIntensity / daysWithEmotions).toFixed(2);

          const mostCommon = Object.entries(emotionCounts)
            .sort((a, b) => b[1] - a[1])[0];
          if (mostCommon) {
            stats.dominantMood = emotionLabels[mostCommon[0]] || mostCommon[0].toUpperCase();
          }

          stats.stabilityIndex = Math.min(100, Math.round(70 + (daysWithEmotions / 7) * 30));
        }
      }
    } catch (e) {
      console.error('Failed to load emotions data:', e);
    } finally {
      isLoading = false;
    }
  }

  function navigateToDiary() {
    currentPage.set('diario');
  }

  function navigateWeek(direction) {
    // direction: -1 for previous week, 1 for next week
    if (direction === 1 && weekOffset >= 0) {
      // Don't go beyond current week
      return;
    }
    weekOffset += direction;
    loadData();
  }

  function navigateToMenu() {
    currentPage.set('home');
  }

  function handleKeydown(e) {
    if (e.key === ' ' || e.code === 'Space') {
      e.preventDefault();
      navigateToDiary();
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      navigateWeek(-1); // Previous week
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      navigateWeek(1); // Next week
    } else if (e.key === 'Escape') {
      e.preventDefault();
      navigateToMenu();
    }
  }

  onMount(() => {
    loadData();
    window.addEventListener('keydown', handleKeydown);
    return () => window.removeEventListener('keydown', handleKeydown);
  });
</script>

<div class="emotions-container">
  <header class="emotions-header">
    <div class="header-left">
      <h1 class="title">WEEKLY EMOTIONS</h1>
      <div class="week-nav">
        <button class="nav-btn" on:click={() => navigateWeek(-1)}>
          <span class="material-symbols-outlined">chevron_left</span>
        </button>
        <p class="subtitle">WEEK {String(weekNumber).padStart(2, '0')}, {weekYear}</p>
        <button class="nav-btn" on:click={() => navigateWeek(1)} disabled={weekOffset >= 0}>
          <span class="material-symbols-outlined">chevron_right</span>
        </button>
      </div>
    </div>
    <div class="stability-box">
      <span class="material-symbols-outlined stability-icon">insights</span>
      <div class="stability-content">
        <span class="stability-label">STABILITY INDEX</span>
        <span class="stability-value">{stats.stabilityIndex.toFixed(1)}%</span>
      </div>
    </div>
  </header>

  <div class="week-grid">
    {#if isLoading}
      <div class="loading-state">
        <span class="loading-text">CARICAMENTO...</span>
      </div>
    {:else}
      {#each weekDays as day}
        <div class="day-column">
          <div class="day-header" class:today={day.isToday}>
            {day.name} {day.day}
          </div>

          <div class="day-content" class:future={day.isFuture} class:empty={!day.hasData && !day.isFuture}>
            {#if day.hasData}
              <!-- Emotion block - flex grows based on intensity -->
              <div class="emotion-block" style="flex: {0.3 + day.emotionIntensity}">
                <span class="material-symbols-outlined emotion-icon">{day.dominantIcon}</span>
                <span class="emotion-label">{day.dominantLabel}</span>
              </div>

              <!-- Energy block - flex grows based on energy level -->
              <div class="energy-block" style="flex: {0.2 + day.energyLevel * 0.5}">
                <span class="material-symbols-outlined energy-icon">{day.energyInfo.icon}</span>
                <span class="energy-label">{day.energyInfo.label}</span>
              </div>
            {:else if day.isFuture}
              <div class="empty-state">
                <span class="material-symbols-outlined empty-icon">add</span>
                <span class="empty-label">LOG</span>
              </div>
            {:else if day.isPast}
              <div class="empty-state">
                <span class="material-symbols-outlined empty-icon">edit_note</span>
                <span class="empty-label">PENDING</span>
              </div>
            {:else}
              <button class="empty-state today-btn" on:click={navigateToDiary}>
                <span class="material-symbols-outlined empty-icon">edit_note</span>
                <span class="empty-label">LOG NOW</span>
              </button>
            {/if}
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <div class="stats-bar">
    <div class="stat-item">
      <span class="stat-label">TOTAL ENTRIES</span>
      <span class="stat-value">{stats.entriesThisMonth} / {stats.daysInMonth}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">DOMINANT MOOD</span>
      <span class="stat-value">{stats.dominantMood}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">AVG INTENSITY</span>
      <span class="stat-value">{stats.avgIntensity}</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">STREAK</span>
      <span class="stat-value">{stats.streak} DAYS</span>
    </div>
  </div>

</div>

<style>
  .emotions-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 32px 48px;
    overflow: hidden;
    background: black;
  }

  .emotions-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 32px;
  }

  .title {
    font-size: 32px;
    font-weight: bold;
    letter-spacing: 0.3em;
    margin: 0 0 8px 0;
  }

  .week-nav {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .nav-btn {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    cursor: pointer;
    padding: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }

  .nav-btn:hover:not(:disabled) {
    border-color: white;
    background: rgba(255, 255, 255, 0.1);
  }

  .nav-btn:disabled {
    opacity: 0.2;
    cursor: not-allowed;
  }

  .nav-btn .material-symbols-outlined {
    font-size: 18px;
  }

  .subtitle {
    font-size: 11px;
    letter-spacing: 0.2em;
    opacity: 0.5;
    margin: 0;
  }

  .stability-box {
    display: flex;
    align-items: center;
    gap: 16px;
    border: 1px solid white;
    padding: 16px 24px;
  }

  .stability-icon {
    font-size: 32px;
    opacity: 0.8;
  }

  .stability-content {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }

  .stability-label {
    font-size: 9px;
    letter-spacing: 0.1em;
    opacity: 0.5;
  }

  .stability-value {
    font-size: 24px;
    font-weight: bold;
  }

  .week-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 12px;
    flex: 1;
    min-height: 0;
    margin-bottom: 24px;
  }

  .loading-state {
    grid-column: span 7;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .loading-text {
    font-size: 12px;
    letter-spacing: 0.2em;
    opacity: 0.5;
  }

  .day-column {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-height: 0;
  }

  .day-header {
    text-align: center;
    padding: 10px 8px;
    border: 1px solid white;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.1em;
    background: transparent;
  }

  .day-header.today {
    background: white;
    color: black;
  }

  .day-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-height: 350px;
  }

  .day-content.future {
    border: 1px dashed rgba(255, 255, 255, 0.3);
    justify-content: center;
    align-items: center;
  }

  .day-content.empty {
    justify-content: center;
    align-items: center;
  }

  /* Emotion block - top section */
  .emotion-block {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border: 1px solid white;
    min-height: 80px;
  }

  /* Energy block - bottom section */
  .energy-block {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 1px solid white;
    min-height: 50px;
  }

  .emotion-icon {
    font-size: 36px;
  }

  .emotion-label {
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.1em;
    text-align: center;
  }

  .energy-icon {
    font-size: 28px;
    opacity: 0.9;
  }

  .energy-label {
    font-size: 10px;
    letter-spacing: 0.1em;
    opacity: 0.8;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    opacity: 0.4;
    padding: 24px;
  }

  .empty-icon {
    font-size: 28px;
  }

  .empty-label {
    font-size: 10px;
    letter-spacing: 0.1em;
  }

  .today-btn {
    background: transparent;
    border: 1px dashed rgba(255, 255, 255, 0.5);
    color: white;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.2s;
    opacity: 0.7;
  }

  .today-btn:hover {
    border-color: white;
    opacity: 1;
  }

  .stats-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 32px;
    padding: 24px 32px;
    border: 1px solid white;
    margin-bottom: 16px;
  }

  .stat-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .stat-label {
    font-size: 9px;
    letter-spacing: 0.15em;
    opacity: 0.5;
  }

  .stat-value {
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 0.05em;
  }

  .material-symbols-outlined {
    font-family: 'Material Symbols Outlined';
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }
</style>
