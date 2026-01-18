<script>
  import { onMount, onDestroy } from 'svelte';
  import { currentPage } from '../stores.js';

  const menuItems = [
    { id: 'diario', label: 'NUOVA PAGINA', icon: 'edit_document' },
    { id: 'calendario', label: 'CALENDARIO', icon: 'calendar_month' },
    { id: 'search', label: 'RICERCA', icon: 'search' },
    { id: 'chat', label: 'CHAT PENSIERI', icon: 'chat' },
    { id: 'emozioni', label: 'EMOZIONI', icon: 'favorite' },
    { id: 'statistiche', label: 'STATISTICHE', icon: 'bar_chart' },
    { id: 'settings', label: 'IMPOSTAZIONI', icon: 'settings' },
  ];

  let selectedIndex = 0;

  function handleKeydown(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = (selectedIndex + 1) % menuItems.length;
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = (selectedIndex - 1 + menuItems.length) % menuItems.length;
    } else if (e.key === 'Enter') {
      e.preventDefault();
      navigateTo(menuItems[selectedIndex].id);
    }
  }

  function navigateTo(pageId) {
    currentPage.set(pageId);
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener('keydown', handleKeydown);
  });
</script>

<div class="home-container">
  <!-- Logo Section -->
  <div class="logo-section">
    <pre class="ascii-logo">██████╗ ███████╗███╗   ███╗██╗███╗   ██╗ ██████╗ ██████╗
██╔══██╗██╔════╝████╗ ████║██║████╗  ██║██╔═══██╗██╔══██╗
██████╔╝█████╗  ██╔████╔██║██║██╔██╗ ██║██║   ██║██████╔╝
██╔══██╗██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║██║   ██║██╔══██╗
██║  ██║███████╗██║ ╚═╝ ██║██║██║ ╚████║╚██████╔╝██║  ██║
╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝</pre>
    <div class="subtitle">PERSONAL  KNOWLEDGE  RETRIEVAL  SYSTEM</div>
  </div>

  <!-- Menu Box -->
  <div class="menu-container">
    <div class="menu-box">
      {#each menuItems as item, index}
        <button
          class="menu-item {selectedIndex === index ? 'selected' : ''}"
          on:click={() => navigateTo(item.id)}
          on:mouseenter={() => selectedIndex = index}
        >
          <span class="icon">{item.icon}</span>
          <span class="label">{item.label}</span>
        </button>
      {/each}
    </div>
  </div>
</div>

<style>
  .home-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    gap: 40px;
  }

  .logo-section {
    text-align: center;
  }

  .ascii-logo {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: bold;
    line-height: 0.85;
    color: white;
    margin: 0;
    white-space: pre;
    text-align: center;
  }

  .subtitle {
    margin-top: 24px;
    font-size: 11px;
    letter-spacing: 0.4em;
    color: rgba(255, 255, 255, 0.5);
  }

  .menu-container {
    width: 100%;
    max-width: 400px;
  }

  .menu-box {
    border: 1px solid white;
    background-color: black;
  }

  .menu-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 20px;
    width: 100%;
    border: none;
    background: transparent;
    color: white;
    cursor: pointer;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    text-align: left;
    transition: background-color 0.1s, color 0.1s;
  }

  .menu-item:hover,
  .menu-item.selected {
    background-color: white;
    color: black;
  }

  .icon {
    font-family: 'Material Symbols Outlined';
    font-size: 18px;
    width: 24px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }

  .label {
    font-weight: 600;
    letter-spacing: 0.08em;
  }
</style>
