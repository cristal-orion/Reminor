<script>
  import { onMount, onDestroy } from 'svelte';
  import { currentUser, selectedDate, isLoading, entriesCache, diaryCache } from '../stores.js';
  import { getEntry, saveEntry, analyzeEmotions, getEmotions } from '../api.js';

  let content = '';
  let wordCount = 0;
  let charCount = 0;
  let isSaving = false;
  let lastSaved = null;
  let emotions = null;
  let showEmotions = false;

  // The 8 emotions to track
  const emotionTypes = [
    'Felice', 'Triste', 'Arrabbiato', 'Ansioso',
    'Sereno', 'Stressato', 'Grato', 'Motivato'
  ];

  // Format date for display
  $: displayDate = new Date($selectedDate).toLocaleDateString('it-IT', {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  }).toUpperCase();

  // Count words and chars
  $: {
    charCount = content.length;
    wordCount = content.trim() ? content.trim().split(/\s+/).length : 0;
  }

  // LocalStorage key for fallback
  function getStorageKey(date) {
    return `reminor_entry_${date}`;
  }

  function getEmotionsKey(date) {
    return `reminor_emotions_${date}`;
  }

  // Invalidate calendar cache for the month of a given date
  function invalidateCalendarCache(date) {
    const [year, month] = date.split('-');
    const userId = $currentUser?.id || 'anon';
    const cacheKey = `${userId}-${year}-${month}`;
    entriesCache.update(cache => {
      delete cache[cacheKey];
      return cache;
    });
  }

  async function loadEntry() {
    const userId = $currentUser?.id || 'anon';
    const cacheKey = `${userId}-${$selectedDate}`;

    // Check diary cache first
    const cached = $diaryCache[cacheKey];
    if (cached) {
      content = cached.content || '';
      emotions = cached.emotions || null;
      return;
    }

    try {
      isLoading.set(true);

      // Try API first
      try {
        const entry = await getEntry($selectedDate);
        content = entry.content || '';
      } catch (e) {
        // Fallback to localStorage
        const saved = localStorage.getItem(getStorageKey($selectedDate));
        content = saved || '';
      }

      // Try to load existing emotions
      try {
        const emotionData = await getEmotions($selectedDate);
        emotions = emotionData;
      } catch (e) {
        // Fallback to localStorage
        const savedEmotions = localStorage.getItem(getEmotionsKey($selectedDate));
        if (savedEmotions) {
          emotions = JSON.parse(savedEmotions);
        } else {
          emotions = null;
        }
      }

      // Store in cache
      diaryCache.update(cache => {
        cache[cacheKey] = { content, emotions };
        return cache;
      });
    } catch (e) {
      content = '';
      emotions = null;
    } finally {
      isLoading.set(false);
    }
  }

  async function save() {
    if (isSaving || !content.trim()) return;

    try {
      isSaving = true;

      // Try API first
      try {
        await saveEntry($selectedDate, content);
        // Invalidate calendar cache so it reloads with new entry
        invalidateCalendarCache($selectedDate);
      } catch (e) {
        // Fallback to localStorage
        localStorage.setItem(getStorageKey($selectedDate), content);
      }

      lastSaved = new Date().toLocaleTimeString('it-IT');

      // Analyze emotions after save
      try {
        const result = await analyzeEmotions($selectedDate);
        emotions = result;
        localStorage.setItem(getEmotionsKey($selectedDate), JSON.stringify(emotions));
      } catch (e) {
        // Generate mock emotions based on content for demo
        emotions = generateMockEmotions(content);
        localStorage.setItem(getEmotionsKey($selectedDate), JSON.stringify(emotions));
      }

      // Update diary cache with new content and emotions
      const userId = $currentUser?.id || 'anon';
      const cacheKey = `${userId}-${$selectedDate}`;
      diaryCache.update(cache => {
        cache[cacheKey] = { content, emotions };
        return cache;
      });
    } catch (e) {
      console.error('Save failed:', e);
    } finally {
      isSaving = false;
    }
  }

  // Mock emotion analysis for when API is not available
  function generateMockEmotions(text) {
    const lowerText = text.toLowerCase();
    const result = {};

    // Simple keyword-based analysis for demo
    const keywords = {
      'Felice': ['felice', 'contento', 'gioia', 'sorriso', 'bello', 'fantastico', 'meraviglioso'],
      'Triste': ['triste', 'piango', 'dolore', 'male', 'soffro', 'perdita'],
      'Arrabbiato': ['arrabbiato', 'rabbia', 'furioso', 'odio', 'irritato'],
      'Ansioso': ['ansioso', 'ansia', 'preoccupato', 'paura', 'nervoso', 'agitato'],
      'Sereno': ['sereno', 'calmo', 'pace', 'tranquillo', 'rilassato'],
      'Stressato': ['stressato', 'stress', 'pressione', 'lavoro', 'stanco', 'esausto'],
      'Grato': ['grato', 'grazie', 'fortunato', 'apprezzo', 'riconoscente'],
      'Motivato': ['motivato', 'energia', 'obiettivo', 'determinato', 'voglia', 'entusiasmo']
    };

    emotionTypes.forEach(emotion => {
      let score = 0;
      const words = keywords[emotion] || [];
      words.forEach(word => {
        if (lowerText.includes(word)) {
          score += 0.2;
        }
      });
      result[emotion] = Math.min(score, 1);
    });

    // Ensure at least one emotion has some value
    const hasValue = Object.values(result).some(v => v > 0);
    if (!hasValue && text.length > 10) {
      result['Sereno'] = 0.3;
    }

    return { emotions: result };
  }

  function exportEntry() {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `diario-${$selectedDate}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleKeydown(e) {
    if (e.ctrlKey && e.key === 's') {
      e.preventDefault();
      save();
    }
    // F2 to toggle emotions panel
    if (e.key === 'F2') {
      e.preventDefault();
      if (emotions) {
        showEmotions = !showEmotions;
      }
    }
  }

  onMount(() => {
    loadEntry();
    window.addEventListener('keydown', handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener('keydown', handleKeydown);
  });
</script>

<div class="diario-container">
  <!-- Page Header -->
  <div class="page-header">
    <h1 class="date-title">{displayDate}</h1>
    <div class="divider">
      <span class="divider-line"></span>
      <span class="divider-text">MEMO_ENTRY</span>
      <span class="divider-line"></span>
    </div>
    <div class="actions">
      <button class="action-btn" on:click={save} disabled={isSaving}>
        <span class="icon">save</span>
        {isSaving ? 'SAVING...' : 'SALVA [^S]'}
      </button>
      <button class="action-btn" on:click={exportEntry}>
        <span class="icon">download</span>
        EXPORT
      </button>
      {#if emotions}
        <button class="action-btn" on:click={() => showEmotions = !showEmotions}>
          <span class="icon">favorite</span>
          EMOZIONI [F2]
        </button>
      {/if}
    </div>
  </div>

  <!-- Main Content Area -->
  <div class="content-area">
    <!-- Editor -->
    <div class="editor-section">
      <textarea
        bind:value={content}
        class="editor"
        placeholder="Inizia a scrivere il tuo pensiero..."
        spellcheck="false"
      ></textarea>
    </div>

    <!-- Emotions Panel (shown with F2) -->
    {#if showEmotions && emotions}
      <div class="emotions-panel">
        <div class="emotions-header">
          <span class="icon">favorite</span>
          <span>EMOZIONI RILEVATE</span>
          <button class="close-btn" on:click={() => showEmotions = false}>×</button>
        </div>

        <div class="emotions-list">
          {#each emotionTypes as emotionName}
            {@const score = emotions.emotions ? (emotions.emotions[emotionName] || 0) : 0}
            <div class="emotion-item">
              <div class="emotion-row">
                <span class="emotion-name">{emotionName}</span>
                <span class="emotion-percent">{Math.round(score * 100)}%</span>
              </div>
              <div class="emotion-bar">
                <div class="emotion-fill" style="width: {score * 100}%"></div>
              </div>
            </div>
          {/each}
        </div>

        {#if emotions.daily_insights}
          <div class="insights-section">
            <div class="insights-header">
              <span class="icon">psychology</span>
              <span>INSIGHT</span>
            </div>
            {#if emotions.daily_insights.mood_summary}
              <p class="mood-summary">{emotions.daily_insights.mood_summary}</p>
            {/if}
            {#if emotions.daily_insights.energy_level !== undefined}
              <div class="energy-row">
                <span class="energy-label">ENERGIA</span>
                <div class="energy-bar">
                  <div class="energy-fill" style="width: {emotions.daily_insights.energy_level * 100}%"></div>
                </div>
                <span class="energy-value">{Math.round(emotions.daily_insights.energy_level * 100)}%</span>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Status Bar -->
  <div class="status-bar">
    <div class="status-left">
      <span class="status-item">
        <span class="icon">memory</span>
        STATUS: <span class="status-value">{isSaving ? 'SAVING' : 'IDLE'}</span>
      </span>
      {#if lastSaved}
        <span class="status-item dimmed">
          <span class="icon">cloud_done</span>
          SAVED: {lastSaved}
        </span>
      {/if}
      {#if emotions}
        <span class="status-item dimmed">
          [F2] EMOZIONI
        </span>
      {/if}
    </div>
    <div class="status-right">
      <span class="status-item">
        WORDS: <span class="counter">{String(wordCount).padStart(3, '0')}</span>
      </span>
      <span class="status-item">
        CHARS: <span class="counter">{String(charCount).padStart(4, '0')}</span>
      </span>
    </div>
  </div>
</div>

<style>
  .diario-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .page-header {
    padding: 24px 48px 16px;
    text-align: center;
    flex-shrink: 0;
  }

  .date-title {
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 0.3em;
    margin: 0 0 12px 0;
  }

  .divider {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
  }

  .divider-line {
    flex: 1;
    height: 1px;
    background: rgba(255, 255, 255, 0.2);
  }

  .divider-text {
    font-size: 10px;
    letter-spacing: 0.3em;
    opacity: 0.5;
  }

  .actions {
    display: flex;
    justify-content: center;
    gap: 12px;
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border: 1px solid white;
    background: transparent;
    color: white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.1em;
    cursor: pointer;
    transition: background-color 0.1s, color 0.1s;
  }

  .action-btn:hover {
    background: white;
    color: black;
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .content-area {
    flex: 1;
    display: flex;
    overflow: hidden;
    padding: 0 48px 16px;
    gap: 24px;
  }

  .editor-section {
    flex: 1;
    display: flex;
    overflow: hidden;
  }

  .editor {
    width: 100%;
    height: 100%;
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 16px;
    color: white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    line-height: 1.8;
    resize: none;
    outline: none;
  }

  .editor::placeholder {
    color: rgba(255, 255, 255, 0.3);
  }

  .emotions-panel {
    width: 280px;
    flex-shrink: 0;
    border: 1px solid white;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .emotions-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    border-bottom: 1px solid white;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.1em;
  }

  .emotions-header span:last-of-type {
    flex: 1;
  }

  .close-btn {
    background: none;
    border: none;
    color: white;
    font-size: 18px;
    cursor: pointer;
    padding: 0 4px;
    opacity: 0.6;
  }

  .close-btn:hover {
    opacity: 1;
  }

  .emotions-list {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    overflow-y: auto;
  }

  .emotion-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .emotion-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .emotion-name {
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  .emotion-percent {
    font-size: 10px;
    opacity: 0.6;
  }

  .emotion-bar {
    height: 6px;
    background: rgba(255, 255, 255, 0.15);
    overflow: hidden;
  }

  .emotion-fill {
    height: 100%;
    background: white;
    transition: width 0.3s;
  }

  .insights-section {
    padding: 16px;
    border-top: 1px dashed rgba(255, 255, 255, 0.3);
    margin-top: auto;
  }

  .insights-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
    opacity: 0.7;
  }

  .mood-summary {
    font-size: 11px;
    line-height: 1.5;
    opacity: 0.9;
    margin: 0 0 12px 0;
    font-style: italic;
  }

  .energy-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .energy-label {
    font-size: 9px;
    letter-spacing: 0.1em;
    opacity: 0.6;
    width: 60px;
  }

  .energy-bar {
    flex: 1;
    height: 4px;
    background: rgba(255, 255, 255, 0.15);
    overflow: hidden;
  }

  .energy-fill {
    height: 100%;
    background: linear-gradient(90deg, rgba(255,255,255,0.5), white);
    transition: width 0.3s;
  }

  .energy-value {
    font-size: 10px;
    opacity: 0.6;
    width: 35px;
    text-align: right;
  }

  .status-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 24px;
    border-top: 1px solid white;
    font-size: 10px;
    letter-spacing: 0.1em;
    flex-shrink: 0;
  }

  .status-left,
  .status-right {
    display: flex;
    align-items: center;
    gap: 20px;
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .status-item.dimmed {
    opacity: 0.5;
  }

  .status-value {
    background: white;
    color: black;
    padding: 2px 6px;
    font-weight: bold;
  }

  .counter {
    border: 1px solid white;
    padding: 2px 6px;
  }

  .icon {
    font-family: 'Material Symbols Outlined';
    font-size: 14px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }
</style>
