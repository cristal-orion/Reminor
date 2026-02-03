"""
Internationalization module for Reminor Backend.
Simple dictionary-based translations for IT/EN.
"""

from typing import Optional

TRANSLATIONS = {
    # ==================== AUTH MESSAGES ====================
    "auth.email_registered": {
        "it": "Email già registrata",
        "en": "Email already registered",
    },
    "auth.invalid_credentials": {
        "it": "Email o password non validi",
        "en": "Invalid email or password",
    },
    "auth.invalid_refresh_token": {
        "it": "Refresh token non valido",
        "en": "Invalid refresh token",
    },
    "auth.invalid_token_type": {
        "it": "Tipo di token non valido",
        "en": "Invalid token type",
    },
    "auth.user_not_found": {
        "it": "Utente non trovato",
        "en": "User not found",
    },
    "auth.credentials_invalid": {
        "it": "Impossibile validare le credenziali",
        "en": "Could not validate credentials",
    },
    "auth.language_updated": {
        "it": "Lingua aggiornata",
        "en": "Language updated",
    },

    # ==================== CHAT MESSAGES ====================
    "chat.api_key_missing": {
        "it": "Errore: API key non configurata per {provider}",
        "en": "Error: API key not configured for {provider}",
    },
    "chat.api_key_invalid": {
        "it": "API key non valida per {provider}. Vai nelle Impostazioni per aggiornare la chiave.",
        "en": "Invalid API key for {provider}. Go to Settings to update the key.",
    },
    "chat.api_key_expired": {
        "it": "API key non valida o scaduta per {provider}. Vai nelle Impostazioni per configurare una nuova chiave.",
        "en": "Invalid or expired API key for {provider}. Go to Settings to configure a new key.",
    },
    "chat.rate_limit": {
        "it": "Rate limit raggiunto per {provider}. Riprova tra poco.",
        "en": "Rate limit reached for {provider}. Try again shortly.",
    },
    "chat.connection_error": {
        "it": "Errore di connessione a {provider}: {error}",
        "en": "Connection error to {provider}: {error}",
    },
    "chat.generic_error": {
        "it": "Errore: {error}",
        "en": "Error: {error}",
    },
    "chat.request_error": {
        "it": "Errore nella richiesta a {provider}: {error}",
        "en": "Request error to {provider}: {error}",
    },
    "chat.related_entries": {
        "it": "Voci correlate",
        "en": "Related entries",
    },

    # ==================== EMOTIONS MESSAGES ====================
    "emotions.api_key_missing": {
        "it": "Per l'analisi delle emozioni, configura una API key nelle impostazioni.",
        "en": "To analyze emotions, configure an API key in settings.",
    },
    "emotions.litellm_unavailable": {
        "it": "LiteLLM non disponibile",
        "en": "LiteLLM not available",
    },
    "emotions.api_key_invalid": {
        "it": "API key non valida per {provider}",
        "en": "Invalid API key for {provider}",
    },
    "emotions.rate_limit": {
        "it": "Rate limit raggiunto per {provider}. Riprova tra poco.",
        "en": "Rate limit reached for {provider}. Try again shortly.",
    },
    "emotions.analysis_error": {
        "it": "Errore durante l'analisi: {error}",
        "en": "Error during analysis: {error}",
    },

    # ==================== DATE FORMATTING ====================
    "date.weekdays": {
        "it": ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"],
        "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    },
    "date.months": {
        "it": ["", "gennaio", "febbraio", "marzo", "aprile", "maggio",
               "giugno", "luglio", "agosto", "settembre", "ottobre",
               "novembre", "dicembre"],
        "en": ["", "January", "February", "March", "April", "May",
               "June", "July", "August", "September", "October",
               "November", "December"],
    },

    # ==================== SYSTEM PROMPT VARIABLES ====================
    "prompt.default_user": {
        "it": "l'utente",
        "en": "the user",
    },
    "prompt.no_knowledge": {
        "it": "Nessuna knowledge base disponibile.",
        "en": "No knowledge base available.",
    },

    # ==================== STATS MESSAGES ====================
    "stats.analysis_in_progress": {
        "it": "ANALISI SISTEMA IN CORSO...",
        "en": "SYSTEM ANALYSIS IN PROGRESS...",
    },
    "stats.no_profile_data": {
        "it": "NESSUN DATO PROFILO DISPONIBILE.",
        "en": "NO PROFILE DATA AVAILABLE.",
    },
    "stats.analysis_unavailable": {
        "it": "ANALISI SISTEMA NON DISPONIBILE. ATTENDERE ELABORAZIONE DATI.",
        "en": "SYSTEM ANALYSIS NOT AVAILABLE. AWAITING DATA PROCESSING.",
    },
    "stats.read_error": {
        "it": "ERRORE LETTURA SISTEMA.",
        "en": "SYSTEM READ ERROR.",
    },
}


def t(key: str, lang: str = "it", **kwargs) -> str:
    """
    Get translated string by key and language.

    Args:
        key: Translation key (e.g., "auth.email_registered")
        lang: Language code ("it" or "en"), defaults to "it"
        **kwargs: Format parameters for the string

    Returns:
        Translated string, with kwargs applied via str.format()
    """
    if lang not in ("it", "en"):
        lang = "it"

    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key

    text = entry.get(lang, entry.get("it", key))

    if isinstance(text, str) and kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return text


def get_list(key: str, lang: str = "it") -> list:
    """
    Get a translated list (e.g., weekday names, month names).

    Args:
        key: Translation key
        lang: Language code

    Returns:
        List of translated strings
    """
    if lang not in ("it", "en"):
        lang = "it"

    entry = TRANSLATIONS.get(key)
    if entry is None:
        return []

    return entry.get(lang, entry.get("it", []))
