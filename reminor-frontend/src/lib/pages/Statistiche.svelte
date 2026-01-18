<script>
  import { onMount } from 'svelte';
  import { currentUser } from '../stores.js';
  import { getStats } from '../api.js';

  let isLoading = true;
  let stats = {
    streak: 0,
    totalWords: 0,
    avgWords: 0,
    trend: '-',
    dominantMood: '-',
    moodPercent: 0,
    topKeywords: []
  };

  // Activity grid (last 7 days)
  let activityDays = [false, false, false, false, false, false, false];

  async function loadStats() {
    isLoading = true;
    try {
      const data = await getStats($currentUser);
      if (data && data.stats) {
        stats.streak = data.stats.current_streak || 0;
        stats.totalWords = data.stats.total_words || 0;
        stats.avgWords = data.stats.average_words || 0;

        // Calculate trend based on average (simple comparison)
        if (stats.avgWords > 0) {
          stats.trend = stats.avgWords > 500 ? '+' + ((stats.avgWords / 500 - 1) * 100).toFixed(1) + '%' : '-';
        }

        // Use weekly_activity if available
        if (data.stats.weekly_activity) {
          activityDays = data.stats.weekly_activity;
        }

        // Calculate activity-based stats
        const activeDays = activityDays.filter(Boolean).length;
        if (activeDays > 0) {
          stats.moodPercent = Math.round((activeDays / 7) * 100);
          stats.dominantMood = activeDays >= 5 ? 'Costante' : activeDays >= 3 ? 'Variabile' : 'Sporadico';
        }
      }
    } catch (e) {
      console.error('Failed to load stats:', e);
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadStats();
  });
</script>

<div class="stats-page">
  <main class="stats-container">
  <div class="page-title">
    --- STATISTICHE PERSONALI ---
  </div>

  <div class="stats-grid">
    <!-- Streak Card -->
    <div class="ascii-border stat-card">
      <div class="flex justify-between items-start mb-3">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-xl">local_fire_department</span>
          <p class="text-white text-[10px] font-bold tracking-widest uppercase">Coerenza</p>
        </div>
        <span class="text-[9px] text-white/40">0x01</span>
      </div>
      <p class="text-3xl font-bold tracking-tighter mb-2">{stats.streak} <span class="text-sm opacity-50">GIORNI</span></p>
      <p class="text-black bg-white text-[9px] font-bold inline-block px-2 py-0.5 self-start mb-3">STREAK ATTIVA</p>
      <div class="mt-auto">
        <div class="flex gap-1">
          {#each activityDays as active}
            <div class="w-5 h-5 {active ? 'bg-white' : 'bg-white/10 border border-white/20'}"></div>
          {/each}
        </div>
      </div>
    </div>

    <!-- Words Card -->
    <div class="ascii-border stat-card">
      <div class="flex justify-between items-start mb-3">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-xl">edit_note</span>
          <p class="text-white text-[10px] font-bold tracking-widest uppercase">Scrittura</p>
        </div>
        <span class="text-[9px] text-white/40">0x02</span>
      </div>
      <p class="text-3xl font-bold mb-3">{stats.totalWords.toLocaleString()} <span class="text-sm opacity-50">WORDS</span></p>
      <div class="border-t border-white/20 pt-3 mt-auto">
        <div class="flex justify-between">
          <div>
            <p class="text-[9px] text-white/40 uppercase">Media/Giorno</p>
            <p class="text-lg font-bold">+{stats.avgWords}</p>
          </div>
          <div class="text-right">
            <p class="text-[9px] text-white/40 uppercase">Trend</p>
            <p class="text-lg font-bold">▲ {stats.trend}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Mood Card -->
    <div class="ascii-border stat-card">
      <div class="flex justify-between items-start mb-3">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-xl">mood</span>
          <p class="text-white text-[10px] font-bold tracking-widest uppercase">Mood</p>
        </div>
        <span class="text-[9px] text-white/40">0x03</span>
      </div>
      <p class="text-2xl font-bold uppercase tracking-wide mb-1">{stats.dominantMood}</p>
      <p class="text-white/40 text-[9px] uppercase mb-3">{stats.moodPercent}% dei log</p>
      <div class="grid grid-cols-7 items-end gap-1 h-12 mt-auto">
        {#each [30, 90, 70, 40, 60, 20, 50] as height, i}
          <div class="{i === 1 ? 'bg-white' : 'bg-white/20'}" style="height: {height}%"></div>
        {/each}
      </div>
    </div>

    <!-- Keywords Card -->
    <div class="ascii-border stat-card">
      <div class="flex justify-between items-start mb-3">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-xl">tag</span>
          <p class="text-white text-[10px] font-bold tracking-widest uppercase">Analisi</p>
        </div>
        <span class="text-[9px] text-white/40">0x04</span>
      </div>
      {#if stats.topKeywords.length > 0}
        <ul class="space-y-2">
          {#each stats.topKeywords.slice(0, 4) as kw, i}
            <li class="flex items-center justify-between text-[10px]">
              <span class="uppercase">{kw.word}</span>
              <span class="text-white/30">{kw.count}x</span>
            </li>
          {/each}
        </ul>
      {:else}
        <div class="flex flex-col items-center justify-center flex-1 opacity-40">
          <span class="material-symbols-outlined text-2xl mb-1">analytics</span>
          <p class="text-[9px] uppercase">In arrivo</p>
        </div>
      {/if}
    </div>
  </div>
  </main>
</div>

<style>
  .stats-page {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .stats-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 16px 32px;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
    min-height: 0;
  }

  .page-title {
    text-align: center;
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 0.3em;
    margin-bottom: 16px;
    flex-shrink: 0;
  }

  .stats-grid {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 12px;
    min-height: 0;
  }

  .stat-card {
    display: flex;
    flex-direction: column;
    padding: 16px;
    background: rgba(255, 255, 255, 0.02);
  }

  .ascii-border {
    border: 1px solid white;
  }

  .material-symbols-outlined {
    font-family: 'Material Symbols Outlined';
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }
</style>
