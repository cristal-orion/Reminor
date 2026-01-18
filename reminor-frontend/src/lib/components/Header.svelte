<script>
  import { currentPage } from '../stores.js';

  const navItems = [
    { id: 'home', label: '[1] DASHBOARD', key: '1' },
    { id: 'diario', label: '[2] DIARIO', key: '2' },
    { id: 'calendario', label: '[3] ARCHIVIO', key: '3' },
    { id: 'chat', label: '[4] CHAT', key: '4' },
    { id: 'emozioni', label: '[5] EMOZIONI', key: '5' },
    { id: 'statistiche', label: '[6] STATS', key: '6' },
    { id: 'settings', label: '[7] SETTINGS', key: '7' },
  ];

  function navigate(pageId) {
    currentPage.set(pageId);
  }

  // Clock
  let time = new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  setInterval(() => {
    time = new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }, 1000);

  // Date
  $: dateStr = new Date().toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
</script>

<header class="header">
  <div class="header-left">
    <div class="brand">REMINOR OS v2.4</div>
    <nav class="nav">
      {#each navItems as item}
        <button
          class="nav-btn {$currentPage === item.id ? 'active' : ''}"
          on:click={() => navigate(item.id)}
        >
          {item.label}
        </button>
      {/each}
    </nav>
  </div>
  <div class="header-right">
    <span>MEM: 1024KB OK</span>
    <span>{dateStr}</span>
    <span>{time}</span>
  </div>
</header>

<style>
  .header {
    width: 100%;
    height: 40px;
    border-bottom: 1px solid white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: black;
    flex-shrink: 0;
  }

  .header-left {
    display: flex;
    align-items: center;
    height: 100%;
  }

  .brand {
    padding: 0 16px;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.05em;
    border-right: 1px solid white;
    height: 100%;
    display: flex;
    align-items: center;
  }

  .nav {
    display: flex;
    height: 100%;
  }

  .nav-btn {
    padding: 0 16px;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.08em;
    border: none;
    border-right: 1px solid white;
    background: transparent;
    color: white;
    cursor: pointer;
    height: 100%;
    display: flex;
    align-items: center;
    transition: background-color 0.1s, color 0.1s;
  }

  .nav-btn:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }

  .nav-btn.active {
    background-color: white;
    color: black;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 24px;
    padding-right: 16px;
    font-size: 10px;
    letter-spacing: 0.05em;
    opacity: 0.7;
  }
</style>
