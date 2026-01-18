<script>
  import { onMount } from 'svelte';
  import { currentUser } from '../stores.js';
  import { getStats } from '../api.js';

  let isLoading = true;
  let stats = {
    streak: 0,
    longestStreak: 0,
    totalWords: 0,
    avgWords: 0,
    totalEntries: 0
  };

  // Heatmap data (90 days)
  let heatmapData = [];

  // Bar chart data (14 days)
  let barChartData = [];

  // Radar chart data (emotions)
  let emotionData = {
    felice: 0,
    sereno: 0,
    motivato: 0,
    grato: 0,
    ansioso: 0,
    stressato: 0
  };
  let dominantEmotion = '-';

  // System log (recent activity)
  let systemLog = [];

  // Tooltip state
  let tooltip = { visible: false, x: 0, y: 0, text: '' };

  async function loadStats() {
    isLoading = true;
    try {
      const data = await getStats($currentUser);
      if (data && data.stats) {
        stats.streak = data.stats.current_streak || 0;
        stats.longestStreak = data.stats.longest_streak || 0;
        stats.totalWords = data.stats.total_words || 0;
        stats.avgWords = data.stats.average_words || 0;
        stats.totalEntries = data.stats.total_entries || 0;

        // Process heatmap data (90 days)
        if (data.stats.daily_words) {
          const sortedDates = Object.keys(data.stats.daily_words).sort();
          heatmapData = sortedDates.map(date => ({
            date,
            words: data.stats.daily_words[date] || 0
          }));
        }

        // Process bar chart data (14 days)
        if (data.stats.recent_daily_words) {
          barChartData = data.stats.recent_daily_words;
        }

        // Process emotion data
        if (data.stats.emotion_averages) {
          const ea = data.stats.emotion_averages;
          emotionData = {
            felice: ea.felice || 0,
            sereno: ea.sereno || 0,
            motivato: ea.motivato || 0,
            grato: ea.grato || 0,
            ansioso: ea.ansioso || 0,
            stressato: ea.stressato || 0
          };

          // Find dominant emotion
          let maxVal = 0;
          for (const [key, val] of Object.entries(emotionData)) {
            if (val > maxVal) {
              maxVal = val;
              dominantEmotion = key.charAt(0).toUpperCase() + key.slice(1);
            }
          }
        }

        // Generate system log from recent activity
        systemLog = generateSystemLog(data.stats);
      }
    } catch (e) {
      console.error('Failed to load stats:', e);
    } finally {
      isLoading = false;
    }
  }

  // Heatmap helper functions
  function getHeatmapColor(words) {
    if (words === 0) return 'rgba(255,255,255,0.08)';
    if (words < 100) return 'rgba(255,255,255,0.25)';
    if (words < 300) return 'rgba(255,255,255,0.5)';
    if (words < 500) return 'rgba(255,255,255,0.75)';
    return 'rgba(255,255,255,1)';
  }

  function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short' });
  }

  function formatLogTime(dateStr) {
    const d = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now - d) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'OGGI';
    if (diffDays === 1) return 'IERI';
    if (diffDays < 7) return `${diffDays}GG FA`;
    return d.toLocaleDateString('it-IT', { day: '2-digit', month: 'short' });
  }

  function generateSystemLog(statsData) {
    const logs = [];
    const now = new Date();

    // Last entry saved
    if (statsData.last_entry) {
      const lastWords = statsData.recent_daily_words?.find(d => d.date === statsData.last_entry)?.words || 0;
      logs.push({
        time: formatLogTime(statsData.last_entry),
        action: 'ENTRY.SAVED',
        detail: `${lastWords} parole`
      });
    }

    // Streak milestone
    if (statsData.current_streak >= 7) {
      logs.push({
        time: 'OGGI',
        action: 'STREAK.MILESTONE',
        detail: `${statsData.current_streak}d attivi`
      });
    }

    // Find most productive day in last 14
    if (statsData.recent_daily_words?.length > 0) {
      const maxDay = statsData.recent_daily_words.reduce((max, d) =>
        d.words > (max?.words || 0) ? d : max, null);
      if (maxDay && maxDay.words > 0) {
        logs.push({
          time: formatLogTime(maxDay.date),
          action: 'PEAK.OUTPUT',
          detail: `${maxDay.words} parole`
        });
      }
    }

    // First entry info
    if (statsData.first_entry) {
      logs.push({
        time: formatLogTime(statsData.first_entry),
        action: 'SYSTEM.INIT',
        detail: 'Prima entry'
      });
    }

    // Add total stats summary
    logs.push({
      time: 'TOTALE',
      action: 'DATA.INDEXED',
      detail: `${statsData.total_entries} entries`
    });

    return logs.slice(0, 6); // Max 6 entries
  }

  // Bar chart calculations
  $: maxBarWords = Math.max(...barChartData.map(d => d.words), 1);
  $: avgBarWords = barChartData.length > 0
    ? barChartData.reduce((sum, d) => sum + d.words, 0) / barChartData.length
    : 0;

  // Radar chart calculations (hexagonal)
  const radarLabels = ['Felice', 'Sereno', 'Motivato', 'Grato', 'Ansioso', 'Stressato'];
  const radarKeys = ['felice', 'sereno', 'motivato', 'grato', 'ansioso', 'stressato'];

  function polarToCart(angle, radius, cx, cy) {
    const rad = (angle - 90) * (Math.PI / 180);
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad)
    };
  }

  $: radarPoints = (() => {
    const cx = 90, cy = 80, maxR = 60;
    const points = [];
    radarKeys.forEach((key, i) => {
      const angle = (360 / 6) * i;
      const value = emotionData[key] || 0;
      const r = value * maxR;
      const pt = polarToCart(angle, r, cx, cy);
      points.push(`${pt.x},${pt.y}`);
    });
    return points.join(' ');
  })();

  // Radar points for larger chart
  $: radarPointsLarge = (() => {
    const cx = 110, cy = 95, maxR = 55;
    const points = [];
    radarKeys.forEach((key, i) => {
      const angle = (360 / 6) * i;
      const value = emotionData[key] || 0;
      const r = value * maxR;
      const pt = polarToCart(angle, r, cx, cy);
      points.push(`${pt.x},${pt.y}`);
    });
    return points.join(' ');
  })();

  // Generate radar grid lines
  function getRadarGrid(level, cx = 90, cy = 80, maxR = 60) {
    const r = (level / 5) * maxR;
    const points = [];
    for (let i = 0; i < 6; i++) {
      const angle = (360 / 6) * i;
      const pt = polarToCart(angle, r, cx, cy);
      points.push(`${pt.x},${pt.y}`);
    }
    return points.join(' ');
  }

  // Tooltip handlers
  function showTooltip(e, text) {
    const rect = e.target.getBoundingClientRect();
    tooltip = {
      visible: true,
      x: rect.left + rect.width / 2,
      y: rect.top - 8,
      text
    };
  }

  function hideTooltip() {
    tooltip.visible = false;
  }

  onMount(() => {
    loadStats();
  });
