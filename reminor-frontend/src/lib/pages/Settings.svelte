<script>
  import { settings, currentUser } from '../stores.js';
  import { t, locale } from '../i18n.js';
  import { importDiaryFiles, rebuildMemory, downloadBackupZip, triggerKnowledgeAnalysis, getLLMConfigFromServer, saveLLMConfigToServer, migrateLLMConfigToServer, updateLanguage } from '../api.js';
  import { logout, saveTokens } from '../auth.js';


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
        'moonshotai/kimi-k2-instruct-0905',
        'openai/gpt-oss-120b',
        'openai/gpt-oss-20b',
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
      models: ['gemini-3-pro-preview', 'gemini-3-flash-preview', 'gemini-2.5-flash-preview-04-17', 'gemini-2.0-flash']
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
  let isSaving = false;
  let testResult = null;
  let hasStoredKey = false;
  let apiKeyPreview = '';

  // Load saved config from server (+ one-time migration from localStorage)
  async function loadLLMConfig() {
    try {
      // Try one-time migration from localStorage
      await migrateLLMConfigToServer();

      // Load from server
      const config = await getLLMConfigFromServer();
      if (config) {
        selectedProvider = config.provider || 'groq';
        selectedModel = config.model || providers.find(p => p.id === selectedProvider)?.models[0] || 'llama-3.3-70b-versatile';
        hasStoredKey = config.has_api_key || false;
        apiKeyPreview = config.api_key_preview || '';
        apiKey = '';  // Never populate the actual key
      }
    } catch (e) {
      console.error('Error loading LLM config:', e);
    }
  }

  // Save config to server
  async function saveLLMConfig() {
    isSaving = true;
    testResult = null;
    try {
      const result = await saveLLMConfigToServer(
        selectedProvider,
        selectedModel,
        apiKey.trim() || null  // Only send key if user entered a new one
      );
      hasStoredKey = result.has_api_key || false;
      apiKeyPreview = result.api_key_preview || '';
      apiKey = '';  // Clear input after save
      testResult = { success: true, message: $t('settings.saved_success') };
    } catch (e) {
      testResult = { success: false, message: e.message || $t('settings.save_error') };
    } finally {
      isSaving = false;
    }
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

  // Save LLM config (modal save button)
  async function saveAndClose() {
    if (!apiKey.trim() && !hasStoredKey) {
      testResult = { success: false, message: $t('settings.enter_api_key') };
      return;
    }

    await saveLLMConfig();
    if (testResult?.success) {
      setTimeout(() => closeLLMModal(), 1000);
    }
  }

  // Close modal
  function closeLLMModal() {
    showLLMModal = false;
    testResult = null;
    apiKey = '';  // Clear input when closing
  }

  // Reload config when user changes
  $: if ($currentUser) {
    loadLLMConfig();
  }

  let currentLanguage = 'it';
  let languageChanging = false;

  // Initialize from locale store
  locale.subscribe(v => currentLanguage = v);

  async function changeLanguage(newLang) {
    if (newLang === currentLanguage || languageChanging) return;
    languageChanging = true;
    try {
      const result = await updateLanguage(newLang);
      // Update locale store
      locale.set(newLang);
      // Save new tokens if returned
      if (result.access_token && result.refresh_token) {
        saveTokens(result.access_token, result.refresh_token);
      }
    } catch (e) {
      console.error('Error changing language:', e);
    } finally {
      languageChanging = false;
    }
  }

  let autoSaveValue = 'ON';
  $: settingsItems = [
    { id: 'theme', label: $t('settings.theme'), value: 'Notte', icon: 'dark_mode' },
    { id: 'font', label: $t('settings.font'), value: 'JetBrains Mono', icon: 'text_fields' },
    { id: 'llm', label: $t('settings.llm_provider'), value: selectedProvider.toUpperCase(), icon: 'smart_toy', action: () => showLLMModal = true },
    { id: 'autoSave', label: $t('settings.autosave'), value: autoSaveValue, icon: 'save' },
    { id: 'help', label: $t('settings.guide'), value: '', icon: 'help_outline', hasArrow: true },
  ];

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
        autoSaveValue = autoSaveValue === 'ON' ? 'OFF' : 'ON';
      }
    } else if (e.key === 'Escape' && showLLMModal) {
      closeLLMModal();
    }
  }

  function handleItemClick(item, index) {
    selectedIndex = index;
    if (item.action) {
      item.action();
    } else if (item.id === 'autoSave') {
      autoSaveValue = autoSaveValue === 'ON' ? 'OFF' : 'ON';
    }
  }

  async function save() {
    await saveLLMConfig();
    if (testResult?.success) {
      alert($t('settings.settings_saved'));
    }
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
      const result = await importDiaryFiles(selectedFiles);
      importResult = result;

      if (result.imported > 0) {
        selectedFiles = [];
      }
    } catch (e) {
      importError = e.message || $t('settings.import_error');
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
      const blob = await downloadBackupZip();

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
      exportError = e.message || $t('settings.export_error');
    } finally {
      isExporting = false;
    }
  }

  // Maintenance state
  let isRebuilding = false;
  let isAnalyzing = false;

  async function handleRebuild() {
    if (isRebuilding) return;
    if (!confirm($t('settings.rebuild_confirm'))) return;

    isRebuilding = true;
    try {
      await rebuildMemory();
      alert($t('settings.rebuild_success'));
    } catch (e) {
      alert($t('settings.rebuild_error') + ': ' + e.message);
    } finally {
      isRebuilding = false;
    }
  }

  async function handleAnalysis() {
    if (isAnalyzing) return;
    if (!confirm($t('settings.knowledge_confirm'))) return;

    isAnalyzing = true;
    try {
      await triggerKnowledgeAnalysis();
      alert($t('settings.knowledge_started'));
    } catch (e) {
      alert($t('settings.analysis_error') + ': ' + e.message);
    } finally {
      isAnalyzing = false;
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
        <h1 class="title">{$t('settings.title')}</h1>
      </div>
      {#if $currentUser}
        <div class="user-info">
          <span class="user-email">{$currentUser.email}</span>
        </div>
      {/if}
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
      <div class="setting-item">
        <span class="setting-label">{$t('settings.language')}</span>
        <div class="lang-toggle">
          <button class="lang-opt {currentLanguage === 'it' ? 'active' : ''}" on:click={() => changeLanguage('it')} disabled={languageChanging}>IT</button>
          <button class="lang-opt {currentLanguage === 'en' ? 'active' : ''}" on:click={() => changeLanguage('en')} disabled={languageChanging}>EN</button>
        </div>
      </div>
    </div>

    <!-- Import/Export Row -->
    <div class="data-row">
      <!-- Import Section -->
      <div class="import-section">
        <div class="section-header">
          <span class="section-icon">upload_file</span>
          <span class="section-title">{$t('settings.import_diary')}</span>
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
            <p class="drop-text">{$t('settings.drag_files')}</p>
            <p class="drop-hint">{$t('settings.or')}</p>
            <label class="file-select-btn">
              <input type="file" accept=".txt" multiple on:change={handleFileSelect} hidden />
              {$t('settings.browse_files')}
            </label>
            <p class="drop-formats">{$t('settings.formats')}</p>
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
                {$t('settings.cancel')}
              </button>
              <button class="import-btn" on:click={doImport} disabled={isImporting}>
                {#if isImporting}
                  <span class="spinner"></span>
                  {$t('settings.importing')}
                {:else}
                  <span class="btn-icon">cloud_upload</span>
                  {$t('settings.import')} {selectedFiles.length} FILE
                {/if}
              </button>
            </div>
          {/if}
        </div>

        {#if importResult}
          <div class="result-box success">
            <span class="result-icon">check_circle</span>
            <div class="result-text">
              <strong>{$t('settings.import_complete')}</strong>
              <p>{$t('settings.imported_skipped', { imported: importResult.imported, skipped: importResult.skipped })}</p>
            </div>
          </div>
        {/if}

        {#if importError}
          <div class="result-box error">
            <span class="result-icon">error</span>
            <div class="result-text">
              <strong>{$t('settings.error')}</strong>
              <p>{importError}</p>
            </div>
          </div>
        {/if}
      </div>

      <!-- Export Section -->
      <div class="export-section">
        <div class="section-header">
          <span class="section-icon">download</span>
          <span class="section-title">{$t('settings.export_backup')}</span>
        </div>

        <div class="export-info">
          <p>{$t('settings.export_info')}</p>
        </div>

        <button class="export-btn" on:click={doExport} disabled={isExporting}>
          {#if isExporting}
            <span class="spinner"></span>
            {$t('settings.exporting')}
          {:else}
            <span class="btn-icon">archive</span>
            {$t('settings.download_zip')}
          {/if}
        </button>

        {#if exportSuccess}
          <div class="result-box success">
            <span class="result-icon">check_circle</span>
            <span>{$t('settings.export_started')}</span>
          </div>
        {/if}

        {#if exportError}
          <div class="result-box error">
            <span class="result-icon">error</span>
            <span>{exportError}</span>
          </div>
        {/if}
      </div>
    </div>

    <!-- Maintenance Section (full width) -->
    <div class="maintenance-section">
      <div class="section-header">
        <span class="section-icon">build</span>
        <span class="section-title">{$t('settings.maintenance')}</span>
      </div>

      <div class="maintenance-actions">
        <div class="maintenance-item">
          <button class="maintenance-btn" on:click={handleRebuild} disabled={isRebuilding}>
            {#if isRebuilding}
              <span class="spinner"></span>
              {$t('settings.rebuilding')}
            {:else}
              <span class="btn-icon">memory</span>
              {$t('settings.rebuild_memory')}
            {/if}
          </button>
          <p class="maintenance-desc">{$t('settings.rebuild_desc')}</p>
        </div>

        <div class="maintenance-item">
          <button class="maintenance-btn" on:click={handleAnalysis} disabled={isAnalyzing}>
            {#if isAnalyzing}
              <span class="spinner"></span>
              {$t('settings.analyzing')}
            {:else}
              <span class="btn-icon">psychology</span>
              {$t('settings.update_knowledge')}
            {/if}
          </button>
          <p class="maintenance-desc">{$t('settings.knowledge_desc')}</p>
        </div>
      </div>
      <p class="maintenance-note">{$t('settings.maintenance_auto_note')}</p>
    </div>

    <!-- Save Button -->
    <div class="save-section">
      <button class="save-btn" on:click={save}>
        <span class="icon">save</span>
        {$t('settings.save_settings')}
      </button>
    </div>
  </div>
</div>

<!-- LLM Configuration Modal -->
{#if showLLMModal}
  <div class="modal-overlay" on:click={() => closeLLMModal()}>
    <div class="modal" on:click|stopPropagation>
      <div class="modal-header">
        <span class="modal-icon">smart_toy</span>
        <h2>{$t('settings.llm_config')}</h2>
        <button class="modal-close" on:click={() => closeLLMModal()}>×</button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label for="provider">{$t('settings.provider')}</label>
          <select id="provider" bind:value={selectedProvider} on:change={handleProviderChange}>
            {#each providers as provider}
              <option value={provider.id}>{provider.name}</option>
            {/each}
          </select>
        </div>

        <div class="form-group">
          <label for="model">{$t('settings.model')}</label>
          <select id="model" bind:value={selectedModel}>
            {#each availableModels as model}
              <option value={model}>{model}</option>
            {/each}
          </select>
        </div>

        <div class="form-group">
          <label for="apikey">{$t('settings.api_key')}</label>
          <input
            type="password"
            id="apikey"
            bind:value={apiKey}
            placeholder={hasStoredKey ? $t('settings.key_placeholder_saved', { preview: apiKeyPreview }) : $t('settings.key_placeholder_new')}
          />
          <p class="hint">{hasStoredKey ? $t('settings.key_saved_hint') : $t('settings.key_save_hint')}</p>
        </div>

        {#if testResult}
          <div class="test-result" class:success={testResult.success} class:error={!testResult.success}>
            <span class="result-icon">{testResult.success ? 'check_circle' : 'error'}</span>
            <span>{testResult.message}</span>
          </div>
        {/if}
      </div>

      <div class="modal-footer">
        <button class="modal-btn secondary" on:click={() => closeLLMModal()}>
          {$t('settings.modal_cancel')}
        </button>
        <button class="modal-btn primary" on:click={saveAndClose} disabled={isSaving}>
          {#if isSaving}
            <span class="spinner"></span>
          {:else}
            <span class="btn-icon">save</span>
          {/if}
          {$t('settings.modal_save')}
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
    min-height: 0;
  }

  .settings-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 32px 24px;
    overflow-y: auto;
    min-height: 0;
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

  .item-icon, .section-icon, .drop-icon, .btn-icon, .result-icon, .modal-icon, .icon {
    font-family: 'Material Symbols Outlined';
    font-weight: normal;
    font-style: normal;
    font-size: 24px;  /* Preferred icon size */
    display: inline-block;
    line-height: 1;
    text-transform: none;
    letter-spacing: normal;
    word-wrap: normal;
    white-space: nowrap;
    direction: ltr;

    /* Support for all WebKit browsers. */
    -webkit-font-smoothing: antialiased;
    /* Support for Safari and Chrome. */
    text-rendering: optimizeLegibility;

    /* Support for Firefox. */
    -moz-osx-font-smoothing: grayscale;

    /* Support for IE. */
    font-feature-settings: 'liga';
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
    /* max-width: 500px; */ /* Removed max-width to let it expand */
    display: flex;
    /* flex-direction: column; */ /* Changed to row/wrap for better space usage */
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 24px;
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
    /* Allow items to flex */
    flex: 1 1 200px; /* Grow, shrink, base width */
    min-width: 200px;
  }

  .setting-label {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.05em;
    flex: 1;
  }

  .lang-toggle {
    display: flex;
    gap: 0;
  }

  .lang-opt {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: rgba(255, 255, 255, 0.6);
    font-family: inherit;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.1em;
    padding: 5px 14px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .lang-opt:first-child {
    border-right: none;
  }

  .lang-opt.active {
    background: white;
    color: black;
    border-color: white;
  }

  .lang-opt:hover:not(.active):not(:disabled) {
    border-color: rgba(255, 255, 255, 0.6);
    color: white;
  }

  .lang-opt:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* ... rest of styles ... */

  /* Sections */
  .import-section, .export-section {
    width: 100%;
    margin-bottom: 0;
    flex-shrink: 0;
    flex: 1 1 300px;
  }

  .maintenance-section {
    width: 100%;
    margin-bottom: 24px;
    flex-shrink: 0;
  }
  
  /* User info in header */
  .user-info {
    margin-top: 8px;
    font-size: 11px;
    opacity: 0.6;
    font-family: 'JetBrains Mono', monospace;
  }
  
  /* Maintenance Section */
  .maintenance-actions {
    display: flex;
    flex-direction: row;
    gap: 24px;
  }

  .maintenance-btn {
    padding: 12px 16px;
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
    justify-content: center;
    gap: 8px;
    width: 100%;
  }

  .maintenance-btn:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.1);
  }

  .maintenance-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .maintenance-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex: 1 1 0;
  }

  .maintenance-desc {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.5);
    line-height: 1.4;
    margin: 0;
    padding: 0 4px;
  }

  .maintenance-note {
    font-size: 10px;
    color: rgba(100, 255, 100, 0.6);
    margin: 4px 0 0 0;
    padding: 0 4px;
    font-style: italic;
  }

  .settings-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    /* align-items: center; */ /* Changed to stretch/start */
    padding: 32px 40px; /* Increased side padding */
    overflow-y: auto;
    min-height: 0;
    max-width: 1200px; /* Max width for large screens */
    margin: 0 auto; /* Center the container */
    width: 100%;
    box-sizing: border-box;
  }

  /* Layout: Import/Export row (2 columns) */
  .data-row {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    width: 100%;
    margin-bottom: 24px;
    align-items: flex-start;
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
