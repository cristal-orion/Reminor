<script>
  import { settings, currentUser } from '../stores.js';
  import { importDiaryFiles, rebuildMemory, downloadBackupZip } from '../api.js';

  // LLM Providers and Models (LiteLLM format: provider/model)
  const providers = [
    {
      id: 'groq',
      name: 'Groq',
      models: [
        'llama-3.3-70b-versatile',
        'llama-3.1-8b-instant',
        'llama3-8b-8192',
        'meta-llama/llama-4-scout-17b-16e-instruct',
        'meta-llama/llama-4-maverick-17b-128e-instruct',
        'qwen/qwen3-32b',
        'mixtral-8x7b-32768'
      ]
    },
    {
      id: 'openai',
      name: 'OpenAI',
      models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo', 'o1-preview', 'o1-mini']
    },
    {
      id: 'anthropic',
      name: 'Anthropic',
      models: ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229']
    },
    {
      id: 'gemini',
      name: 'Google Gemini',
      models: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
    },
    {
      id: 'mistral',
      name: 'Mistral AI',
      models: ['mistral-large-latest', 'mistral-medium-latest', 'mistral-small-latest', 'codestral-latest']
    },
    {
      id: 'deepseek',
      name: 'DeepSeek',
      models: ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner']
    },
  ];

  // LLM Configuration state
  let showLLMModal = false;
  let selectedProvider = 'groq';
  let selectedModel = 'llama-3.3-70b-versatile';
  let apiKey = '';
  let isTesting = false;
  let testResult = null;

  // Load saved config from localStorage
  function loadLLMConfig() {
    const saved = localStorage.getItem('reminor_llm_config');
    if (saved) {
      try {
        const config = JSON.parse(saved);
        selectedProvider = config.provider || 'groq';
        selectedModel = config.model || 'llama-3.3-70b-versatile';
        apiKey = config.apiKey || '';
      } catch (e) {
        console.error('Error loading LLM config:', e);
      }
    }
  }

  // Save config to localStorage
  function saveLLMConfig() {
    const config = {
      provider: selectedProvider,
      model: selectedModel,
      apiKey: apiKey
    };
    localStorage.setItem('reminor_llm_config', JSON.stringify(config));
  }

  // Get models for selected provider
  $: availableModels = providers.find(p => p.id === selectedProvider)?.models || [];

  // Reset model when provider changes
  function handleProviderChange() {
    const provider = providers.find(p => p.id === selectedProvider);
    if (provider && provider.models.length > 0) {
      selectedModel = provider.models[0];
    }
    testResult = null;
  }

  // Test API connection
  async function testConnection() {
    if (!apiKey.trim()) {
      testResult = { success: false, message: 'Inserisci una API key' };
      return;
    }

    isTesting = true;
    testResult = null;

    try {
      // For now, just save and show success - actual test would require backend endpoint
      saveLLMConfig();
      testResult = { success: true, message: 'Configurazione salvata!' };
    } catch (e) {
      testResult = { success: false, message: e.message || 'Errore di connessione' };
    } finally {
      isTesting = false;
    }
  }

  // Close modal and save
  function closeLLMModal(save = false) {
    if (save && apiKey.trim()) {
      saveLLMConfig();
    }
    showLLMModal = false;
    testResult = null;
  }

  // Initialize
  loadLLMConfig();

  let settingsItems = [
    { id: 'theme', label: 'Tema', value: 'Notte', icon: 'dark_mode' },
    { id: 'font', label: 'Font', value: 'JetBrains Mono', icon: 'text_fields' },
    { id: 'llm', label: 'LLM Provider', value: selectedProvider.toUpperCase(), icon: 'smart_toy', action: () => showLLMModal = true },
    { id: 'autoSave', label: 'AutoSave', value: 'ON', icon: 'save' },
    { id: 'help', label: 'Guida', value: '', icon: 'help_outline', hasArrow: true },
  ];

  // Update LLM display value when provider changes
  $: settingsItems = settingsItems.map(item =>
    item.id === 'llm' ? { ...item, value: selectedProvider.toUpperCase() } : item
  );

  let selectedIndex = 0;

  // Import state
  let isDragging = false;
  let selectedFiles = [];
  let isImporting = false;
  let importResult = null;
  let importError = null;

  function handleKeydown(e) {
    if (showLLMModal) return; // Ignore when modal is open

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = (selectedIndex + 1) % settingsItems.length;
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = (selectedIndex - 1 + settingsItems.length) % settingsItems.length;
    } else if (e.key === 'Enter') {
      const item = settingsItems[selectedIndex];
      if (item.action) {
        item.action();
      } else if (item.id === 'autoSave') {
        item.value = item.value === 'ON' ? 'OFF' : 'ON';
        settingsItems = [...settingsItems];
      }
    } else if (e.key === 'Escape' && showLLMModal) {
      closeLLMModal(false);
    }
  }

  function handleItemClick(item, index) {
    selectedIndex = index;
    if (item.action) {
      item.action();
    } else if (item.id === 'autoSave') {
      item.value = item.value === 'ON' ? 'OFF' : 'ON';
      settingsItems = [...settingsItems];
    }
  }

  function save() {
    saveLLMConfig();
    alert('Impostazioni salvate!');
  }

  // Drag & Drop handlers
  function handleDragEnter(e) {
    e.preventDefault();
    isDragging = true;
  }

  function handleDragOver(e) {
    e.preventDefault();
    isDragging = true;
  }

  function handleDragLeave(e) {
    e.preventDefault();
    isDragging = false;
  }

  function handleDrop(e) {
    e.preventDefault();
    isDragging = false;

    const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.txt'));
    if (files.length > 0) {
      selectedFiles = [...selectedFiles, ...files];
      importResult = null;
      importError = null;
    }
  }

  function handleFileSelect(e) {
    const files = Array.from(e.target.files).filter(f => f.name.endsWith('.txt'));
    if (files.length > 0) {
      selectedFiles = [...selectedFiles, ...files];
      importResult = null;
      importError = null;
    }
  }

  function removeFile(index) {
    selectedFiles = selectedFiles.filter((_, i) => i !== index);
  }

  function clearFiles() {
    selectedFiles = [];
    importResult = null;
    importError = null;
  }

  async function doImport() {
    if (selectedFiles.length === 0 || isImporting) return;

    isImporting = true;
    importError = null;
    importResult = null;

    try {
      const result = await importDiaryFiles($currentUser, selectedFiles);
      importResult = result;

      if (result.imported > 0) {
        selectedFiles = [];
      }
    } catch (e) {
      importError = e.message || 'Errore durante l\'import';
    } finally {
      isImporting = false;
    }
  }

  // Export/Backup state
  let isExporting = false;
  let exportError = null;
  let exportSuccess = false;

  async function doExport() {
    if (isExporting) return;

    isExporting = true;
    exportError = null;
    exportSuccess = false;

    try {
      const blob = await downloadBackupZip($currentUser);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const date = new Date().toISOString().split('T')[0];
      a.download = `reminor_backup_${date}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      exportSuccess = true;
      setTimeout(() => exportSuccess = false, 3000);
    } catch (e) {
      exportError = e.message || 'Errore durante l\'export';
    } finally {
      isExporting = false;
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="settings-page">
  <div class="settings-container">
    <!-- Page Header -->
    <div class="page-header">
      <div class="title-row">
        <span class="icon">settings</span>
        <h1 class="title">IMPOSTAZIONI</h1>
      </div>
    </div>

    <!-- Settings List (moved to top for better visibility) -->
    <div class="settings-list">
      {#each settingsItems as item, index}
        <button
          class="setting-item"
          class:selected={selectedIndex === index}
          class:disabled={item.disabled}
          disabled={item.disabled}
          on:mouseenter={() => !item.disabled && (selectedIndex = index)}
          on:click={() => handleItemClick(item, index)}
        >
          <span class="item-icon">{item.icon}</span>
          <span class="item-label">{item.label}:</span>
          <span class="item-value">
            {#if item.value}
              {item.value}
            {/if}
            {#if item.hasArrow || item.action}
              <span class="arrow">›</span>
            {/if}
          </span>
        </button>
      {/each}
    </div>

    <!-- Import Section -->
    <div class="import-section">
      <div class="section-header">
        <span class="section-icon">upload_file</span>
        <span class="section-title">IMPORTA DIARIO</span>
      </div>

      <div
        class="drop-zone"
        class:dragging={isDragging}
        on:dragenter={handleDragEnter}
        on:dragover={handleDragOver}
        on:dragleave={handleDragLeave}
        on:drop={handleDrop}
      >
        {#if selectedFiles.length === 0}
          <span class="drop-icon">folder_open</span>
          <p class="drop-text">Trascina qui i tuoi file .txt</p>
          <p class="drop-hint">oppure</p>
          <label class="file-select-btn">
            <input type="file" accept=".txt" multiple on:change={handleFileSelect} hidden />
            SFOGLIA FILE
          </label>
          <p class="drop-formats">Formati: 2024-01-15.txt, 15-01-2024.txt</p>
        {:else}
          <div class="files-list">
            {#each selectedFiles as file, index}
              <div class="file-item">
                <span class="file-icon">description</span>
                <span class="file-name">{file.name}</span>
                <button class="file-remove" on:click={() => removeFile(index)}>×</button>
              </div>
            {/each}
          </div>

          <div class="import-actions">
            <button class="clear-btn" on:click={clearFiles} disabled={isImporting}>
              ANNULLA
            </button>
            <button class="import-btn" on:click={doImport} disabled={isImporting}>
              {#if isImporting}
                <span class="spinner"></span>
                IMPORTANDO...
              {:else}
                <span class="btn-icon">cloud_upload</span>
                IMPORTA {selectedFiles.length} FILE
              {/if}
            </button>
          </div>
        {/if}
      </div>

      {#if importResult}
        <div class="result-box success">
          <span class="result-icon">check_circle</span>
          <div class="result-text">
            <strong>Import completato!</strong>
            <p>{importResult.imported} importati, {importResult.skipped} saltati</p>
          </div>
        </div>
      {/if}

      {#if importError}
        <div class="result-box error">
          <span class="result-icon">error</span>
          <div class="result-text">
            <strong>Errore</strong>
            <p>{importError}</p>
          </div>
        </div>
      {/if}
    </div>

    <!-- Export Section -->
    <div class="export-section">
      <div class="section-header">
        <span class="section-icon">download</span>
        <span class="section-title">ESPORTA BACKUP</span>
      </div>

      <div class="export-info">
        <p>Scarica archivio ZIP con: diario, memoria, knowledge base, emozioni</p>
      </div>

      <button class="export-btn" on:click={doExport} disabled={isExporting}>
        {#if isExporting}
          <span class="spinner"></span>
          ESPORTANDO...
        {:else}
          <span class="btn-icon">archive</span>
          SCARICA BACKUP ZIP
        {/if}
      </button>

      {#if exportSuccess}
        <div class="result-box success">
          <span class="result-icon">check_circle</span>
          <span>Download avviato!</span>
        </div>
      {/if}

      {#if exportError}
        <div class="result-box error">
          <span class="result-icon">error</span>
          <span>{exportError}</span>
        </div>
      {/if}
    </div>

    <!-- Save Button -->
    <div class="save-section">
      <button class="save-btn" on:click={save}>
        <span class="icon">save</span>
        SALVA IMPOSTAZIONI
      </button>
    </div>
  </div>
</div>

<!-- LLM Configuration Modal -->
{#if showLLMModal}
  <div class="modal-overlay" on:click={() => closeLLMModal(false)}>
    <div class="modal" on:click|stopPropagation>
      <div class="modal-header">
        <span class="modal-icon">smart_toy</span>
        <h2>CONFIGURAZIONE LLM</h2>
        <button class="modal-close" on:click={() => closeLLMModal(false)}>×</button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label for="provider">PROVIDER</label>
          <select id="provider" bind:value={selectedProvider} on:change={handleProviderChange}>
            {#each providers as provider}
              <option value={provider.id}>{provider.name}</option>
            {/each}
          </select>
        </div>

        <div class="form-group">
          <label for="model">MODELLO</label>
          <select id="model" bind:value={selectedModel}>
            {#each availableModels as model}
              <option value={model}>{model}</option>
            {/each}
          </select>
        </div>

        <div class="form-group">
          <label for="apikey">API KEY</label>
          <input
            type="password"
            id="apikey"
            bind:value={apiKey}
            placeholder="Inserisci la tua API key..."
          />
          <p class="hint">La key viene salvata localmente nel browser</p>
        </div>

        {#if testResult}
          <div class="test-result" class:success={testResult.success} class:error={!testResult.success}>
            <span class="result-icon">{testResult.success ? 'check_circle' : 'error'}</span>
            <span>{testResult.message}</span>
          </div>
        {/if}
      </div>

      <div class="modal-footer">
        <button class="modal-btn secondary" on:click={() => closeLLMModal(false)}>
          ANNULLA
        </button>
        <button class="modal-btn primary" on:click={testConnection} disabled={isTesting}>
          {#if isTesting}
            <span class="spinner"></span>
          {:else}
            <span class="btn-icon">save</span>
          {/if}
          SALVA
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .settings-page {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }

  .settings-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 32px 24px;
    overflow-y: auto;
    max-height: 100%;
  }

  .page-header {
    text-align: center;
    margin-bottom: 24px;
    flex-shrink: 0;
  }

  .title-row {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .icon {
    font-family: 'Material Symbols Outlined';
    font-size: 28px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }

  .title {
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 0.2em;
    margin: 0;
  }

  /* Settings List */
  .settings-list {
    width: 100%;
    max-width: 500px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 32px;
    flex-shrink: 0;
  }

  .setting-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: transparent;
    color: white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s;
  }

  .setting-item:hover:not(.disabled) {
    border-color: white;
    background: rgba(255, 255, 255, 0.05);
  }

  .setting-item.selected {
    background: white;
    color: black;
  }

  .setting-item.disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .item-icon {
    font-family: 'Material Symbols Outlined';
    font-size: 20px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
    width: 24px;
  }

  .item-label {
    font-weight: bold;
  }

  .item-value {
    margin-left: auto;
    opacity: 0.8;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .arrow {
    opacity: 0.5;
    font-size: 18px;
  }

  /* Sections */
  .import-section, .export-section {
    width: 100%;
    max-width: 500px;
    margin-bottom: 24px;
    flex-shrink: 0;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  }

  .section-icon {
    font-family: 'Material Symbols Outlined';
    font-size: 20px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }

  .section-title {
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 0.15em;
  }

  /* Drop Zone */
  .drop-zone {
    border: 2px dashed rgba(255, 255, 255, 0.3);
    padding: 24px 16px;
    text-align: center;
    transition: all 0.2s;
    min-height: 140px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .drop-zone.dragging {
    border-color: white;
    background: rgba(255, 255, 255, 0.05);
  }

  .drop-icon {
    font-family: 'Material Symbols Outlined';
    font-size: 36px;
    font-variation-settings: 'FILL' 0, 'wght' 400;
    opacity: 0.5;
    margin-bottom: 12px;
  }

  .drop-text {
    font-size: 13px;
    margin: 0 0 6px 0;
  }

  .drop-hint {
    font-size: 11px;
    opacity: 0.5;
    margin: 0 0 10px 0;
  }

  .drop-formats {
    font-size: 10px;
    opacity: 0.4;
    margin: 12px 0 0 0;
  }

  .file-select-btn {
    padding: 8px 16px;
    border: 1px solid white;
    background: transparent;
    color: white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.1em;
    cursor: pointer;
    transition: all 0.15s;
  }

  .file-select-btn:hover {
    background: white;
    color: black;
  }

  .files-list {
    width: 100%;
    max-height: 120px;
    overflow-y: auto;
    margin-bottom: 12px;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    margin-bottom: 4px;
    font-size: 11px;
  }

  .file-icon {
    font-family: 'Material Symbols Outlined';
    font-size: 14px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
    opacity: 0.7;
  }

  .file-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .file-remove {
    background: none;
    border: none;
    color: white;
    opacity: 0.5;
    cursor: pointer;
    font-size: 16px;
    padding: 0 4px;
    line-height: 1;
  }

  .file-remove:hover {
    opacity: 1;
  }

  .import-actions {
    display: flex;
    gap: 10px;
    justify-content: center;
  }

  .clear-btn, .import-btn, .export-btn {
    padding: 10px 16px;
    border: 1px solid white;
    background: transparent;
    color: white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.1em;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .import-btn, .export-btn {
    background: white;
    color: black;
  }

  .import-btn:hover:not(:disabled), .export-btn:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.9);
  }

  .clear-btn:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.1);
  }

  .import-btn:disabled, .clear-btn:disabled, .export-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-icon {
    font-family: 'Material Symbols Outlined';
    font-size: 16px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }

  .spinner {
    width: 14px;
    height: 14px;
    border: 2px solid transparent;
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Export Section */
  .export-info {
    padding: 12px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    margin-bottom: 12px;
  }

  .export-info p {
    margin: 0;
    font-size: 12px;
    opacity: 0.8;
  }

  .export-btn {
    width: 100%;
    justify-content: center;
  }

  /* Result Box */
  .result-box {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px;
    margin-top: 12px;
    border: 1px solid;
    font-size: 12px;
  }

  .result-box.success {
    border-color: #4ade80;
    background: rgba(74, 222, 128, 0.1);
  }

  .result-box.error {
    border-color: #f87171;
    background: rgba(248, 113, 113, 0.1);
  }

  .result-icon {
    font-family: 'Material Symbols Outlined';
    font-size: 20px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }

  .result-box.success .result-icon { color: #4ade80; }
  .result-box.error .result-icon { color: #f87171; }

  .result-text {
    flex: 1;
  }

  .result-text strong {
    display: block;
    margin-bottom: 2px;
  }

  .result-text p {
    margin: 0;
    opacity: 0.8;
    font-size: 11px;
  }

  /* Save Section */
  .save-section {
    margin-top: 24px;
    margin-bottom: 32px;
    flex-shrink: 0;
  }

  .save-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 28px;
    border: 2px solid white;
    background: transparent;
    color: white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 0.15em;
    cursor: pointer;
    transition: all 0.15s;
  }

  .save-btn:hover {
    background: white;
    color: black;
  }

  .save-btn .icon {
    font-size: 20px;
  }

  /* Modal Styles */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 24px;
  }

  .modal {
    background: #0a0a0a;
    border: 2px solid white;
    width: 100%;
    max-width: 480px;
    max-height: 90vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .modal-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 24px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  }

  .modal-icon {
    font-family: 'Material Symbols Outlined';
    font-size: 24px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }

  .modal-header h2 {
    flex: 1;
    margin: 0;
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 0.15em;
  }

  .modal-close {
    background: none;
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
    opacity: 0.6;
    padding: 0;
    line-height: 1;
  }

  .modal-close:hover {
    opacity: 1;
  }

  .modal-body {
    padding: 24px;
    overflow-y: auto;
  }

  .form-group {
    margin-bottom: 20px;
  }

  .form-group label {
    display: block;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
    opacity: 0.7;
  }

  .form-group select,
  .form-group input {
    width: 100%;
    padding: 12px 14px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    background: transparent;
    color: white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
  }

  .form-group select {
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='white' viewBox='0 0 24 24'%3E%3Cpath d='M7 10l5 5 5-5z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
    background-size: 20px;
    padding-right: 40px;
  }

  .form-group select option {
    background: #0a0a0a;
    color: white;
  }

  .form-group input::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }

  .form-group input:focus,
  .form-group select:focus {
    outline: none;
    border-color: white;
  }

  .hint {
    font-size: 10px;
    opacity: 0.5;
    margin: 6px 0 0 0;
  }

  .test-result {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px;
    border: 1px solid;
    font-size: 12px;
  }

  .test-result.success {
    border-color: #4ade80;
    background: rgba(74, 222, 128, 0.1);
  }

  .test-result.success .result-icon { color: #4ade80; }

  .test-result.error {
    border-color: #f87171;
    background: rgba(248, 113, 113, 0.1);
  }

  .test-result.error .result-icon { color: #f87171; }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
  }

  .modal-btn {
    padding: 12px 20px;
    border: 1px solid white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 0.1em;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .modal-btn.secondary {
    background: transparent;
    color: white;
  }

  .modal-btn.secondary:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  .modal-btn.primary {
    background: white;
    color: black;
  }

  .modal-btn.primary:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.9);
  }

  .modal-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
