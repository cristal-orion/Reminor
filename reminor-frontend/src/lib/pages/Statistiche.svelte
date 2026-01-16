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

<div class="scanline"></div>

<main class="flex-1 flex flex-col items-center justify-center px-8 py-10 max-w-[1200px] mx-auto w-full overflow-y-auto">
  <div class="w-full mb-10 text-center">
    <h1 class="text-white text-3xl font-bold tracking-[0.3em] uppercase">
      --- STATISTICHE PERSONALI ---
    </h1>
    <p class="text-white/30 text-[10px] mt-4 tracking-[0.5em] uppercase italic">
      Sistema Operativo Reminor // Accesso Autorizzato
    </p>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-8 w-full">
    <!-- Streak Card -->
    <div class="ascii-border p-8 flex flex-col bg-white/[0.03]">
      <div class="flex justify-between items-start mb-8">
        <div class="flex items-center gap-4">
          <span class="material-symbols-outlined pixel-icon-large">local_fire_department</span>
          <p class="text-white text-xs font-bold tracking-widest uppercase border-b border-dashed border-white/50">Coerenza</p>
        </div>
        <span class="text-[10px] text-white/40">ID: 0x01</span>
      </div>
      <div class="flex-1 flex flex-col">
        <p class="text-5xl font-bold tracking-tighter mb-4 uppercase">{stats.streak} Giorni</p>
        <p class="text-black bg-white text-[10px] font-bold inline-block px-2 py-1 self-start mb-8 tracking-widest">STREAK ATTIVA</p>
        <div class="mt-auto">
          <p class="text-[10px] text-white/50 mb-3 uppercase tracking-widest">Attività Recente</p>
          <div class="flex gap-2">
            {#each activityDays as active}
              <div class="w-8 h-8 {active ? 'bg-white' : 'bg-white/10 border border-white/20'}"></div>
            {/each}
          </div>
          <div class="flex justify-between mt-2 text-[9px] text-white/30 uppercase tracking-[0.2em]">
            <span>LUN</span>
            <span>DOM</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Words Card -->
    <div class="ascii-border p-8 flex flex-col bg-white/[0.03]">
      <div class="flex justify-between items-start mb-8">
        <div class="flex items-center gap-4">
          <span class="material-symbols-outlined pixel-icon-large">edit_note</span>
          <p class="text-white text-xs font-bold tracking-widest uppercase border-b border-dashed border-white/50">Scrittura</p>
        </div>
        <span class="text-[10px] text-white/40">ID: 0x02</span>
      </div>
      <div class="flex-1 flex flex-col justify-center">
        <p class="text-white/40 text-[10px] mb-2 uppercase tracking-widest">Volume Totale</p>
        <p class="text-6xl font-bold mb-6">{stats.totalWords.toLocaleString()} <span class="text-lg font-light opacity-30">WORDS</span></p>
        <div class="border-t border-terminal-border pt-6 mt-auto">
          <div class="flex justify-between items-end">
            <div>
              <p class="text-[10px] text-white/40 uppercase tracking-widest">Media/Giorno</p>
              <p class="text-2xl font-bold">+{stats.avgWords} <span class="text-[10px] font-normal opacity-40">AVG</span></p>
            </div>
            <div class="text-right">
              <p class="text-[10px] text-white/40 uppercase tracking-widest">Trend Settimanale</p>
              <p class="text-white text-lg font-bold">▲ {stats.trend}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mood Card -->
    <div class="ascii-border p-8 flex flex-col bg-white/[0.03]">
      <div class="flex justify-between items-start mb-8">
        <div class="flex items-center gap-4">
          <span class="material-symbols-outlined pixel-icon-large">mood</span>
          <p class="text-white text-xs font-bold tracking-widest uppercase border-b border-dashed border-white/50">Mood Prevalente</p>
        </div>
        <span class="text-[10px] text-white/40">ID: 0x03</span>
      </div>
      <div class="flex-1 flex flex-col justify-between">
        <div>
          <p class="text-4xl font-bold uppercase tracking-widest">{stats.dominantMood}</p>
          <p class="text-white/40 text-[10px] uppercase mt-2 tracking-[0.2em]">Rilevato nell'{stats.moodPercent}% dei log</p>
        </div>
        <div class="grid grid-cols-7 items-end gap-3 h-24 mt-8">
          {#each [30, 90, 70, 40, 60, 20, 50] as height, i}
            <div class="bg-white/{i === 6 ? '' : '10'} h-[{height}%] border-t border-white/40" style="height: {height}%"></div>
          {/each}
        </div>
      </div>
    </div>

    <!-- Keywords Card -->
    <div class="ascii-border p-8 flex flex-col bg-white/[0.03]">
      <div class="flex justify-between items-start mb-6">
        <div class="flex items-center gap-4">
          <span class="material-symbols-outlined pixel-icon-large">tag</span>
          <p class="text-white text-xs font-bold tracking-widest uppercase border-b border-dashed border-white/50">Analisi Testuale</p>
        </div>
        <span class="text-[10px] text-white/40">ID: 0x04</span>
      </div>
      <div class="flex-1">
        {#if stats.topKeywords.length > 0}
          <ul class="space-y-4 mt-2">
            {#each stats.topKeywords as kw, i}
              <li class="flex items-center justify-between group cursor-pointer border-b border-white/5 pb-2">
                <div class="flex items-center gap-3">
                  <span class="text-white/40 text-[10px]">{String(i + 1).padStart(2, '0')}.</span>
                  <span class="text-xs uppercase tracking-[0.2em] group-hover:bg-white group-hover:text-black transition-all px-1">{kw.word}</span>
                </div>
                <span class="text-[9px] text-white/30 tracking-widest uppercase">{kw.count} Occur.</span>
              </li>
            {/each}
          </ul>
        {:else}
          <div class="flex flex-col items-center justify-center h-full opacity-40">
            <span class="material-symbols-outlined text-3xl mb-2">analytics</span>
            <p class="text-[10px] uppercase tracking-widest">Analisi in arrivo</p>
            <p class="text-[9px] mt-1 opacity-60">Richiede più dati</p>
          </div>
        {/if}
      </div>
    </div>
  </div>
</main>

<style>
  .material-symbols-outlined {
    font-family: 'Material Symbols Outlined';
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }
</style>
