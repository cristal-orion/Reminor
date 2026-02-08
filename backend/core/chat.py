"""
Chat Service for Reminor Backend
Handles AI conversations with journal context using LiteLLM for multi-provider support
"""

import os
import re
import litellm
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .memory import MemoryManager
from .i18n import t, get_list

# Disable LiteLLM telemetry
litellm.telemetry = False


class ChatService:
    """
    AI Chat service with journal context awareness.
    Supports multiple LLM providers via LiteLLM (Groq, OpenAI, Anthropic, Gemini, Mistral, DeepSeek).
    """

    # Default models per provider (LiteLLM format)
    DEFAULT_MODELS = {
        "groq": "groq/llama-3.3-70b-versatile",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-20241022",
        "gemini": "gemini/gemini-2.0-flash",
        "mistral": "mistral/mistral-large-latest",
        "deepseek": "deepseek/deepseek-chat",
    }

    # Gemini preview models mapping (user-friendly -> LiteLLM format)
    GEMINI_MODELS = {
        "gemini-3-pro-preview": "gemini/gemini-3-pro-preview",
        "gemini-3-flash-preview": "gemini/gemini-3-flash-preview",
        "gemini-2.5-flash-preview-04-17": "gemini/gemini-2.5-flash-preview-04-17",
        "gemini-2.0-flash": "gemini/gemini-2.0-flash",
    }

    # API key environment variable names per provider
    API_KEY_ENV_VARS = {
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }

    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize chat service.

        Args:
            memory_manager: Memory manager instance for context
        """
        self.memory_manager = memory_manager
        self.prompts_dir = Path(__file__).parent.parent.parent / "prompts"

        # Conversation history per user (in-memory, could be Redis)
        self._conversations: Dict[str, List[Dict[str, str]]] = {}

    def get_litellm_model(self, provider: str, model: Optional[str] = None) -> str:
        """
        Get the LiteLLM model string for a provider/model combination.

        Args:
            provider: Provider name (groq, openai, anthropic, etc.)
            model: Optional model name

        Returns:
            LiteLLM-formatted model string
        """
        if not model:
            return self.DEFAULT_MODELS.get(provider, self.DEFAULT_MODELS["groq"])

        # LiteLLM format: provider/model (except openai which is just model name)
        if provider == "openai":
            return model
        elif provider == "groq":
            return f"groq/{model}"
        elif provider == "anthropic":
            return model  # Anthropic models don't need prefix
        elif provider == "gemini":
            # Use mapping for Gemini models, fallback to gemini/ prefix
            return self.GEMINI_MODELS.get(model, f"gemini/{model}")
        elif provider == "mistral":
            return f"mistral/{model}"
        elif provider == "deepseek":
            return f"deepseek/{model}"
        else:
            return model

    def parse_date_query(self, query: str, language: str = "it") -> List[str]:
        """Extract and convert dates from query text to ISO format.

        Supports both Italian and English date patterns.
        """
        dates = []
        current_year = datetime.now().year
        query_lower = query.lower()

        # Italian month patterns
        it_patterns = [
            (r'(\d{1,2})\s+gennaio', 1),
            (r'(\d{1,2})\s+febbraio', 2),
            (r'(\d{1,2})\s+marzo', 3),
            (r'(\d{1,2})\s+aprile', 4),
            (r'(\d{1,2})\s+maggio', 5),
            (r'(\d{1,2})\s+giugno', 6),
            (r'(\d{1,2})\s+luglio', 7),
            (r'(\d{1,2})\s+agosto', 8),
            (r'(\d{1,2})\s+settembre', 9),
            (r'(\d{1,2})\s+ottobre', 10),
            (r'(\d{1,2})\s+novembre', 11),
            (r'(\d{1,2})\s+dicembre', 12),
        ]

        # English month patterns
        en_patterns = [
            (r'(\d{1,2})\s+january', 1), (r'january\s+(\d{1,2})', 1),
            (r'(\d{1,2})\s+february', 2), (r'february\s+(\d{1,2})', 2),
            (r'(\d{1,2})\s+march', 3), (r'march\s+(\d{1,2})', 3),
            (r'(\d{1,2})\s+april', 4), (r'april\s+(\d{1,2})', 4),
            (r'(\d{1,2})\s+may', 5), (r'may\s+(\d{1,2})', 5),
            (r'(\d{1,2})\s+june', 6), (r'june\s+(\d{1,2})', 6),
            (r'(\d{1,2})\s+july', 7), (r'july\s+(\d{1,2})', 7),
            (r'(\d{1,2})\s+august', 8), (r'august\s+(\d{1,2})', 8),
            (r'(\d{1,2})\s+september', 9), (r'september\s+(\d{1,2})', 9),
            (r'(\d{1,2})\s+october', 10), (r'october\s+(\d{1,2})', 10),
            (r'(\d{1,2})\s+november', 11), (r'november\s+(\d{1,2})', 11),
            (r'(\d{1,2})\s+december', 12), (r'december\s+(\d{1,2})', 12),
        ]

        # Always try both Italian and English patterns (diary may be in either language)
        all_patterns = it_patterns + en_patterns

        for pattern, month in all_patterns:
            matches = re.findall(pattern, query_lower)
            for day in matches:
                try:
                    date_str = f"{current_year}-{month:02d}-{int(day):02d}"
                    if date_str not in dates:
                        dates.append(date_str)
                except ValueError:
                    continue

        # "il X" pattern - Italian (assumes current month)
        il_pattern = re.findall(r'\bil\s+(\d{1,2})\b', query_lower)
        current_month = datetime.now().month
        for day in il_pattern:
            try:
                date_str = f"{current_year}-{current_month:02d}-{int(day):02d}"
                if date_str not in dates:
                    dates.append(date_str)
            except ValueError:
                continue

        # "the Xth/Xst/Xnd/Xrd" pattern - English (assumes current month)
        the_pattern = re.findall(r'\bthe\s+(\d{1,2})(?:st|nd|rd|th)?\b', query_lower)
        for day in the_pattern:
            try:
                date_str = f"{current_year}-{current_month:02d}-{int(day):02d}"
                if date_str not in dates:
                    dates.append(date_str)
            except ValueError:
                continue

        # Relative dates - Italian
        if 'ieri' in query_lower:
            yesterday = datetime.now() - timedelta(days=1)
            dates.append(yesterday.strftime("%Y-%m-%d"))

        if any(word in query_lower for word in ['oggi', 'stamattina', 'stasera']):
            today = datetime.now()
            dates.append(today.strftime("%Y-%m-%d"))

        # Relative dates - English
        if 'yesterday' in query_lower:
            yesterday = datetime.now() - timedelta(days=1)
            d = yesterday.strftime("%Y-%m-%d")
            if d not in dates:
                dates.append(d)

        if any(word in query_lower for word in ['today', 'this morning', 'tonight']):
            today = datetime.now()
            d = today.strftime("%Y-%m-%d")
            if d not in dates:
                dates.append(d)

        return dates

    def get_intelligent_context(self, user_id: str, query: str,
                                 num_entries: int = 20,
                                 language: str = "it") -> str:
        """
        Get intelligent context based on user query.

        Args:
            user_id: User ID
            query: User's query
            num_entries: Max entries to include
            language: User language for labels

        Returns:
            Formatted context string
        """
        memory = self.memory_manager.get_user_memory(user_id)
        context_parts = []

        # 1. Look for specific dates in query
        target_dates = self.parse_date_query(query, language)

        if target_dates:
            for date in target_dates:
                if date in memory.entries:
                    entry = memory.entries[date]
                    context_parts.append(f"=== {date} ===\n{entry}\n")

        # 2. Use similarity search for additional context
        similarity_context = memory.get_rich_context(query=query, num_entries=num_entries)

        if similarity_context:
            related_label = t("chat.related_entries", language)
            if context_parts:
                context_parts.append(f"=== {related_label} ===\n" + similarity_context)
            else:
                context_parts.append(similarity_context)

        return "\n".join(context_parts) if context_parts else similarity_context

    def get_system_prompt(self, user_name: str, context: str,
                          knowledge: str = "", language: str = "it") -> str:
        """
        Generate system prompt for the AI.

        Args:
            user_name: User's name
            context: Journal context (from semantic search)
            knowledge: Knowledge base (persistent info about user)
            language: User language ("it" or "en")

        Returns:
            System prompt string
        """
        now = datetime.now()
        weekdays = get_list("date.weekdays", language)
        months = get_list("date.months", language)

        weekday_name = weekdays[now.weekday()]

        if language == "en":
            data_oggi = f"{weekday_name}, {months[now.month]} {now.day}, {now.year}"
        else:
            data_oggi = f"{weekday_name} {now.day} {months[now.month]} {now.year}"

        ora_attuale = now.strftime("%H:%M")
        data_iso = now.strftime("%Y-%m-%d")

        default_user = t("prompt.default_user", language)
        no_knowledge = t("prompt.no_knowledge", language)

        # Select prompt file based on language
        if language == "en":
            prompt_file = self.prompts_dir / "system_prompt_en.txt"
            if not prompt_file.exists():
                prompt_file = self.prompts_dir / "system_prompt.txt"
        else:
            prompt_file = self.prompts_dir / "system_prompt.txt"

        variables = {
            'user_name': user_name or default_user,
            'data_oggi': data_oggi,
            'ora_attuale': ora_attuale,
            'data_iso': data_iso,
            'knowledge': knowledge or no_knowledge,
            'context': context
        }

        try:
            if prompt_file.exists():
                template = prompt_file.read_text(encoding='utf-8')
                for key, value in variables.items():
                    template = template.replace(f"{{{key}}}", str(value))
                return template
        except Exception as e:
            print(f"Error loading prompt file: {e}")

        # Fallback prompt
        return self._get_fallback_prompt(variables, language)

    def _get_fallback_prompt(self, variables: dict, language: str = "it") -> str:
        """Fallback system prompt"""
        if language == "en":
            return f"""# WHO YOU ARE

