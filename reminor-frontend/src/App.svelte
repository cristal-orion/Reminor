<script>
  import { onMount, onDestroy } from 'svelte';
  import { currentPage, isAuthenticated } from './lib/stores.js';
  import { initAuth } from './lib/auth.js';

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
  import Login from './lib/pages/Login.svelte';

  // Auth initialization state
  let authInitialized = false;
  let authLoading = true;

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
    login: Login,
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
    emozioni: [
      { key: '←→', label: 'SETTIMANA' },
      { key: '[SPACE]', label: 'DIARIO' },
      { key: '[ESC]', label: 'MENU' },
    ],
    statistiche: [
      { key: '[ESC]', label: 'MENU' },
    ],
    login: [
      { key: '[ENTER]', label: 'CONFERMA' },
      { key: '[TAB]', label: 'CAMPO' },
    ],
    default: [
      { key: '[ESC]', label: 'MENU' },
    ],
  };

  $: CurrentPage = pages[$currentPage] || Home;
  $: hints = footerHints[$currentPage] || footerHints.default;

  // Redirect to login if not authenticated
  $: {
    if (authInitialized && !$isAuthenticated && $currentPage !== 'login') {
      currentPage.set('login');
    }
  }

  function handleGlobalKeydown(e) {
    // Don't handle navigation if on login page
    if ($currentPage === 'login') return;

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
      if (e.key === '5') currentPage.set('emozioni');
      if (e.key === '6') currentPage.set('statistiche');
      if (e.key === '7') currentPage.set('settings');
    }
  }

  onMount(async () => {
    // Initialize authentication
    authLoading = true;
    const authenticated = await initAuth();
    authInitialized = true;
    authLoading = false;

    // If not authenticated, redirect to login
    if (!authenticated) {
      currentPage.set('login');
    }

    window.addEventListener('keydown', handleGlobalKeydown);
  });

  onDestroy(() => {
    window.removeEventListener('keydown', handleGlobalKeydown);
  });
</script>

<div class="app-container">
  {#if authLoading}
    <!-- Loading state while checking auth -->
    <div class="loading-screen">
      <div class="loading-text">INIZIALIZZAZIONE SISTEMA...</div>
      <div class="loading-bar">
        <div class="loading-progress"></div>
      </div>
    </div>
  {:else if $currentPage === 'login'}
    <!-- Login page (no header/footer) -->
    <main class="main-content full-height">
      <Login />
    </main>
  {:else}
    <!-- Authenticated app -->
    <Header />
    <main class="main-content">
      <svelte:component this={CurrentPage} />
    </main>
    <Footer {hints} />
  {/if}
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    overflow: hidden;
  }

  .app-container {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: black;
    color: white;
    overflow: hidden;
  }

  .main-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .main-content.full-height {
    height: 100vh;
  }

  /* Loading screen */
  .loading-screen {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 20px;
  }

  .loading-text {
    font-size: 12px;
    letter-spacing: 0.2em;
    opacity: 0.7;
    animation: pulse 1s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }

  .loading-bar {
    width: 200px;
    height: 2px;
    background: rgba(255, 255, 255, 0.2);
    overflow: hidden;
  }

  .loading-progress {
    height: 100%;
    width: 30%;
    background: white;
    animation: loading 1s ease-in-out infinite;
  }

  @keyframes loading {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(400%); }
  }
</style>
