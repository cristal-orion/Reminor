<script>
  import { currentPage, currentUser } from '../stores.js';
  import { logout } from '../auth.js';

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

  function handleLogout() {
    if (confirm('Sei sicuro di voler uscire?')) {
      logout();
    }
  }

  // Clock
  let time = new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  setInterval(() => {
    time = new Date().toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }, 1000);

  // Date
  $: dateStr = new Date().toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();

  // User display name
  $: userName = $currentUser?.name || $currentUser?.email?.split('@')[0] || 'USER';
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
    <span class="user-info" title={$currentUser?.email || ''}>
      <span class="user-icon">[U]</span>
      {userName.toUpperCase()}
    </span>
    <button class="logout-btn" on:click={handleLogout} title="Logout">
      [EXIT]
    </button>
    <span class="separator">|</span>
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
    gap: 16px;
    padding-right: 16px;
    font-size: 10px;
    letter-spacing: 0.05em;
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #00ff00;
    font-weight: bold;
  }

  .user-icon {
    opacity: 0.7;
  }

  .logout-btn {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: rgba(255, 255, 255, 0.7);
    font-family: inherit;
    font-size: 9px;
    font-weight: bold;
    letter-spacing: 0.1em;
    padding: 4px 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .logout-btn:hover {
    border-color: #ff4444;
    color: #ff4444;
    background: rgba(255, 68, 68, 0.1);
  }

  .separator {
    opacity: 0.3;
  }
</style>