You are Reminor's AI, the digital companion who has read the user's diary.

# INFORMATION
- **Username**: {variables['user_name']}
- **Today is**: {variables['data_oggi']}
- **Current time**: {variables['ora_attuale']}

# KNOWLEDGE BASE (Permanent information about the user)
{variables['knowledge']}

# DIARY CONTEXT (Search results for this question)
{variables['context']}

# HOW YOU SPEAK
- Speak like a friend who knows the user's story
- Use specific references from the diary and knowledge base
- Brief and direct (2-3 sentences)
- Always respond in English

# ANTI-HALLUCINATION RULES
- IF YOU DON'T HAVE INFORMATION FROM THE DIARY, SAY SO CLEARLY
- NEVER INVENT dates, names, places or events
"""
        return f"""# CHI SEI

Sei l'AI di Reminor, il compagno digitale che ha letto il diario dell'utente.

# INFORMAZIONI
- **Nome utente**: {variables['user_name']}
- **Oggi è**: {variables['data_oggi']}
- **Ora attuale**: {variables['ora_attuale']}

# KNOWLEDGE BASE (Informazioni permanenti sull'utente)
{variables['knowledge']}

# CONTESTO DEL DIARIO (Risultati ricerca per questa domanda)
{variables['context']}

# COME PARLI
- Parla come un amico che conosce la storia dell'utente
- Usa riferimenti specifici dal diario e dalla knowledge base
- Breve e diretto (2-3 frasi)
- Rispondi SEMPRE in italiano

