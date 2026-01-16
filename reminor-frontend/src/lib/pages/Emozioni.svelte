<script>
  import { onMount } from 'svelte';
  import { currentUser } from '../stores.js';
  import { getStats, getWeeklyEmotions } from '../api.js';

  let weekDays = [];
  let isLoading = true;
  let stats = {
    stabilityIndex: 0,
    totalEntries: 0,
    dominantMood: '-',
    avgIntensity: 0,
    streak: 0
  };

  // Emotion icon mapping
  const emotionIcons = {
    'felice': 'sentiment_very_satisfied',
    'triste': 'sentiment_dissatisfied',
    'arrabbiato': 'sentiment_very_dissatisfied',
    'ansioso': 'psychology_alt',
    'neutro': 'sentiment_neutral',
    'calmo': 'self_improvement',
    'energico': 'bolt'
  };

  const emotionLabels = {
    'felice': 'FELICE',
    'triste': 'TRISTE',
    'arrabbiato': 'ARRABBIATO',
    'ansioso': 'ANSIOSO',
    'neutro': 'NEUTRO',
    'calmo': 'CALMO',
    'energico': 'ENERGICO'
  };

  // Generate week days structure
  function initWeekDays() {
    const today = new Date();
    const dayNames = ['DOM', 'LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB'];
    const days = [];

    for (let i = 6; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const dateStr = d.toISOString().split('T')[0];
      days.push({
        name: dayNames[d.getDay()],
        day: d.getDate(),
        date: dateStr,
        isToday: i === 0,
        emotion: null,
        dominant: null,
        intensity: 0
      });
    }
    return days;
  }

  async function loadData() {
    isLoading = true;
    weekDays = initWeekDays();

    try {
      // Load stats
      const statsData = await getStats($currentUser);
      if (statsData && statsData.stats) {
        stats.totalEntries = statsData.stats.total_entries || 0;
        stats.streak = statsData.stats.current_streak || 0;
      }

      // Load weekly emotions
      const emotionsData = await getWeeklyEmotions($currentUser);
      if (emotionsData && emotionsData.weekly_emotions) {
        let totalIntensity = 0;
        let emotionCounts = {};
        let daysWithEmotions = 0;

        weekDays = weekDays.map(day => {
          const dayEmotions = emotionsData.weekly_emotions[day.date];
          if (dayEmotions && dayEmotions.emotions) {
            daysWithEmotions++;
            totalIntensity += dayEmotions.intensity || 0;

            // Count dominant emotions
            const dominant = dayEmotions.dominant;
            if (dominant) {
              emotionCounts[dominant] = (emotionCounts[dominant] || 0) + 1;
            }

            return {
              ...day,
              emotion: emotionIcons[dayEmotions.dominant] || 'sentiment_neutral',
              dominant: dayEmotions.dominant,
              intensity: dayEmotions.intensity
            };
          }
          return day;
        });

        // Calculate stats
        if (daysWithEmotions > 0) {
          stats.avgIntensity = (totalIntensity / daysWithEmotions).toFixed(2);

          // Find most common emotion
          const mostCommon = Object.entries(emotionCounts)
            .sort((a, b) => b[1] - a[1])[0];
          if (mostCommon) {
            stats.dominantMood = emotionLabels[mostCommon[0]] || mostCommon[0].toUpperCase();
          }

          // Simple stability index (lower variance = more stable)
          stats.stabilityIndex = Math.min(100, Math.round(70 + (daysWithEmotions / 7) * 30));
        }
      }
    } catch (e) {
      console.error('Failed to load emotions data:', e);
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadData();
  });
</script>

<main class="flex-grow flex flex-col p-8 overflow-y-auto">
  <header class="mb-8 flex justify-between items-end">
    <div>
      <h1 class="text-4xl font-bold uppercase tracking-[0.3em] mb-2">WEEKLY EMOTIONS</h1>
      <div class="h-1 w-32 bg-white mb-4"></div>
      <p class="text-[12px] opacity-60 tracking-widest uppercase">STATISTICAL OVERVIEW</p>
    </div>
    <div class="flex gap-4">
      <div class="border border-white p-4 flex items-center gap-4">
        <span class="material-symbols-outlined pixel-icon-large">insights</span>
        <div>
          <div class="text-[10px] opacity-60">STABILITY INDEX</div>
          <div class="text-2xl font-bold">{stats.stabilityIndex}%</div>
        </div>
      </div>
    </div>
  </header>

  <!-- Week grid -->
  <div class="grid grid-cols-7 gap-4 flex-grow mb-12">
    {#if isLoading}
      <div class="col-span-7 flex items-center justify-center">
        <span class="text-[12px] opacity-60 tracking-widest">CARICAMENTO...</span>
      </div>
    {:else}
      {#each weekDays as day}
        <div class="flex flex-col gap-2">
          <div class="text-center py-2 border border-white {day.isToday ? 'bg-white text-black' : ''} font-bold text-[11px] tracking-widest">
            {day.name} {day.day}
          </div>
          <div class="emotion-cell flex-grow {!day.emotion ? 'border-dashed opacity-50' : ''}">
            {#if day.emotion}
              <span class="material-symbols-outlined pixel-icon-large">{day.emotion}</span>
              <span class="text-[10px] tracking-widest uppercase mt-4">
                {emotionLabels[day.dominant] || day.dominant?.toUpperCase() || 'ANALIZZATO'}
              </span>
              <span class="text-[14px] font-bold opacity-40">{(day.intensity * 100).toFixed(0)}%</span>
            {:else}
              <span class="material-symbols-outlined pixel-icon-large">{day.isToday ? 'edit_note' : 'remove'}</span>
              <span class="text-[10px] tracking-widest uppercase mt-4">{day.isToday ? 'OGGI' : 'N/A'}</span>
            {/if}
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <!-- Stats bar -->
  <div class="mt-auto border border-white p-6 grid grid-cols-4 gap-8">
    <div class="flex flex-col gap-1">
      <span class="text-[9px] opacity-60 tracking-widest">TOTAL ENTRIES</span>
      <span class="text-2xl font-bold">{stats.totalEntries}</span>
    </div>
    <div class="flex flex-col gap-1">
      <span class="text-[9px] opacity-60 tracking-widest">DOMINANT MOOD</span>
      <span class="text-2xl font-bold">{stats.dominantMood}</span>
    </div>
    <div class="flex flex-col gap-1">
      <span class="text-[9px] opacity-60 tracking-widest">AVG INTENSITY</span>
      <span class="text-2xl font-bold">{stats.avgIntensity}</span>
    </div>
    <div class="flex flex-col gap-1">
      <span class="text-[9px] opacity-60 tracking-widest">STREAK</span>
      <span class="text-2xl font-bold">{stats.streak} DAYS</span>
    </div>
  </div>
</main>

<style>
  .material-symbols-outlined {
    font-family: 'Material Symbols Outlined';
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }
</style>
