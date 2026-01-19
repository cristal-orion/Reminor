<script>
  import { onMount } from 'svelte';
  import { login, register } from '../auth.js';
  import { currentPage } from '../stores.js';

  let mode = 'login'; // 'login' or 'register'
  let email = '';
  let password = '';
  let name = '';
  let confirmPassword = '';
  let error = '';
  let loading = false;

  // Boot sequence animation
  let bootLines = [];
  let showForm = false;
  let bootComplete = false;

  const bootSequence = [
    'REMINOR SYSTEM v2.4',
    'INITIALIZING NEURAL INTERFACE...',
    'LOADING MEMORY BANKS...',
    'ESTABLISHING SECURE CONNECTION...',
    'AUTHENTICATION REQUIRED',
  ];

  onMount(async () => {
    // Play boot animation
    for (let i = 0; i < bootSequence.length; i++) {
      await new Promise(r => setTimeout(r, 300));
      bootLines = [...bootLines, bootSequence[i]];
    }
    await new Promise(r => setTimeout(r, 500));
    bootComplete = true;
    await new Promise(r => setTimeout(r, 200));
    showForm = true;
  });

  async function handleSubmit() {
    error = '';

    // Validation
    if (!email || !password) {
      error = 'Email e password richiesti';
      return;
    }

    if (mode === 'register') {
      if (password !== confirmPassword) {
        error = 'Le password non coincidono';
        return;
      }
      if (password.length < 8) {
        error = 'Password minimo 8 caratteri';
        return;
      }
    }

    loading = true;

    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password, name || null);
      }
      // Success - redirect to home
      currentPage.set('home');
    } catch (e) {
      error = e.message || 'Errore di autenticazione';
    } finally {
      loading = false;
    }
  }

  function toggleMode() {
    mode = mode === 'login' ? 'register' : 'login';
    error = '';
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !loading) {
      handleSubmit();
    }
  }
</script>