# REGOLE ANTI-ALLUCINAZIONE
- SE NON HAI INFORMAZIONI DAL DIARIO, DILLO CHIARAMENTE
- NON INVENTARE MAI date, nomi, luoghi o eventi
"""

    def get_conversation(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a user"""
        if user_id not in self._conversations:
            self._conversations[user_id] = []
        return self._conversations[user_id]

    def add_message(self, user_id: str, role: str, content: str):
        """Add message to conversation history"""
        conversation = self.get_conversation(user_id)
        conversation.append({"role": role, "content": content})

        # Keep last 20 messages
        if len(conversation) > 20:
            self._conversations[user_id] = conversation[-20:]

    def clear_conversation(self, user_id: str):
        """Clear conversation history for a user"""
        self._conversations[user_id] = []

    async def chat(self, user_id: str, message: str,
                   user_name: str = "",
                   user_api_key: Optional[str] = None,
                   provider: str = "groq",
                   model: Optional[str] = None,
                   include_context: bool = True,
                   language: str = "it") -> Dict[str, Any]:
        """
        Send a chat message and get a response using LiteLLM.

        Args:
            user_id: User ID
            message: User's message
            user_name: User's name for personalization
            user_api_key: Optional user API key (overrides env)
            provider: LLM provider (groq, openai, anthropic, gemini, mistral, deepseek)
            model: Optional model name (uses default for provider if not specified)
            include_context: Whether to include journal context
            language: User language for prompts and error messages

        Returns:
            Dict with response and metadata
        """
        # Get API key: user-provided > environment variable
        api_key = user_api_key
        if not api_key:
            env_var = self.API_KEY_ENV_VARS.get(provider, "GROQ_API_KEY")
            api_key = os.getenv(env_var) or os.getenv("GROQ_API_KEY")

        if not api_key:
            return {
                "response": t("chat.api_key_missing", language, provider=provider),
                "error": True
            }

        # Get LiteLLM model string
        litellm_model = self.get_litellm_model(provider, model)

        # Get context and knowledge base
        context = ""
        knowledge = ""
        if include_context:
            context = self.get_intelligent_context(user_id, message, language=language)
            knowledge = self.memory_manager.get_user_knowledge(user_id, language=language)

        # Use knowledge base name as fallback if user_name not provided
        effective_user_name = user_name
        if not effective_user_name:
            effective_user_name = self.memory_manager.get_user_name_from_knowledge(user_id)

        # Build messages
        system_prompt = self.get_system_prompt(effective_user_name, context, knowledge, language)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.get_conversation(user_id))
        messages.append({"role": "user", "content": message})

        # Make API request via LiteLLM
        try:
            response = await litellm.acompletion(
                model=litellm_model,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                api_key=api_key,
            )

            assistant_message = response.choices[0].message.content

            # Save to conversation history (maintains history across provider switches)
            self.add_message(user_id, "user", message)
            self.add_message(user_id, "assistant", assistant_message)

            return {
                "response": assistant_message,
                "context_used": bool(context),
                "model": litellm_model,
                "provider": provider,
                "error": False
            }

        except litellm.AuthenticationError as e:
            return {
                "response": t("chat.api_key_invalid", language, provider=provider),
                "error": True
            }
        except litellm.BadRequestError as e:
            error_msg = str(e).lower()
            if "api key" in error_msg or "api_key" in error_msg or "invalid" in error_msg:
                return {
                    "response": t("chat.api_key_expired", language, provider=provider),
                    "error": True
                }
            return {
                "response": t("chat.request_error", language, provider=provider, error=str(e)),
                "error": True
            }
        except litellm.RateLimitError as e:
            return {
                "response": t("chat.rate_limit", language, provider=provider),
                "error": True
            }
        except litellm.APIConnectionError as e:
            return {
                "response": t("chat.connection_error", language, provider=provider, error=str(e)),
                "error": True
            }
        except Exception as e:
            error_msg = str(e).lower()
            if "api key" in error_msg or "api_key" in error_msg or "invalid api" in error_msg:
                return {
                    "response": t("chat.api_key_invalid", language, provider=provider),
                    "error": True
                }
            if "405" in error_msg or "method not allowed" in error_msg:
                detail = (
                    f"The provider '{provider}' returned a 405 error. This usually means the model or endpoint is not available. Check your provider/model settings."
                    if language == "en"
                    else f"Il provider '{provider}' ha restituito un errore 405. Questo di solito significa che il modello o l'endpoint non e' disponibile. Controlla le impostazioni del provider/modello."
                )
                return {
                    "response": detail,
                    "error": True
                }
            return {
                "response": t("chat.generic_error", language, error=str(e)),
                "error": True
            }
