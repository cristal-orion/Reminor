/**
 * Internationalization module for Reminor Frontend.
 * Simple dictionary-based IT/EN translations.
 */

import { writable, derived } from 'svelte/store';

// ==================== LOCALE STORE ====================

const LOCALE_KEY = 'reminor_language';

function getInitialLocale() {
  try {
    const stored = localStorage.getItem(LOCALE_KEY);
    if (stored === 'it' || stored === 'en') return stored;
  } catch {}
  return 'it';
}

export const locale = writable(getInitialLocale());

// Sync to localStorage
locale.subscribe(($locale) => {
  try {
    localStorage.setItem(LOCALE_KEY, $locale);
  } catch {}
});

// ==================== TRANSLATIONS ====================

const translations = {
  // ---- LOGIN ----
  'login.system_access': { it: 'ACCESSO SISTEMA', en: 'SYSTEM ACCESS' },
  'login.new_user_registration': { it: 'REGISTRAZIONE NUOVO UTENTE', en: 'NEW USER REGISTRATION' },
  'login.enter_credentials': { it: 'Inserisci le credenziali', en: 'Enter your credentials' },
  'login.create_account': { it: 'Crea un nuovo account', en: 'Create a new account' },
  'login.email': { it: 'EMAIL', en: 'EMAIL' },
  'login.password': { it: 'PASSWORD', en: 'PASSWORD' },
  'login.confirm_password': { it: 'CONFERMA PASSWORD', en: 'CONFIRM PASSWORD' },
  'login.name_optional': { it: 'NOME (OPZIONALE)', en: 'NAME (OPTIONAL)' },
  'login.name_placeholder': { it: 'Il tuo nome', en: 'Your name' },
  'login.submit_login': { it: '[ACCEDI]', en: '[LOGIN]' },
  'login.submit_register': { it: '[REGISTRATI]', en: '[REGISTER]' },
  'login.processing': { it: 'ELABORAZIONE', en: 'PROCESSING' },
  'login.toggle_to_register': { it: 'Nuovo utente? Registrati', en: 'New user? Register' },
  'login.toggle_to_login': { it: 'Hai un account? Accedi', en: 'Have an account? Login' },
  'login.security_notice': { it: 'CONNESSIONE SICURA - CRITTOGRAFIA ATTIVA', en: 'SECURE CONNECTION - ENCRYPTION ACTIVE' },
  'login.error_required': { it: 'Email e password richiesti', en: 'Email and password required' },
  'login.error_mismatch': { it: 'Le password non coincidono', en: 'Passwords do not match' },
  'login.error_min_length': { it: 'Password minimo 8 caratteri', en: 'Password minimum 8 characters' },
  'login.error_generic': { it: 'Errore di autenticazione', en: 'Authentication error' },
  'login.language': { it: 'LINGUA', en: 'LANGUAGE' },

  // ---- APP / LOADING ----
  'app.loading': { it: 'INIZIALIZZAZIONE SISTEMA...', en: 'SYSTEM INITIALIZATION...' },

  // ---- FOOTER HINTS ----
  'hint.navigate': { it: 'NAVIGA', en: 'NAVIGATE' },
  'hint.select': { it: 'SELEZIONA', en: 'SELECT' },
  'hint.exit': { it: 'ESCI', en: 'EXIT' },
  'hint.save': { it: 'SALVA', en: 'SAVE' },
  'hint.menu': { it: 'MENU', en: 'MENU' },
  'hint.month': { it: 'MESE', en: 'MONTH' },
  'hint.open': { it: 'APRI', en: 'OPEN' },
  'hint.send': { it: 'INVIA', en: 'SEND' },
  'hint.week': { it: 'SETTIMANA', en: 'WEEK' },
  'hint.diary': { it: 'DIARIO', en: 'DIARY' },
  'hint.confirm': { it: 'CONFERMA', en: 'CONFIRM' },
  'hint.field': { it: 'CAMPO', en: 'FIELD' },

  // ---- HEADER ----
  'header.dashboard': { it: 'DASHBOARD', en: 'DASHBOARD' },
  'header.diary': { it: 'DIARIO', en: 'DIARY' },
  'header.archive': { it: 'ARCHIVIO', en: 'ARCHIVE' },
  'header.chat': { it: 'CHAT', en: 'CHAT' },
  'header.emotions': { it: 'EMOZIONI', en: 'EMOTIONS' },
  'header.stats': { it: 'STATS', en: 'STATS' },
  'header.settings': { it: 'SETTINGS', en: 'SETTINGS' },
  'header.exit': { it: 'EXIT', en: 'EXIT' },
  'header.logout_confirm': { it: 'Sei sicuro di voler uscire?', en: 'Are you sure you want to log out?' },
  'header.system_ready': { it: 'SYSTEM READY', en: 'SYSTEM READY' },

  // ---- HOME ----
  'home.subtitle': { it: 'PERSONAL KNOWLEDGE RETRIEVAL SYSTEM', en: 'PERSONAL KNOWLEDGE RETRIEVAL SYSTEM' },
  'home.new_page': { it: 'NUOVA PAGINA', en: 'NEW PAGE' },
  'home.calendar': { it: 'CALENDARIO', en: 'CALENDAR' },
  'home.search': { it: 'RICERCA', en: 'SEARCH' },
  'home.chat': { it: 'CHAT PENSIERI', en: 'CHAT THOUGHTS' },
  'home.emotions': { it: 'EMOZIONI', en: 'EMOTIONS' },
  'home.statistics': { it: 'STATISTICHE', en: 'STATISTICS' },
  'home.settings': { it: 'IMPOSTAZIONI', en: 'SETTINGS' },

  // ---- DIARY ----
  'diary.placeholder': { it: 'Inizia a scrivere il tuo pensiero...', en: 'Start writing your thought...' },
  'diary.save': { it: 'SALVA [^S]', en: 'SAVE [^S]' },
  'diary.export': { it: 'EXPORT', en: 'EXPORT' },
  'diary.emotions_btn': { it: 'EMOZIONI [F2]', en: 'EMOTIONS [F2]' },
  'diary.saving': { it: 'SAVING...', en: 'SAVING...' },
  'diary.emotions_detected': { it: 'EMOZIONI RILEVATE', en: 'DETECTED EMOTIONS' },
  'diary.insight': { it: 'INSIGHT', en: 'INSIGHT' },
  'diary.energy': { it: 'ENERGIA', en: 'ENERGY' },
  'diary.status': { it: 'STATUS:', en: 'STATUS:' },
  'diary.status_saving': { it: 'SAVING', en: 'SAVING' },
  'diary.status_idle': { it: 'IDLE', en: 'IDLE' },
  'diary.status_saved': { it: 'SAVED:', en: 'SAVED:' },
  'diary.emotions_shortcut': { it: '[F2] EMOZIONI', en: '[F2] EMOTIONS' },

  // ---- CHAT ----
  'chat.title': { it: 'AI_THOUGHT_PROCESSOR // SESSION_042', en: 'AI_THOUGHT_PROCESSOR // SESSION_042' },
  'chat.welcome': {
    it: 'Ciao! Sono il tuo assistente personale. Posso aiutarti a esplorare i tuoi pensieri, cercare nei tuoi diari o semplicemente conversare. Come posso aiutarti oggi?',
    en: 'Hello! I\'m your personal assistant. I can help you explore your thoughts, search through your diaries, or just chat. How can I help you today?'
  },
  'chat.input_label': { it: 'INPUT_TERMINAL', en: 'INPUT_TERMINAL' },
  'chat.placeholder': { it: 'Digita un comando o una domanda...', en: 'Type a command or question...' },
  'chat.send': { it: 'INVIA', en: 'SEND' },
  'chat.processing': { it: 'Elaborazione in corso...', en: 'Processing...' },
  'chat.unknown_error': { it: 'Errore sconosciuto', en: 'Unknown error' },

  // ---- SEARCH ----
  'search.title': { it: 'RICERCA SEMANTICA', en: 'SEMANTIC SEARCH' },
  'search.subtitle': { it: 'Cerca nei tuoi pensieri usando il linguaggio naturale', en: 'Search your thoughts using natural language' },
  'search.placeholder': { it: 'Cosa vuoi cercare?', en: 'What are you looking for?' },
  'search.button': { it: 'CERCA', en: 'SEARCH' },
  'search.searching': { it: 'CERCO...', en: 'SEARCHING...' },
  'search.results': { it: 'RISULTATI:', en: 'RESULTS:' },
  'search.no_results': { it: 'Nessun risultato trovato', en: 'No results found' },
  'search.score': { it: 'SCORE:', en: 'SCORE:' },

  // ---- CALENDAR ----
  'calendar.title': { it: 'CALENDARIO', en: 'CALENDAR' },
  'calendar.prev': { it: 'PREV', en: 'PREV' },
  'calendar.next': { it: 'NEXT', en: 'NEXT' },
  'calendar.weekdays': { it: ['LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB', 'DOM'], en: ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'] },

  // ---- EMOTIONS ----
  'emotions.title': { it: 'EMOZIONI SETTIMANALI', en: 'WEEKLY EMOTIONS' },
  'emotions.loading': { it: 'CARICAMENTO...', en: 'LOADING...' },
  'emotions.stability': { it: 'INDICE STABILITÀ', en: 'STABILITY INDEX' },
  'emotions.weekdays': { it: ['LUN', 'MAR', 'MER', 'GIO', 'VEN', 'SAB', 'DOM'], en: ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'] },
  'emotions.log': { it: 'LOG', en: 'LOG' },
  'emotions.pending': { it: 'ATTESA', en: 'PENDING' },
  'emotions.log_now': { it: 'SCRIVI ORA', en: 'LOG NOW' },
  'emotions.total_entries': { it: 'VOCI TOTALI', en: 'TOTAL ENTRIES' },
  'emotions.dominant_mood': { it: 'MOOD DOMINANTE', en: 'DOMINANT MOOD' },
  'emotions.avg_intensity': { it: 'INTENSITÀ MEDIA', en: 'AVG INTENSITY' },
  'emotions.streak': { it: 'STREAK', en: 'STREAK' },
  'emotions.days': { it: 'GIORNI', en: 'DAYS' },
  'emotions.tired': { it: 'STANCO', en: 'TIRED' },
  'emotions.calm': { it: 'CALMO', en: 'CALM' },
  'emotions.energetic': { it: 'ENERGIA', en: 'ENERGY' },
  'emotions.week': { it: 'SETTIMANA', en: 'WEEK' },

  // ---- STATISTICS ----
  'stats.title': { it: '--- STATISTICHE PERSONALI ---', en: '--- PERSONAL STATISTICS ---' },
  'stats.subtitle': { it: 'SISTEMA OPERATIVO DIARIO DI BORDO // USER: ADMIN', en: 'DIARY OPERATING SYSTEM // USER: ADMIN' },
  'stats.density': { it: 'DENSITÀ MEMORIA', en: 'MEMORY DENSITY' },
  'stats.writing': { it: 'SCRITTURA', en: 'WRITING' },
  'stats.dominant_mood': { it: 'MOOD PREVALENTE', en: 'DOMINANT MOOD' },
  'stats.system_profile': { it: 'PROFILO SISTEMA', en: 'SYSTEM PROFILE' },
  'stats.last_days': { it: 'ULTIMI 84 GIORNI', en: 'LAST 84 DAYS' },
  'stats.less': { it: 'MENO', en: 'LESS' },
  'stats.more': { it: 'PIÙ', en: 'MORE' },
  'stats.total_volume': { it: 'VOLUME TOTALE', en: 'TOTAL VOLUME' },
  'stats.daily_average': { it: 'MEDIA GIORNALIERA', en: 'DAILY AVERAGE' },
  'stats.trend': { it: 'TREND', en: 'TREND' },
  'stats.detected_in': { it: 'RILEVATO NEL', en: 'DETECTED IN' },
  'stats.of_texts': { it: 'DEI TESTI', en: 'OF TEXTS' },
  'stats.system_init': { it: 'SYSTEM_ANALYSIS_INIT', en: 'SYSTEM_ANALYSIS_INIT' },
  'stats.reading_pattern': { it: 'READING_USER_PATTERN...', en: 'READING_USER_PATTERN...' },
  'stats.analysis_unavailable': { it: 'ANALISI SISTEMA NON DISPONIBILE. ELABORAZIONE IN CORSO...', en: 'SYSTEM ANALYSIS NOT AVAILABLE. PROCESSING...' },

  // ---- SETTINGS ----
  'settings.title': { it: 'IMPOSTAZIONI', en: 'SETTINGS' },
  'settings.import_diary': { it: 'IMPORTA DIARIO', en: 'IMPORT DIARY' },
  'settings.export_backup': { it: 'ESPORTA BACKUP', en: 'EXPORT BACKUP' },
  'settings.maintenance': { it: 'MANUTENZIONE SISTEMA', en: 'SYSTEM MAINTENANCE' },
  'settings.theme': { it: 'Tema', en: 'Theme' },
  'settings.font': { it: 'Font', en: 'Font' },
  'settings.llm_provider': { it: 'LLM Provider', en: 'LLM Provider' },
  'settings.autosave': { it: 'AutoSave', en: 'AutoSave' },
  'settings.guide': { it: 'Guida', en: 'Guide' },
  'settings.browse_files': { it: 'SFOGLIA FILE', en: 'BROWSE FILES' },
  'settings.cancel': { it: 'ANNULLA', en: 'CANCEL' },
  'settings.import': { it: 'IMPORTA', en: 'IMPORT' },
  'settings.exporting': { it: 'ESPORTANDO...', en: 'EXPORTING...' },
  'settings.download_zip': { it: 'SCARICA BACKUP ZIP', en: 'DOWNLOAD ZIP BACKUP' },
  'settings.rebuild_memory': { it: 'RICOSTRUISCI MEMORIA', en: 'REBUILD MEMORY' },
  'settings.update_knowledge': { it: 'AGGIORNA CONOSCENZA', en: 'UPDATE KNOWLEDGE' },
  'settings.save_settings': { it: 'SALVA IMPOSTAZIONI', en: 'SAVE SETTINGS' },
  'settings.drag_files': { it: 'Trascina qui i tuoi file .txt', en: 'Drag your .txt files here' },
  'settings.or': { it: 'oppure', en: 'or' },
  'settings.formats': { it: 'Formati: 2024-01-15.txt, 15-01-2024.txt', en: 'Formats: 2024-01-15.txt, 15-01-2024.txt' },
  'settings.import_complete': { it: 'Import completato!', en: 'Import complete!' },
  'settings.error': { it: 'Errore', en: 'Error' },
  'settings.rebuild_confirm': {
    it: 'Sei sicuro di voler ricostruire la memoria? Questa operazione potrebbe richiedere del tempo.',
    en: 'Are you sure you want to rebuild memory? This operation may take some time.'
  },
  'settings.rebuild_success': { it: 'Memoria ricostruita con successo!', en: 'Memory rebuilt successfully!' },
  'settings.knowledge_confirm': { it: 'Vuoi avviare l\'analisi della conoscenza?', en: 'Do you want to start knowledge analysis?' },
  'settings.knowledge_started': { it: 'Analisi avviata in background!', en: 'Analysis started in background!' },
  'settings.llm_config': { it: 'CONFIGURAZIONE LLM', en: 'LLM CONFIGURATION' },
  'settings.provider': { it: 'PROVIDER', en: 'PROVIDER' },
  'settings.model': { it: 'MODELLO', en: 'MODEL' },
  'settings.api_key': { it: 'API KEY', en: 'API KEY' },
  'settings.key_saved_hint': {
    it: 'Key salvata sul server, crittografata. Lascia vuoto per mantenere quella attuale.',
    en: 'Key saved on server, encrypted. Leave empty to keep current one.'
  },
  'settings.key_save_hint': {
    it: 'La key verrà salvata sul server, crittografata.',
    en: 'The key will be saved on server, encrypted.'
  },
  'settings.language': { it: 'Lingua', en: 'Language' },
  'settings.language_it': { it: 'Italiano', en: 'Italian' },
  'settings.language_en': { it: 'English', en: 'English' },
  'settings.language_changed': { it: 'Lingua aggiornata!', en: 'Language updated!' },
  'settings.saved_success': { it: 'Configurazione salvata sul server!', en: 'Configuration saved to server!' },
  'settings.save_error': { it: 'Errore nel salvataggio', en: 'Error saving' },
  'settings.enter_api_key': { it: 'Inserisci una API key', en: 'Enter an API key' },
  'settings.settings_saved': { it: 'Impostazioni salvate!', en: 'Settings saved!' },
  'settings.import_error': { it: 'Errore durante l\'import', en: 'Error during import' },
  'settings.imported_skipped': { it: '{imported} importati, {skipped} saltati', en: '{imported} imported, {skipped} skipped' },
  'settings.export_info': { it: 'Scarica archivio ZIP con: diario, memoria, knowledge base, emozioni', en: 'Download ZIP archive with: diary, memory, knowledge base, emotions' },
  'settings.export_started': { it: 'Download avviato!', en: 'Download started!' },
  'settings.export_error': { it: 'Errore durante l\'export', en: 'Error during export' },
  'settings.rebuild_error': { it: 'Errore durante la ricostruzione', en: 'Error during rebuild' },
  'settings.analysis_error': { it: 'Errore durante l\'avvio dell\'analisi', en: 'Error starting analysis' },
  'settings.modal_cancel': { it: 'ANNULLA', en: 'CANCEL' },
  'settings.modal_save': { it: 'SALVA', en: 'SAVE' },
  'settings.key_placeholder_saved': { it: 'Key salvata: {preview}', en: 'Key saved: {preview}' },
  'settings.key_placeholder_new': { it: 'Inserisci la tua API key...', en: 'Enter your API key...' },
  'settings.rebuilding': { it: 'RICOSTRUZIONE...', en: 'REBUILDING...' },
  'settings.analyzing': { it: 'ANALISI IN CORSO...', en: 'ANALYZING...' },
  'settings.importing': { it: 'IMPORTING...', en: 'IMPORTING...' },

  // ---- EMOTION DISPLAY NAMES ----
  // Maps Italian API keys to display names per language
  'emotion.Felice': { it: 'Felice', en: 'Happy' },
  'emotion.Triste': { it: 'Triste', en: 'Sad' },
  'emotion.Arrabbiato': { it: 'Arrabbiato', en: 'Angry' },
  'emotion.Ansioso': { it: 'Ansioso', en: 'Anxious' },
  'emotion.Sereno': { it: 'Sereno', en: 'Calm' },
  'emotion.Stressato': { it: 'Stressato', en: 'Stressed' },
  'emotion.Grato': { it: 'Grato', en: 'Grateful' },
  'emotion.Motivato': { it: 'Motivato', en: 'Motivated' },
  // Lowercase variants (from API data)
  'emotion.felice': { it: 'Felice', en: 'Happy' },
  'emotion.triste': { it: 'Triste', en: 'Sad' },
  'emotion.arrabbiato': { it: 'Arrabbiato', en: 'Angry' },
  'emotion.ansioso': { it: 'Ansioso', en: 'Anxious' },
  'emotion.sereno': { it: 'Sereno', en: 'Calm' },
  'emotion.stressato': { it: 'Stressato', en: 'Stressed' },
  'emotion.grato': { it: 'Grato', en: 'Grateful' },
  'emotion.motivato': { it: 'Motivato', en: 'Motivated' },

  // Short emotion labels (for charts)
  'emotion_short.felice': { it: 'FEL', en: 'JOY' },
  'emotion_short.triste': { it: 'TRI', en: 'SAD' },
  'emotion_short.arrabbiato': { it: 'RAB', en: 'ANG' },
  'emotion_short.ansioso': { it: 'ANS', en: 'ANX' },
  'emotion_short.sereno': { it: 'SER', en: 'CAL' },
  'emotion_short.stressato': { it: 'STR', en: 'STR' },
  'emotion_short.grato': { it: 'GRA', en: 'GRT' },
  'emotion_short.motivato': { it: 'MOT', en: 'MOT' },
};

// ==================== TRANSLATION FUNCTION ====================

/**
 * Derived store: returns a function t(key, params) that resolves translations.
 * Usage in Svelte: $t('login.email')
 */
export const t = derived(locale, ($locale) => {
  return (key, params) => {
    const entry = translations[key];
    if (!entry) return key;

    let text = entry[$locale] || entry['it'] || key;

    // If it's not a string (e.g., an array), return directly
    if (typeof text !== 'string') return text;

    // Simple param interpolation: {name} -> value
    if (params && typeof params === 'object') {
      for (const [k, v] of Object.entries(params)) {
        text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
      }
    }

    return text;
  };
});

/**
 * Get emotion display name from API key.
 * API always returns Italian keys (Felice, Triste, etc.)
 * This maps them to the correct display name for the current locale.
 */
export function getEmotionDisplayName(apiKey, currentLocale) {
  const entry = translations[`emotion.${apiKey}`];
  if (!entry) return apiKey;
  return entry[currentLocale] || entry['it'] || apiKey;
}

/**
 * Get short emotion label for charts.
 */
export function getEmotionShortName(apiKey, currentLocale) {
  const lower = apiKey.toLowerCase();
  const entry = translations[`emotion_short.${lower}`];
  if (!entry) return apiKey.substring(0, 3).toUpperCase();
  return entry[currentLocale] || entry['it'] || apiKey.substring(0, 3).toUpperCase();
}