<div class="login-container">
  <!-- Boot sequence -->
  <div class="boot-sequence" class:fade-out={showForm}>
    {#each bootLines as line, i}
      <div class="boot-line" style="animation-delay: {i * 0.1}s">
        <span class="prompt">&gt;</span> {line}
        {#if i === bootLines.length - 1 && !bootComplete}
          <span class="cursor">_</span>
        {/if}
      </div>
    {/each}
  </div>

  <!-- Login form -->
  {#if showForm}
    <div class="login-form" class:visible={showForm}>
      <div class="form-header">
        <div class="title">
          {mode === 'login' ? 'ACCESSO SISTEMA' : 'REGISTRAZIONE NUOVO UTENTE'}
        </div>
        <div class="subtitle">
          {mode === 'login' ? 'Inserisci le credenziali' : 'Crea un nuovo account'}
        </div>
      </div>

      {#if error}
        <div class="error-box">
          <span class="error-icon">[!]</span>
          {error}
        </div>
      {/if}

      <div class="form-fields">
        {#if mode === 'register'}
          <div class="field">
            <label for="name">NOME (OPZIONALE)</label>
            <input
              type="text"
              id="name"
              bind:value={name}
              placeholder="Il tuo nome"
              disabled={loading}
              on:keydown={handleKeydown}
            />
          </div>
        {/if}

        <div class="field">
          <label for="email">EMAIL</label>
          <input
            type="email"
            id="email"
            bind:value={email}
            placeholder="user@example.com"
            disabled={loading}
            on:keydown={handleKeydown}
            autocomplete="email"
          />
        </div>

        <div class="field">
          <label for="password">PASSWORD</label>
          <input
            type="password"
            id="password"
            bind:value={password}
            placeholder="********"
            disabled={loading}
            on:keydown={handleKeydown}
            autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
          />
        </div>

        {#if mode === 'register'}
          <div class="field">
            <label for="confirmPassword">CONFERMA PASSWORD</label>
            <input
              type="password"
              id="confirmPassword"
              bind:value={confirmPassword}
              placeholder="********"
              disabled={loading}
              on:keydown={handleKeydown}
              autocomplete="new-password"
            />
          </div>
        {/if}
      </div>

      <div class="form-actions">
        <button
          class="submit-btn"
          on:click={handleSubmit}
          disabled={loading}
        >
          {#if loading}
            <span class="loading-dots">ELABORAZIONE</span>
          {:else}
            {mode === 'login' ? '[ACCEDI]' : '[REGISTRATI]'}
          {/if}
        </button>

        <button
          class="toggle-btn"
          on:click={toggleMode}
          disabled={loading}
        >
          {mode === 'login' ? 'Nuovo utente? Registrati' : 'Hai un account? Accedi'}
        </button>
      </div>

      <div class="form-footer">
        <div class="security-notice">
          <span class="lock-icon">[*]</span>
          CONNESSIONE SICURA - CRITTOGRAFIA ATTIVA
        </div>
      </div>
    </div>
  {/if}

  <!-- Decorative elements -->
  <div class="corner top-left"></div>
  <div class="corner top-right"></div>
  <div class="corner bottom-left"></div>
  <div class="corner bottom-right"></div>
</div>

<style>
  .login-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    position: relative;
    background: linear-gradient(180deg, #000 0%, #0a0a0a 100%);
  }

  /* Boot sequence */
  .boot-sequence {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    color: #00ff00;
    text-align: left;
    position: absolute;
    transition: opacity 0.5s ease;
  }

  .boot-sequence.fade-out {
    opacity: 0;
    pointer-events: none;
  }

  .boot-line {
    margin: 8px 0;
    animation: fadeIn 0.3s ease forwards;
    opacity: 0;
  }

  @keyframes fadeIn {
    to { opacity: 1; }
  }

  .prompt {
    color: #888;
  }

  .cursor {
    animation: blink 0.5s step-end infinite;
  }

  @keyframes blink {
    50% { opacity: 0; }
  }

  /* Login form */
  .login-form {
    width: 100%;
    max-width: 400px;
    border: 1px solid white;
    background: black;
    padding: 0;
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.5s ease;
  }

  .login-form.visible {
    opacity: 1;
    transform: translateY(0);
  }

  .form-header {
    border-bottom: 1px solid white;
    padding: 16px 20px;
  }

  .title {
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 0.1em;
    margin-bottom: 4px;
  }

  .subtitle {
    font-size: 10px;
    opacity: 0.6;
    letter-spacing: 0.05em;
  }

  .error-box {
    background: rgba(255, 0, 0, 0.1);
    border: 1px solid #ff4444;
    color: #ff4444;
    padding: 12px 16px;
    margin: 16px;
    font-size: 11px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .error-icon {
    font-weight: bold;
  }

  .form-fields {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .field label {
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.1em;
    opacity: 0.7;
  }

  .field input {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    padding: 12px 14px;
    font-family: inherit;
    font-size: 13px;
    outline: none;
    transition: border-color 0.2s;
  }

  .field input:focus {
    border-color: white;
  }

  .field input::placeholder {
    color: rgba(255, 255, 255, 0.3);
  }

  .field input:disabled {
    opacity: 0.5;
  }

  .form-actions {
    padding: 0 20px 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .submit-btn {
    background: white;
    color: black;
    border: none;
    padding: 14px 20px;
    font-family: inherit;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 0.1em;
    cursor: pointer;
    transition: all 0.2s;
  }

  .submit-btn:hover:not(:disabled) {
    background: #00ff00;
    color: black;
  }

  .submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .loading-dots::after {
    content: '';
    animation: dots 1s steps(4, end) infinite;
  }

  @keyframes dots {
    0% { content: ''; }
    25% { content: '.'; }
    50% { content: '..'; }
    75% { content: '...'; }
    100% { content: ''; }
  }

  .toggle-btn {
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.6);
    font-family: inherit;
    font-size: 11px;
    cursor: pointer;
    padding: 8px;
    transition: color 0.2s;
  }

  .toggle-btn:hover:not(:disabled) {
    color: white;
  }

  .form-footer {
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    padding: 12px 20px;
  }

  .security-notice {
    font-size: 9px;
    letter-spacing: 0.1em;
    opacity: 0.5;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .lock-icon {
    color: #00ff00;
  }

  /* Corner decorations */
  .corner {
    position: absolute;
    width: 20px;
    height: 20px;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .top-left {
    top: 20px;
    left: 20px;
    border-right: none;
    border-bottom: none;
  }

  .top-right {
    top: 20px;
    right: 20px;
    border-left: none;
    border-bottom: none;
  }

  .bottom-left {
    bottom: 20px;
    left: 20px;
    border-right: none;
    border-top: none;
  }

  .bottom-right {
    bottom: 20px;
    right: 20px;
    border-left: none;
    border-top: none;
  }
</style>
