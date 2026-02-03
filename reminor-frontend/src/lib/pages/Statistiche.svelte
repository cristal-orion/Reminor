<script>
  import { onMount } from 'svelte';
  import { currentUser } from '../stores.js';
  import { getStats, triggerKnowledgeAnalysis } from '../api.js';
  import { t, locale, getEmotionDisplayName } from '../i18n.js';

  let isLoading = true;
  let stats = {
    streak: 0,
    longestStreak: 0,
    totalWords: 0,
    avgWords: 0,
    totalEntries: 0
  };

  // Density Map (Last 90 days)
  let densityMap = [];
  
  // System Profile
  let aiSummary = "";

  // Visual Stats
  let writingTrend = 0;
  let isPositiveTrend = true;
  let dominantMood = "N/D";
  let dominantPercentage = 0;
  let moodDistribution = [];

  async function loadStats() {
    isLoading = true;
    try {
      const data = await getStats();
      if (data && data.stats) {
        stats.streak = data.stats.current_streak || 0;
        stats.longestStreak = data.stats.longest_streak || 0;
        stats.totalWords = data.stats.total_words || 0;
        stats.avgWords = Math.round(data.stats.average_words || 0);
        stats.totalEntries = data.stats.total_entries || 0;
        
        // 0. AI Summary (System Profile)
        // Check if ai_summary exists in stats (from user_knowledge.json via backend)
        // The backend structure for 'stats' endpoint returns { stats: ..., ai_summary: ... }
        if (data.ai_summary) {
            aiSummary = data.ai_summary;
        } else {
            // Trigger analysis if not available
            aiSummary = null; // Will use $t('stats.analysis_unavailable') in template
            try {
                // Trigger background analysis silently
                // We don't await this to keep UI responsive
                triggerKnowledgeAnalysis().then(() => {
                    // Optional: reload stats after a delay?
                    // For now just let it run for next time.
                    console.log("Analysis triggered.");
                }).catch(err => console.error("Analysis trigger failed", err));
            } catch (e) {
                console.error("Failed to trigger analysis", e);
            }
        }

        // 1. Process Density Map (Last ~12 weeks/84 days for a clean grid)
        // We need 12 columns of 7 days = 84 blocks
        const densityDays = 84; 
        const today = new Date();
        densityMap = Array(densityDays).fill(0).map((_, i) => {
          // Calculate date going backwards from today (but we want today at the end)
          // The grid fills column by column (top-down). 
          // 84 blocks: 
          // Col 1: Day -83 to -77
          // ...
          // Col 12: Day -6 to Today
          
          // Actually, let's just make a linear list of days from oldest to newest
          // The CSS grid-auto-flow: column will fill top-to-bottom, left-to-right.
          // So index 0 is Top-Left (oldest), index 6 is Bottom-Left.
          // index 7 is Top-SecondColumn, etc.
          // So we need to order dates such that the visual result is correct.
          // Visual result standard: Left->Right are weeks. Top->Bottom are days (Mon->Sun).
          
          // Let's stick to a simpler row-based approach or just standard flex wrap if grid is too hard to calc perfectly without library.
          // BUT, to fix the "overflow" issue, the grid needs to fit the container.
          // 84 blocks might be too many for the width/height of the card.
          // Let's reduce to 10 weeks (70 days) to be safe or adjust CSS gap/size.
          
          const d = new Date(today);
          d.setDate(d.getDate() - (densityDays - 1 - i));
          
          const dateStr = d.toISOString().split('T')[0];
          const wordCount = data.stats.daily_words ? (data.stats.daily_words[dateStr] || 0) : 0;
          
          // Determine intensity 0-4
          let intensity = 0;
          if (wordCount > 0) intensity = 1;
          if (wordCount > 100) intensity = 2;
          if (wordCount > 300) intensity = 3;
          if (wordCount > 600) intensity = 4;

          return {
            date: dateStr,
            count: wordCount,
            intensity: intensity
          };
        });

        // 2. Calculate Writing Trend
        // Now fetched from backend
        if (data.stats.writing_trend !== undefined) {
          writingTrend = Math.abs(data.stats.writing_trend);
          isPositiveTrend = data.stats.writing_trend >= 0;
        } else {
           // Fallback if backend doesn't return it yet
           writingTrend = 0;
           isPositiveTrend = true;
        }

        // 3. Process Mood Distribution
        if (data.stats.emotion_averages) {
          const em = data.stats.emotion_averages;
          // Map to array for bar chart
          const rawMoods = [
            { name: 'felice', value: em.felice || 0 },
            { name: 'sereno', value: em.sereno || 0 },
            { name: 'motivato', value: em.motivato || 0 },
            { name: 'grato', value: em.grato || 0 },
            { name: 'ansioso', value: em.ansioso || 0 },
            { name: 'stressato', value: em.stressato || 0 }
          ];
          
          // Sort by value to find dominant
          rawMoods.sort((a, b) => b.value - a.value);
          
          if (rawMoods[0].value > 0) {
            dominantMood = rawMoods[0].name;
            dominantPercentage = Math.round(rawMoods[0].value * 100);
          }

          // Take top 6 for chart
          moodDistribution = rawMoods.slice(0, 6);
        }
      }
    } catch (e) {
      console.error('Failed to load stats:', e);
    } finally {
      isLoading = false;
    }
  }

  function formatNumber(num) {
    const loc = $locale === 'en' ? 'en-US' : 'it-IT';
    return num.toLocaleString(loc);
  }

  onMount(() => {
    loadStats();
  });
