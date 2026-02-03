<script>
  import { currentUser, currentPage, selectedDate } from '../stores.js';
  import { searchEntries } from '../api.js';
  import { t } from '../i18n.js';

  let query = '';
  let results = [];
  let isSearching = false;
  let hasSearched = false;

  async function search() {
    if (!query.trim() || isSearching) return;

    try {
      isSearching = true;
      hasSearched = true;
      const data = await searchEntries(query.trim());
      results = data.results || [];
    } catch (e) {
      console.error('Search failed:', e);
      results = [];
    } finally {
      isSearching = false;
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      search();
    }
  }

  function openEntry(date) {
    selectedDate.set(date);
    currentPage.set('diario');
  }
</script>

<main class="flex-grow flex flex-col items-center p-8 overflow-y-auto">
  <div class="w-full max-w-3xl">
    <header class="text-center mb-12">
      <div class="flex items-center justify-center gap-3 mb-4">
        <span class="material-symbols-outlined text-3xl">search</span>
        <h1 class="text-2xl font-bold tracking-widest">{$t('search.title')}</h1>
      </div>
      <p class="text-[12px] opacity-60 tracking-widest uppercase">
        {$t('search.subtitle')}
      </p>
    </header>

    <!-- Search input -->
    <div class="border-2 border-white p-4 mb-8">
      <div class="flex items-center gap-4">
        <span class="text-white opacity-60 font-bold">&gt;</span>
        <input
          type="text"
          bind:value={query}
          on:keydown={handleKeydown}
          class="flex-grow bg-transparent border-none outline-none text-lg"
          placeholder={$t('search.placeholder')}
          spellcheck="false"
        />
        <button
          class="border border-white px-6 py-2 hover:bg-white hover:text-black transition-all font-bold uppercase text-[11px] tracking-widest"
          on:click={search}
          disabled={isSearching}
        >
          {isSearching ? $t('search.searching') : $t('search.button')}
        </button>
      </div>
    </div>

    <!-- Results -->
    {#if hasSearched}
      <div class="border-t border-white/20 pt-8">
        <div class="flex justify-between items-center mb-6">
          <span class="text-[11px] uppercase tracking-widest opacity-60">
            {$t('search.results')} {results.length}
          </span>
        </div>

        {#if results.length === 0}
          <div class="text-center py-12 opacity-60">
            <span class="material-symbols-outlined text-4xl mb-4 block">search_off</span>
            <p>{$t('search.no_results')}</p>
          </div>
        {:else}
          <div class="space-y-4">
            {#each results as result}
              <button
                class="w-full text-left border border-white/20 p-4 hover:border-white hover:bg-white/5 transition-all"
                on:click={() => openEntry(result.date)}
              >
                <div class="flex justify-between items-start mb-2">
                  <span class="text-[11px] font-bold tracking-widest">{result.date}</span>
                  <span class="text-[10px] opacity-60">{$t('search.score')} {result.score.toFixed(1)}</span>
                </div>
                <p class="text-sm opacity-80 line-clamp-2">{result.content}</p>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  </div>
</main>

<style>
  .material-symbols-outlined {
    font-family: 'Material Symbols Outlined';
    font-variation-settings: 'FILL' 1, 'wght' 400;
  }

  input {
    font-family: 'JetBrains Mono', monospace;
  }

  input::placeholder {
    color: rgba(255, 255, 255, 0.3);
  }

  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
