<script>
  import { t } from '../i18n.js';

  export let hints = [
    { key: '↕', label: 'NAVIGATE' },
    { key: '[ENTER]', label: 'SELECT' },
    { key: '[ESC]', label: 'EXIT' },
  ];

  let time = new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  setInterval(() => {
    const loc = localStorage.getItem('reminor_language') === 'en' ? 'en-US' : 'it-IT';
    time = new Date().toLocaleTimeString(loc, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }, 1000);

  // Simulated disk usage
  const diskFree = 82;
</script>

<footer class="footer-bar">
  <div class="footer-left">
    {#each hints as hint}
      <span class="hint-item">
        <span class="hint-key">{hint.key}</span>
        <span class="hint-label">{hint.label}</span>
      </span>
    {/each}
  </div>

  <div class="footer-right">
    <span class="disk-info">DISK: {diskFree}% FREE</span>
    <div class="progress-bar">
      <div class="progress-fill" style="width: {diskFree}%"></div>
    </div>
    <span class="system-status">SYSTEM READY</span>
  </div>
</footer>

<style>
  .footer-bar {
    width: 100%;
    height: 40px;
    border-top: 1px solid white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    background-color: black;
    flex-shrink: 0;
  }

  .footer-left {
    display: flex;
    align-items: center;
    gap: 24px;
  }

  .hint-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .hint-key {
    color: white;
    font-weight: bold;
  }

  .hint-label {
    color: rgba(255, 255, 255, 0.6);
  }

  .footer-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .disk-info {
    color: rgba(255, 255, 255, 0.6);
  }

  .progress-bar {
    width: 80px;
    height: 8px;
    border: 1px solid white;
    background: transparent;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background-color: white;
  }

  .system-status {
    color: white;
    font-weight: bold;
  }
</style>