</script>

<div class="stats-page">
  <!-- Scanlines overlay -->
  <div class="scanlines"></div>

  <main class="stats-container">
    <div class="page-title glitch" data-text="--- STATS TERMINAL ---">
      --- STATS TERMINAL ---
    </div>

    <div class="stats-grid">
      <!-- 0x01: COERENZA (Heatmap) -->
      <div class="stat-card">
        <div class="corner-tl"></div>
        <div class="corner-tr"></div>
        <div class="corner-bl"></div>
        <div class="corner-br"></div>

        <div class="card-header">
          <div class="header-left">
            <span class="material-symbols-outlined">local_fire_department</span>
            <span class="card-label glitch-text">COERENZA</span>
          </div>
          <span class="card-id">0x01</span>
        </div>

        <div class="coerenza-content">
          <div class="streak-header">
            <div class="streak-display">
              <span class="streak-num">{stats.streak}</span>
              <span class="streak-label">GIORNI</span>
            </div>
            <div class="streak-meta">
              <div class="streak-badge-outline">STREAK ATTIVA</div>
              <div class="streak-record">REC: {stats.longestStreak}d</div>
            </div>
          </div>

          <!-- GitHub-style Heatmap (larger, centered) -->
          <div class="heatmap-container">
            <div class="heatmap-grid">
              {#each Array(7) as _, row}
                <div class="heatmap-row">
                  {#each Array(13) as _, col}
                    {@const idx = col * 7 + row}
                    {@const item = heatmapData[idx]}
                    {#if item}
                      <div
                        class="heatmap-cell"
                        style="background: {getHeatmapColor(item.words)}"
                        on:mouseenter={(e) => showTooltip(e, `${formatDate(item.date)}: ${item.words} parole`)}
                        on:mouseleave={hideTooltip}
                        role="gridcell"
                        tabindex="-1"
                      ></div>
                    {:else}
                      <div class="heatmap-cell empty"></div>
                    {/if}
                  {/each}
                </div>
              {/each}
            </div>
            <div class="heatmap-legend">
              <span class="legend-label">MENO</span>
              <div class="legend-cell" style="background: rgba(255,255,255,0.08)"></div>
              <div class="legend-cell" style="background: rgba(255,255,255,0.25)"></div>
              <div class="legend-cell" style="background: rgba(255,255,255,0.5)"></div>
              <div class="legend-cell" style="background: rgba(255,255,255,0.75)"></div>
              <div class="legend-cell" style="background: rgba(255,255,255,1)"></div>
              <span class="legend-label">PIU</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 0x02: SCRITTURA (Bar Chart) -->
      <div class="stat-card">
        <div class="corner-tl"></div>
        <div class="corner-tr"></div>
        <div class="corner-bl"></div>
        <div class="corner-br"></div>

        <div class="card-header">
          <div class="header-left">
            <span class="material-symbols-outlined">edit_note</span>
            <span class="card-label glitch-text">SCRITTURA</span>
          </div>
          <span class="card-id">0x02</span>
        </div>

        <div class="scrittura-content">
          <div class="words-display">
            <span class="words-num">{stats.totalWords.toLocaleString()}</span>
            <span class="words-label">PAROLE TOTALI</span>
          </div>
          <div class="words-meta">
            <div class="meta-item">
              <span class="meta-label">MEDIA/GG</span>
              <span class="meta-value">{stats.avgWords}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">ENTRIES</span>
              <span class="meta-value">{stats.totalEntries}</span>
            </div>
          </div>

          <!-- SVG Bar Chart -->
          <div class="barchart-container">
            <svg viewBox="0 0 280 100" class="barchart-svg">
              <!-- Average line -->
              {#if avgBarWords > 0}
                <line
                  x1="0"
                  y1={85 - (avgBarWords / maxBarWords) * 70}
                  x2="280"
                  y2={85 - (avgBarWords / maxBarWords) * 70}
                  stroke="rgba(255,255,255,0.3)"
                  stroke-dasharray="4,4"
                  stroke-width="1"
                />
                <text
                  x="275"
                  y={82 - (avgBarWords / maxBarWords) * 70}
                  fill="rgba(255,255,255,0.4)"
                  font-size="6"
                  text-anchor="end"
                >AVG</text>
              {/if}

              <!-- Bars -->
              {#each barChartData as day, i}
                {@const barHeight = maxBarWords > 0 ? (day.words / maxBarWords) * 70 : 0}
                {@const barX = i * 20 + 2}
                <rect
                  x={barX}
                  y={85 - barHeight}
                  width="16"
                  height={barHeight}
                  fill={day.words >= avgBarWords ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.4)'}
                  on:mouseenter={(e) => showTooltip(e, `${formatDate(day.date)}: ${day.words} parole`)}
                  on:mouseleave={hideTooltip}
                  role="graphics-symbol"
                  tabindex="-1"
                />
              {/each}

              <!-- X axis -->
              <line x1="0" y1="86" x2="280" y2="86" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
            </svg>
            <div class="barchart-labels">
              <span>14 GG FA</span>
              <span>OGGI</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 0x03: MOOD (Radar Chart) -->
      <div class="stat-card">
        <div class="corner-tl"></div>
        <div class="corner-tr"></div>
        <div class="corner-bl"></div>
        <div class="corner-br"></div>

        <div class="card-header">
          <div class="header-left">
            <span class="material-symbols-outlined">mood</span>
            <span class="card-label glitch-text">MOOD</span>
          </div>
          <span class="card-id">0x03</span>
        </div>

        <div class="mood-content">
          <!-- SVG Radar Chart (full size) -->
          <div class="radar-container">
            <svg viewBox="0 0 220 200" class="radar-svg">
              <!-- Grid levels -->
              {#each [1, 2, 3, 4, 5] as level}
                <polygon
                  points={getRadarGrid(level, 110, 95, 55)}
                  fill="none"
                  stroke="rgba(255,255,255,{0.08 + level * 0.02})"
                  stroke-width="0.5"
                />
              {/each}

              <!-- Axis lines -->
              {#each radarLabels as _, i}
                {@const angle = (360 / 6) * i}
                {@const endPt = polarToCart(angle, 55, 110, 95)}
                <line
                  x1="110" y1="95"
                  x2={endPt.x} y2={endPt.y}
                  stroke="rgba(255,255,255,0.12)"
                  stroke-width="0.5"
                />
              {/each}

              <!-- Data polygon -->
              <polygon
                points={radarPointsLarge}
                fill="rgba(255,255,255,0.12)"
                stroke="rgba(255,255,255,0.8)"
                stroke-width="1.5"
              />

              <!-- Data points -->
              {#each radarKeys as key, i}
                {@const angle = (360 / 6) * i}
                {@const value = emotionData[key] || 0}
                {@const pt = polarToCart(angle, value * 55, 110, 95)}
                <circle cx={pt.x} cy={pt.y} r="2.5" fill="white"/>
              {/each}

              <!-- Labels (full names) -->
              {#each radarLabels as label, i}
                {@const angle = (360 / 6) * i}
                {@const labelPt = polarToCart(angle, 75, 110, 95)}
                <text
                  x={labelPt.x}
                  y={labelPt.y}
                  fill="rgba(255,255,255,0.6)"
                  font-size="9"
                  text-anchor="middle"
                  dominant-baseline="middle"
                  font-family="JetBrains Mono, monospace"
                >{label.toUpperCase()}</text>
              {/each}

              <!-- Center label with background -->
              <rect x="80" y="87" width="60" height="16" fill="rgba(0,0,0,0.8)" rx="2"/>
              <text
                x="110" y="95"
                fill="white"
                font-size="9"
                text-anchor="middle"
                dominant-baseline="middle"
                font-weight="bold"
                font-family="JetBrains Mono, monospace"
              >{dominantEmotion.toUpperCase()}</text>
            </svg>
          </div>
        </div>
      </div>

      <!-- 0x04: SYSTEM LOG -->
      <div class="stat-card">
        <div class="corner-tl"></div>
        <div class="corner-tr"></div>
        <div class="corner-bl"></div>
        <div class="corner-br"></div>

        <div class="card-header">
          <div class="header-left">
            <span class="material-symbols-outlined">terminal</span>
            <span class="card-label glitch-text">SYSTEM.LOG</span>
          </div>
          <span class="card-id">0x04</span>
        </div>

        <div class="analisi-content">
          <div class="terminal-output">
            <div class="terminal-line header-line">
              <span class="terminal-prompt">&gt;</span>
              <span class="terminal-cmd">tail -f /var/log/reminor.log</span>
            </div>
            {#each systemLog as log, i}
              <div class="log-entry" style="animation-delay: {i * 0.1}s">
                <span class="log-time">[{log.time}]</span>
                <span class="log-action">{log.action}</span>
                <span class="log-detail">{log.detail}</span>
              </div>
            {/each}
            {#if systemLog.length === 0}
              <div class="log-entry empty">
                <span class="log-detail">Nessuna attività recente...</span>
              </div>
            {/if}
            <div class="terminal-line">
              <span class="terminal-prompt">&gt;</span>
              <span class="terminal-cursor">_</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <!-- Tooltip -->
  {#if tooltip.visible}
    <div
      class="tooltip"
      style="left: {tooltip.x}px; top: {tooltip.y}px;"
    >
      {tooltip.text}
    </div>
  {/if}
</div>

<style>
  .stats-page {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    position: relative;
    overflow: hidden;
  }

  /* Scanlines overlay */
  .scanlines {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
      0deg,
      rgba(0, 0, 0, 0) 0px,
      rgba(0, 0, 0, 0) 1px,
      rgba(0, 0, 0, 0.03) 1px,
      rgba(0, 0, 0, 0.03) 2px
    );
    pointer-events: none;
    z-index: 100;
  }

  .stats-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 12px 24px;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
    min-height: 0;
  }

  .page-title {
    text-align: center;
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 0.25em;
    margin-bottom: 12px;
    flex-shrink: 0;
    font-family: 'JetBrains Mono', monospace;
  }

  /* Glitch effect */
  .glitch {
    position: relative;
    animation: glitch-skew 4s infinite linear alternate-reverse;
  }

  .glitch::before,
  .glitch::after {
    content: attr(data-text);
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
  }

  .glitch::before {
    left: 2px;
    text-shadow: -2px 0 rgba(255, 255, 255, 0.3);
    clip: rect(24px, 550px, 90px, 0);
    animation: glitch-anim 3s infinite linear alternate-reverse;
  }

  .glitch::after {
    left: -2px;
    text-shadow: 2px 0 rgba(255, 255, 255, 0.3);
    clip: rect(85px, 550px, 140px, 0);
    animation: glitch-anim2 2s infinite linear alternate-reverse;
  }

  @keyframes glitch-anim {
    0% { clip: rect(51px, 9999px, 28px, 0); }
    5% { clip: rect(70px, 9999px, 19px, 0); }
    10% { clip: rect(12px, 9999px, 45px, 0); }
    15% { clip: rect(0, 0, 0, 0); }
    100% { clip: rect(0, 0, 0, 0); }
  }

  @keyframes glitch-anim2 {
    0% { clip: rect(65px, 9999px, 3px, 0); }
    5% { clip: rect(22px, 9999px, 57px, 0); }
    10% { clip: rect(0, 0, 0, 0); }
    100% { clip: rect(0, 0, 0, 0); }
  }

  @keyframes glitch-skew {
    0% { transform: skew(0deg); }
    2% { transform: skew(0.5deg); }
    4% { transform: skew(0deg); }
    100% { transform: skew(0deg); }
  }

  .glitch-text {
    animation: glitch-text-flicker 5s infinite;
  }

  @keyframes glitch-text-flicker {
    0%, 90%, 100% { opacity: 1; }
    91% { opacity: 0.8; }
    92% { opacity: 1; }
    93% { opacity: 0.9; }
    94% { opacity: 1; }
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
    padding: 12px 14px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.3);
    position: relative;
    overflow: hidden;
  }

  /* Corner markers */
  .corner-tl, .corner-tr, .corner-bl, .corner-br {
    position: absolute;
    width: 8px;
    height: 8px;
    border-color: white;
    border-style: solid;
    border-width: 0;
  }

  .corner-tl {
    top: -1px;
    left: -1px;
    border-top-width: 2px;
    border-left-width: 2px;
  }

  .corner-tr {
    top: -1px;
    right: -1px;
    border-top-width: 2px;
    border-right-width: 2px;
  }

  .corner-bl {
    bottom: -1px;
    left: -1px;
    border-bottom-width: 2px;
    border-left-width: 2px;
  }

  .corner-br {
    bottom: -1px;
    right: -1px;
    border-bottom-width: 2px;
    border-right-width: 2px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    flex-shrink: 0;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .card-label {
    font-size: 9px;
    font-weight: bold;
    letter-spacing: 0.15em;
    font-family: 'JetBrains Mono', monospace;
  }

  .card-id {
    font-size: 8px;
    color: rgba(255, 255, 255, 0.3);
    font-family: 'JetBrains Mono', monospace;
  }

  .material-symbols-outlined {
    font-family: 'Material Symbols Outlined';
    font-size: 16px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }

  /* 0x01 COERENZA */
  .coerenza-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .streak-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
  }

  .streak-display {
    display: flex;
    align-items: baseline;
    gap: 4px;
  }

  .streak-num {
    font-size: 28px;
    font-weight: bold;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
  }

  .streak-label {
    font-size: 9px;
    opacity: 0.5;
  }

  .streak-meta {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .streak-badge-outline {
    display: inline-block;
    border: 1px solid rgba(255, 255, 255, 0.4);
    color: rgba(255, 255, 255, 0.6);
    font-size: 7px;
    font-weight: bold;
    padding: 2px 5px;
    font-family: 'JetBrains Mono', monospace;
  }

  .streak-record {
    font-size: 8px;
    opacity: 0.4;
    font-family: 'JetBrains Mono', monospace;
  }

  .heatmap-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 0;
    padding: 8px 0;
  }

  .heatmap-grid {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .heatmap-row {
    display: flex;
    gap: 2px;
  }

  .heatmap-cell {
    width: 16px;
    height: 16px;
    border-radius: 2px;
    cursor: pointer;
    transition: transform 0.1s;
  }

  .heatmap-cell:hover {
    transform: scale(1.2);
  }

  .heatmap-cell.empty {
    background: rgba(255, 255, 255, 0.05);
  }

  .heatmap-legend {
    display: flex;
    align-items: center;
    gap: 3px;
    margin-top: 8px;
    justify-content: center;
    flex-shrink: 0;
  }

  .legend-label {
    font-size: 6px;
    opacity: 0.4;
    font-family: 'JetBrains Mono', monospace;
  }

  .legend-cell {
    width: 10px;
    height: 10px;
    border-radius: 2px;
  }

  /* 0x02 SCRITTURA */
  .scrittura-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .words-display {
    display: flex;
    align-items: baseline;
    gap: 6px;
    flex-shrink: 0;
  }

  .words-num {
    font-size: 26px;
    font-weight: bold;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
  }

  .words-label {
    font-size: 9px;
    opacity: 0.5;
  }

  .words-meta {
    display: flex;
    gap: 20px;
    margin: 6px 0;
    flex-shrink: 0;
  }

  .meta-item {
    display: flex;
    flex-direction: column;
  }

  .meta-label {
    font-size: 7px;
    opacity: 0.4;
    font-family: 'JetBrains Mono', monospace;
  }

  .meta-value {
    font-size: 14px;
    font-weight: bold;
    font-family: 'JetBrains Mono', monospace;
  }

  .barchart-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    min-height: 0;
  }

  .barchart-svg {
    width: 100%;
    flex: 1;
    min-height: 60px;
  }

  .barchart-svg rect {
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .barchart-svg rect:hover {
    opacity: 0.7;
  }

  .barchart-labels {
    display: flex;
    justify-content: space-between;
    font-size: 6px;
    opacity: 0.4;
    margin-top: 4px;
    font-family: 'JetBrains Mono', monospace;
    flex-shrink: 0;
  }

  /* 0x03 MOOD */
  .mood-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 0;
  }

  .radar-container {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 0;
  }

  .radar-svg {
    width: 100%;
    height: 100%;
    max-width: 100%;
  }

  /* 0x04 SYSTEM LOG */
  .analisi-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .terminal-output {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
  }

  .terminal-line {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
  }

  .terminal-line.header-line {
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .terminal-prompt {
    color: rgba(255, 255, 255, 0.5);
  }

  .terminal-cmd {
    color: rgba(255, 255, 255, 0.4);
    font-size: 8px;
  }

  .log-entry {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 3px 0;
    animation: log-fade-in 0.3s ease-out forwards;
    opacity: 0;
  }

  .log-entry.empty {
    opacity: 0.4;
    font-style: italic;
  }

  @keyframes log-fade-in {
    from {
      opacity: 0;
      transform: translateX(-8px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .log-time {
    color: rgba(255, 255, 255, 0.35);
    font-size: 7px;
    min-width: 50px;
  }

  .log-action {
    color: white;
    font-weight: bold;
    font-size: 9px;
  }

  .log-detail {
    color: rgba(255, 255, 255, 0.45);
    font-size: 8px;
    margin-left: auto;
  }

  .terminal-cursor {
    animation: cursor-blink 1s infinite;
  }

  @keyframes cursor-blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }

  /* Tooltip */
  .tooltip {
    position: fixed;
    background: white;
    color: black;
    padding: 4px 8px;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    pointer-events: none;
    transform: translate(-50%, -100%);
    z-index: 200;
    white-space: nowrap;
  }

  .tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 4px solid transparent;
    border-top-color: white;
  }
</style>
