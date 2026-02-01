<script>
  import { onMount, onDestroy } from 'svelte';
  import { currentUser, chatMessages, isLoading } from '../stores.js';
  import { sendChatMessage, clearChatHistory } from '../api.js';

  let inputText = '';
  let messagesContainer;

  // Initialize with welcome message
  if ($chatMessages.length === 0) {
    chatMessages.set([
      {
        role: 'ai',
        content: 'Ciao! Sono il tuo assistente personale. Posso aiutarti a esplorare i tuoi pensieri, cercare nei tuoi diari o semplicemente conversare. Come posso aiutarti oggi?'
      }
    ]);
  }

  async function sendMessage() {
    if (!inputText.trim() || $isLoading) return;

    const userMessage = inputText.trim();
    inputText = '';

    chatMessages.update(msgs => [...msgs, { role: 'user', content: userMessage }]);

    try {
      isLoading.set(true);
      const response = await sendChatMessage(userMessage);
      chatMessages.update(msgs => [...msgs, { role: 'ai', content: response.response }]);
    } catch (e) {
      const errorMsg = e.message || 'Errore sconosciuto';
      chatMessages.update(msgs => [...msgs, {
        role: 'ai',
        content: errorMsg,
        isError: true
      }]);
    } finally {
      isLoading.set(false);
    }

    setTimeout(() => {
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }, 100);
  }

  function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }
</script>

<div class="chat-container">
  <div class="chat-box">
    <!-- Chat Header -->
    <div class="chat-header">
      <div class="header-left">
        <span class="icon">psychology</span>
        <span class="header-title">AI_THOUGHT_PROCESSOR // SESSION_042</span>
      </div>
      <div class="header-right">
        <span class="window-btn"></span>
        <span class="window-btn filled"></span>
      </div>
    </div>

    <!-- Messages Area -->
    <div class="messages-area" bind:this={messagesContainer}>
      {#each $chatMessages as message}
        <div class="message {message.role}" class:error={message.isError}>
          <div class="message-label">
            {#if message.role === 'ai'}
              <span class="dot">○</span> {message.isError ? 'SYSTEM_ERROR' : 'SYSTEM_AI'}
            {:else}
              USER_01 <span class="dot">●</span>
            {/if}
          </div>
          <div class="message-content">
            <p>{message.content}</p>
          </div>
        </div>
      {/each}

      {#if $isLoading}
        <div class="message ai">
          <div class="message-label">
            <span class="dot">○</span> SYSTEM_AI
          </div>
          <div class="message-content">
            <p class="loading">Elaborazione in corso...</p>
          </div>
        </div>
      {/if}
    </div>

    <!-- Input Area -->
    <div class="input-area">
      <div class="input-box">
        <div class="input-label">INPUT_TERMINAL</div>
        <div class="input-row">
          <span class="prompt">&gt;</span>
          <textarea
            bind:value={inputText}
            on:keydown={handleKeydown}
            placeholder="Digita un comando o una domanda..."
            spellcheck="false"
            rows="1"
          ></textarea>
        </div>
      </div>
      <button class="send-btn" on:click={sendMessage} disabled={$isLoading}>
        INVIA <span class="arrow">→</span>
      </button>
    </div>
  </div>
</div>

<style>
  .chat-container {
    display: flex;
    padding: 16px;
    height: calc(100vh - 80px);
    box-sizing: border-box;
  }

  .chat-box {
    flex: 1;
    display: flex;
    flex-direction: column;
    border: 2px solid white;
    background: black;
    max-height: 100%;
  }

  .chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid white;
    flex-shrink: 0;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .icon {
    font-family: 'Material Symbols Outlined';
    font-size: 18px;
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }

  .header-title {
    font-size: 11px;
    letter-spacing: 0.15em;
  }

  .header-right {
    display: flex;
    gap: 8px;
  }

  .window-btn {
    width: 12px;
    height: 12px;
    border: 1px solid white;
  }

  .window-btn.filled {
    background: white;
  }

  .messages-area {
    flex: 1 1 0;
    overflow-y: auto;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .message {
    display: flex;
    flex-direction: column;
    max-width: 80%;
  }

  .message.ai {
    align-self: flex-start;
  }

  .message.user {
    align-self: flex-end;
  }

  .message-label {
    font-size: 10px;
    letter-spacing: 0.1em;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .message.ai .message-label {
    padding-left: 8px;
  }

  .message.user .message-label {
    justify-content: flex-end;
    padding-right: 8px;
  }

  .dot {
    font-size: 12px;
  }

  .message-content {
    border: 1px solid white;
    padding: 16px;
    background: black;
    overflow-wrap: break-word;
    word-wrap: break-word;
  }

  .message.user .message-content {
    border-style: dashed;
  }

  .message-content p {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
  }

  .message-content p.loading {
    opacity: 0.5;
  }

  .message.error .message-content {
    border-color: #f87171;
    background: rgba(248, 113, 113, 0.05);
  }

  .message.error .message-label {
    color: #f87171;
  }

  .input-area {
    display: flex;
    align-items: flex-end;
    gap: 16px;
    padding: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    flex-shrink: 0;
  }

  .input-box {
    flex: 1;
    border: 1px solid white;
    padding: 16px;
    position: relative;
  }

  .input-label {
    position: absolute;
    top: -8px;
    left: 12px;
    background: black;
    padding: 0 8px;
    font-size: 9px;
    letter-spacing: 0.15em;
    opacity: 0.6;
  }

  .input-row {
    display: flex;
    align-items: flex-start;
    gap: 8px;
  }

  .prompt {
    font-size: 14px;
    opacity: 0.5;
    font-weight: bold;
  }

  textarea {
    flex: 1;
    background: transparent;
    border: none;
    color: white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    resize: none;
    outline: none;
    min-height: 24px;
  }

  textarea::placeholder {
    color: rgba(255, 255, 255, 0.3);
  }

  .send-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 16px 24px;
    border: 2px solid white;
    background: transparent;
    color: white;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 0.1em;
    cursor: pointer;
    transition: background-color 0.1s, color 0.1s;
  }

  .send-btn:hover {
    background: white;
    color: black;
  }

  .send-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .arrow {
    font-size: 16px;
  }
</style>