</script>

<div class="stats-page">
  <div class="page-header">
    <div class="header-content">
      <div class="header-line">{$t('stats.title')}</div>
      <div class="header-sub">{$t('stats.subtitle')}</div>
    </div>
  </div>

  <div class="stats-grid">
    
    <!-- CARD 1: DENSITÀ MEMORIA -->
    <div class="stat-card">
      <div class="card-top">
        <div class="card-icon-title">
          <span class="pixel-icon">grid_view</span>
          <span class="card-title">{$t('stats.density')}</span>
        </div>
        <span class="card-id">0x01</span>
      </div>

      <div class="card-main">
        <div class="density-grid">
          {#each densityMap as block}
            <div class="density-block intensity-{block.intensity}" title="{block.date}: {block.count} words"></div>
          {/each}
        </div>
      </div>

      <div class="card-bottom">
        <div class="row-between">
            <div class="bottom-label">{$t('stats.last_days')}</div>
            <div class="density-legend">
                <span>{$t('stats.less')}</span>
                <div class="legend-scale">
                    <div class="density-block intensity-0"></div>
                    <div class="density-block intensity-2"></div>
                    <div class="density-block intensity-4"></div>
                </div>
                <span>{$t('stats.more')}</span>
            </div>
        </div>
      </div>
    </div>

    <!-- CARD 2: SCRITTURA -->
    <div class="stat-card">
      <div class="card-top">
        <div class="card-icon-title">
          <span class="pixel-icon">edit</span>
          <span class="card-title">{$t('stats.writing')}</span>
        </div>
        <span class="card-id">0x02</span>
      </div>

      <div class="card-main">
        <div class="mid-label">{$t('stats.total_volume')}</div>
        <div class="big-number-row">
          <span class="giant-number">{formatNumber(stats.totalWords)}</span>
          <span class="unit">WORDS</span>
        </div>
      </div>

      <div class="card-bottom row-between">
        <div class="metric-col">
          <div class="bottom-label">{$t('stats.daily_average')}</div>
          <div class="metric-value">+{formatNumber(stats.avgWords)} <span class="dim">AVG</span></div>
        </div>
        <div class="metric-col right">
          <div class="bottom-label">{$t('stats.trend')}</div>
          <div class="metric-value {isPositiveTrend ? 'green' : 'red'}">
            {isPositiveTrend ? '▲' : '▼'} {writingTrend}%
          </div>
        </div>
      </div>
    </div>

    <!-- CARD 3: MOOD PREVALENTE -->
    <div class="stat-card">
      <div class="card-top">
        <div class="card-icon-title">
          <span class="pixel-icon">sentiment_satisfied</span>
          <span class="card-title">{$t('stats.dominant_mood')}</span>
        </div>
        <span class="card-id">0x03</span>
      </div>

      <div class="card-main">
        <div class="giant-text">{getEmotionDisplayName(dominantMood, $locale)}</div>
        <div class="sub-text">{$t('stats.detected_in')} {dominantPercentage}% {$t('stats.of_texts')}</div>
      </div>

      <div class="card-bottom no-pad">
        <div class="mood-bars">
          {#each moodDistribution as mood}
            <div class="mood-bar-container">
              <div class="mood-bar" style="height: {mood.value * 100}%"></div>
            </div>
          {/each}
        </div>
      </div>
    </div>

    <!-- CARD 4: PROFILO SISTEMA -->
    <div class="stat-card">
      <div class="card-top">
        <div class="card-icon-title">
          <span class="pixel-icon">terminal</span>
          <span class="card-title">{$t('stats.system_profile')}</span>
        </div>
        <span class="card-id">0x04</span>
      </div>

      <div class="card-terminal">
        <div class="terminal-content">
          > {$t('stats.system_init')}<br>
          > {$t('stats.reading_pattern')}<br>
          <br>
          <span class="terminal-text">{aiSummary || $t('stats.analysis_unavailable')}</span>
          <span class="cursor">_</span>
        </div>
      </div>
    </div>

  </div>
</div>

<style>
  :global(body) {
    background-color: #050505;
  }

  .stats-page {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 20px 40px;
    height: 100vh;
    box-sizing: border-box;
    font-family: 'JetBrains Mono', monospace;
    background-color: #050505;
    color: #e0e0e0;
  }

  /* Header */
  .page-header {
    display: flex;
    justify-content: center;
    margin-bottom: 40px;
    margin-top: 10px;
  }

  .header-content {
    text-align: center;
  }

  .header-line {
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 0.2em;
    margin-bottom: 8px;
    color: #fff;
  }

  .header-sub {
    font-size: 10px;
    color: #666;
    letter-spacing: 0.1em;
  }

  /* Grid Layout */
  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 20px;
    flex: 1;
    min-height: 0; /* Important for scrolling if needed */
  }

  /* Card Base */
  .stat-card {
    background: #0a0a0a;
    border: 1px solid #333;
    padding: 24px;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  /* Card Top */
  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
  }

  .card-icon-title {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .pixel-icon {
    font-family: 'Material Symbols Outlined';
    font-size: 18px;
    opacity: 0.7;
    /* Dotted texture simulation if possible, else solid */
  }

  .card-title {
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom: 1px dotted #666;
    padding-bottom: 2px;
  }

  .card-id {
    font-size: 10px;
    color: #444;
  }

  /* Card Main Content */
  .card-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .big-number {
    font-size: 36px;
    font-weight: bold;
    color: #fff;
    margin-bottom: 8px;
  }

  .streak-badge {
    background: #ccc;
    color: #000;
    display: inline-block;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: bold;
    width: fit-content;
  }

  .mid-label {
    font-size: 10px;
    color: #666;
    text-transform: uppercase;
    margin-bottom: 4px;
  }

  .big-number-row {
    display: flex;
    align-items: baseline;
    gap: 12px;
  }

  .giant-number {
    font-size: 48px;
    font-weight: bold;
    color: #fff;
    line-height: 1;
  }

  .unit {
    font-size: 14px;
    color: #666;
    font-weight: bold;
  }

  .giant-text {
    font-size: 42px;
    font-weight: bold;
    color: #fff;
    line-height: 1;
    margin-bottom: 8px;
  }

  .sub-text {
    font-size: 10px;
    color: #666;
    text-transform: uppercase;
  }

  /* Card Bottom */
  .card-bottom {
    margin-top: auto;
    padding-top: 20px;
  }
  
  .card-bottom.no-pad {
    padding-top: 0;
    margin-bottom: -10px; /* Align bars to bottom edge visually */
  }

  .row-between {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }

  .metric-col {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .metric-col.right {
    text-align: right;
  }

  .bottom-label {
    font-size: 9px;
    color: #555;
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .metric-value {
    font-size: 16px;
    font-weight: bold;
    color: #fff;
  }
  
  .metric-value.green { color: #fff; } /* Keeping monochromatic as per reference */
  .metric-value .dim { font-size: 10px; color: #666; }

  /* Density Grid (Memory) */
  .density-grid {
    display: grid;
    /* Adjust grid to fit container better: 12 columns might be too wide with gap. 
       Let's try flexible columns or reduce count. 
       Actually, the issue is likely the fixed size blocks + gap overflowing.
    */
    grid-template-columns: repeat(12, 1fr);
    grid-template-rows: repeat(7, 1fr);
    grid-auto-flow: column;
    gap: 3px; /* Reduced gap */
    height: 100%;
    width: 100%; /* Ensure grid fits width */
    max-width: 100%; /* Prevent overflow */
    overflow: hidden; /* Hide anything that spills out, though ideally shouldn't happen */
    
    /* Remove max-height constraint to let it fill available space in card-main */
    /* max-height: 140px; */ 
    align-content: center; /* Center vertically if space allows */
    justify-content: center; /* Center horizontally */
  }

  .density-block {
    background: #1a1a1a;
    border-radius: 1px;
    /* aspect-ratio: 1;  <-- This might cause overflow if width > height available */
    width: 100%; /* Fill the grid cell */
    height: 100%; /* Fill the grid cell */
    /* Remove min-width/height to allow shrinking if necessary */
    /* min-width: 10px; */
    /* min-height: 10px; */
  }

  .density-block.intensity-0 { background: #1a1a1a; }
  .density-block.intensity-1 { background: #333; }
  .density-block.intensity-2 { background: #666; }
  .density-block.intensity-3 { background: #999; }
  .density-block.intensity-4 { background: #e0e0e0; }

  .density-legend {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 8px;
    color: #666;
  }

  .legend-scale {
    display: flex;
    gap: 2px;
  }

  .legend-scale .density-block {
    width: 8px;
    height: 8px;
  }

  /* Terminal Profile */
  .card-terminal {
    flex: 1;
    background: #000;
    border: 1px solid #1a1a1a;
    padding: 12px;
    font-family: 'JetBrains Mono', monospace;
    overflow: hidden;
    position: relative;
  }

  .terminal-content {
    font-size: 10px;
    line-height: 1.4;
    color: #888;
  }

  .terminal-text {
    color: #ccc;
    white-space: pre-wrap; /* Maintain formatting of summary */
  }

  .cursor {
    display: inline-block;
    width: 6px;
    height: 12px;
    background: #ccc;
    animation: blink 1s step-end infinite;
    vertical-align: text-bottom;
    margin-left: 2px;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }

  /* Mood Bars */
  .mood-bars {
    display: flex;
    align-items: flex-end;
    gap: 12px;
    height: 60px;
  }

  .mood-bar-container {
    flex: 1;
    height: 100%;
    display: flex;
    align-items: flex-end;
  }

  .mood-bar {
    width: 100%;
    background: #333;
    min-height: 2px;
  }
  
  /* Make the first (dominant) bar white */
  .mood-bar-container:first-child .mood-bar {
    background: #e0e0e0;
  }


</style>
