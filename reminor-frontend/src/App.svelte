<script>
  import { onMount, onDestroy } from 'svelte';
  import { currentPage } from './lib/stores.js';

  // Components
  import Header from './lib/components/Header.svelte';
  import Footer from './lib/components/Footer.svelte';

  // Pages
  import Home from './lib/pages/Home.svelte';
  import Diario from './lib/pages/Diario.svelte';
  import Calendario from './lib/pages/Calendario.svelte';
  import Chat from './lib/pages/Chat.svelte';
  import Emozioni from './lib/pages/Emozioni.svelte';
  import Statistiche from './lib/pages/Statistiche.svelte';
  import Settings from './lib/pages/Settings.svelte';
  import Search from './lib/pages/Search.svelte';

  // Page components map
  const pages = {
    home: Home,
    diario: Diario,
    calendario: Calendario,
    chat: Chat,
    emozioni: Emozioni,
    statistiche: Statistiche,
    settings: Settings,
    search: Search,
  };

  // Footer hints per page
  const footerHints = {
    home: [
      { key: '↕', label: 'NAVIGA' },
      { key: '[ENTER]', label: 'SELEZIONA' },
      { key: '[ESC]', label: 'ESCI' },
    ],
    diario: [
      { key: '[^S]', label: 'SALVA' },
      { key: '[ESC]', label: 'MENU' },
    ],
    calendario: [
      { key: '←→', label: 'MESE' },
      { key: '[ENTER]', label: 'APRI' },
      { key: '[ESC]', label: 'MENU' },
    ],
    chat: [
      { key: '[ENTER]', label: 'INVIA' },
      { key: '[ESC]', label: 'MENU' },
    ],
    default: [
      { key: '[ESC]', label: 'MENU' },
    ],
  };

  $: CurrentPage = pages[$currentPage] || Home;
  $: hints = footerHints[$currentPage] || footerHints.default;

  function handleGlobalKeydown(e) {
    // ESC to go back to home
    if (e.key === 'Escape' && $currentPage !== 'home') {
      e.preventDefault();
      currentPage.set('home');
    }

    // Number keys for quick navigation (only if not in input)
    const activeElement = document.activeElement;
    const isEditing = activeElement.tagName === 'INPUT' ||
                      activeElement.tagName === 'TEXTAREA' ||
                      activeElement.isContentEditable;

    if (!isEditing && !e.ctrlKey && !e.metaKey) {
      if (e.key === '1') currentPage.set('home');
      if (e.key === '2') currentPage.set('diario');
      if (e.key === '3') currentPage.set('calendario');
      if (e.key === '4') currentPage.set('chat');
      if (e.key === '5') currentPage.set('settings');
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleGlobalKeydown);
  });

  onDestroy(() => {
    window.removeEventListener('keydown', handleGlobalKeydown);
  });
</script>

<div class="app-container">
  <!-- Header (sempre visibile, uguale in tutte le pagine) -->
  <Header />

  <!-- Main content -->
  <main class="main-content">
    <svelte:component this={CurrentPage} />
  </main>

  <!-- Footer -->
  <Footer {hints} />
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    overflow: hidden;
  }

  .app-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: black;
    color: white;
  }

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
</style>
