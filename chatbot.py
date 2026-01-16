#!/usr/bin/env python3
"""
ChatBot module for MySoul Extreme Journal
Integrates with Groq API to chat with journal entries
Adapted for 400x300 display with larger fonts and arrow navigation.
"""

import os
import datetime
import requests
import re
from pathlib import Path
from typing import List, Dict, Optional
import tkinter as tk  # Importato tkinter come tk

# Gestione import opzionale di dotenv
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    print("[WARN] Avviso: python-dotenv non installato. Utilizzando variabili d'ambiente del sistema.")

# Usa Memvid invece di FAISS per la memoria
try:
    from memvid_memory import MemvidMemory as UnifiedMemory
    print("[OK] Usando MemvidMemory (leggero e veloce)")
except ImportError:
    from memory_system import UnifiedMemory
    print("[WARN] Memvid non disponibile, usando memory_system tradizionale")

# Carica il file .env se dotenv è disponibile
api_key = None
env_path = Path(__file__).parent / '.env'

if HAS_DOTENV:
    # Carica il file .env in modo esplicito
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"[OK] File .env caricato da: {env_path}")
    else:
        print(f"[WARN] File .env non trovato in: {env_path}")
else:
    if env_path.exists():
        # Leggi manualmente il file .env
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        if key == 'GROQ_API_KEY':
                            os.environ[key] = value
                            print(f"[OK] GROQ_API_KEY caricata manualmente dal file .env")
        except Exception as e:
            print(f"[WARN] Errore nella lettura manuale del file .env: {e}")

# Verifica che la chiave sia caricata
api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    print("[ERROR] GROQ_API_KEY non trovata nel file .env o nelle variabili d'ambiente")
    print("   Assicurati che il file .env contenga: GROQ_API_KEY=your_api_key_here")
else:
    print(f"[OK] GROQ_API_KEY caricata correttamente (lunghezza: {len(api_key)} caratteri)")

class JournalChatBot:
    def __init__(self, journal_dir: Path, settings: dict, structured_memory: UnifiedMemory = None):
        self.journal_dir = journal_dir
        self.settings = settings
        self.api_key = os.getenv('GROQ_API_KEY')
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "openai/gpt-oss-120b"
        self.conversation_history = []
        self.structured_memory = structured_memory

    def load_journal_context(self, days_back: int = None) -> str:
        """Load recent journal entries as context, preferendo UnifiedMemory se disponibile"""
        if self.structured_memory is not None and hasattr(self.structured_memory, "get_rich_context"):
            # Usa la memoria avanzata per il contesto
            return self.structured_memory.get_rich_context(num_entries=10)

        context_entries = []
        files_to_load = []

        # Prima proviamo a ordinare in base al nome del file (YYYY-MM-DD)
        try:
            all_files = sorted(
                [f for f in self.journal_dir.glob("*.txt") if f.is_file()],
                key=lambda x: x.name,
                reverse=True  # Più recenti prima
            )
        except:
            # Se fallisce, ordina per data di modifica come fallback
            all_files = sorted(
                [f for f in self.journal_dir.glob("*.txt") if f.is_file()],
                key=lambda x: x.stat().st_mtime,
                reverse=True  # Più recenti prima
            )

        if days_back:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
            files_to_load = [
                f for f in all_files
                if datetime.datetime.fromtimestamp(f.stat().st_mtime) >= cutoff_date
            ]
        else:
            # Aumentiamo il numero di file da caricare da 10 a 15
            files_to_load = all_files[:15]

        # Aggiungi debug per verificare quali file vengono trovati
        print(f"Trovati {len(files_to_load)} file di diario recenti per il contesto.")
        
        for file_path in files_to_load:
            try:
                content = file_path.read_text(encoding='utf-8')
                if content.strip():
                    date_str = file_path.stem
                    context_entries.append(f"=== Diario del {date_str} ===\n{content}")
                    print(f"Aggiunta voce diario: {date_str}")
            except Exception as e:
                print(f"Errore leggendo {file_path}: {e}")

        if not context_entries:
            return "Nessuna voce del diario disponibile per il contesto."

        # Aumentiamo il numero di voci da includere nel contesto da 5 a 10
        # e li prendiamo dall'inizio dell'array (i più recenti) invece che dalla fine
        return "\n\n".join(context_entries[:10])

    def parse_italian_date_query(self, query: str) -> list:
        """Estrae e converte date italiane in formato ISO"""
        import re
        from datetime import datetime, timedelta
        
        dates = []
        current_year = datetime.now().year
        
        # Pattern per date italiane
        patterns = [
            (r'(\d{1,2})\s+giugno', 6),
            (r'(\d{1,2})\s+gennaio', 1),
            (r'(\d{1,2})\s+febbraio', 2),
            (r'(\d{1,2})\s+marzo', 3),
            (r'(\d{1,2})\s+aprile', 4),
            (r'(\d{1,2})\s+maggio', 5),
            (r'(\d{1,2})\s+luglio', 7),
            (r'(\d{1,2})\s+agosto', 8),
            (r'(\d{1,2})\s+settembre', 9),
            (r'(\d{1,2})\s+ottobre', 10),
            (r'(\d{1,2})\s+novembre', 11),
            (r'(\d{1,2})\s+dicembre', 12),
        ]
        
        for pattern, month in patterns:
            matches = re.findall(pattern, query.lower())
            for day in matches:
                try:
                    date_str = f"{current_year}-{month:02d}-{int(day):02d}"
                    dates.append(date_str)
                except ValueError:
                    continue
        
        # Pattern per "il X" (assume mese corrente)
        il_pattern = re.findall(r'\bil\s+(\d{1,2})\b', query.lower())
        current_month = datetime.now().month
        for day in il_pattern:
            try:
                date_str = f"{current_year}-{current_month:02d}-{int(day):02d}"
                dates.append(date_str)
            except ValueError:
                continue
        
        # Date relative
        if 'ieri' in query.lower():
            yesterday = datetime.now() - timedelta(days=1)
            dates.append(yesterday.strftime("%Y-%m-%d"))
        
        if 'oggi' in query.lower() or 'stamattina' in query.lower() or 'stasera' in query.lower():
            today = datetime.now()
            dates.append(today.strftime("%Y-%m-%d"))
        
        return dates

    def load_journal_context_intelligent(self, user_query: str, days_back: int = None) -> str:
        """Load intelligent context based on user query using similarity search"""
        if self.structured_memory is not None and hasattr(self.structured_memory, "get_rich_context"):
            # 1. Prima cerca date specifiche nella query
            target_dates = self.parse_italian_date_query(user_query)
            context_parts = []
            
            # 2. Carica direttamente le voci per le date trovate
            if target_dates:
                for date in target_dates:
                    if hasattr(self.structured_memory, 'entries') and date in self.structured_memory.entries:
                        entry = self.structured_memory.entries[date]
                        context_parts.append(f"=== {date} ===\n{entry}\n")
            
            # 3. Usa anche la ricerca per similarità per contesto aggiuntivo
            similarity_context = self.structured_memory.get_rich_context(query=user_query, num_entries=5)
            if similarity_context:
                if context_parts:
                    context_parts.append("=== Voci correlate ===\n" + similarity_context)
                else:
                    context_parts.append(similarity_context)
            
            return "\n".join(context_parts) if context_parts else similarity_context
        
        # Fallback al metodo vecchio se UnifiedMemory non disponibile
        return self.load_journal_context(days_back)

    def _get_system_prompt(self, context: str) -> str:
        """Genera il system prompt avanzato per l'AI leggendo da file"""
        import datetime
        import locale
        from pathlib import Path

        # Prova a impostare locale italiano per i nomi dei giorni
        try:
            locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'it_IT')
            except:
                pass  # Usa default se italiano non disponibile

        now = datetime.datetime.now()
        giorni_settimana = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        mesi = ['', 'gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
                'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']

        giorno_settimana = giorni_settimana[now.weekday()]
        data_oggi = f"{giorno_settimana} {now.day} {mesi[now.month]} {now.year}"
        ora_attuale = now.strftime("%H:%M")
        data_iso = now.strftime("%Y-%m-%d")

        # Percorso del file del prompt
        prompt_file = Path(__file__).parent / "prompts" / "system_prompt.txt"

        # Ottieni il nome utente dalle impostazioni
        user_name = self.settings.get('user_name', '').strip()
        if not user_name:
            user_name = "l'utente"

        # Variabili da sostituire nel template
        variables = {
            'user_name': user_name,
            'data_oggi': data_oggi,
            'ora_attuale': ora_attuale,
            'data_iso': data_iso,
            'context': context
        }

        try:
            # Leggi il prompt da file
            if prompt_file.exists():
                template = prompt_file.read_text(encoding='utf-8')

                # Sostituisci le variabili nel template
                for key, value in variables.items():
                    template = template.replace(f"{{{key}}}", str(value))

                return template
            else:
                # Fallback se il file non esiste
                print(f"[WARN] File prompt non trovato: {prompt_file}")
                return self._get_fallback_prompt(variables)

        except Exception as e:
            print(f"[ERROR] Errore leggendo il prompt da file: {e}")
            return self._get_fallback_prompt(variables)

    def _get_fallback_prompt(self, variables: dict) -> str:
        """Prompt di fallback se il file non è disponibile"""
        return f"""# CHI SEI

Sei l'AI di Reminor, il compagno digitale che ha letto il diario dell'utente. Non sei un terapista né un life coach - sei quella presenza che conosce la storia, ricorda i dettagli, e sa quando dire "eh già, proprio come quella volta a giugno".

# INFORMAZIONI UTENTE
- **Nome utente**: {variables['user_name']}

# INFORMAZIONI TEMPORALI
- **Oggi è**: {variables['data_oggi']}
- **Ora attuale**: {variables['ora_attuale']}
- **Data ISO**: {variables['data_iso']}

# COSA SAI

Hai accesso a:
- **Il diario completo** dell'utente (le ultime voci sono nel CONTESTO)
- **Le emozioni rilevate** in ogni giorno
- **Pattern e ricorrenze** (persone, luoghi, comportamenti)

# CONTESTO DEL DIARIO
{variables['context']}

# COME PARLI

## La regola d'oro
**Parla come un amico che conosce davvero la tua storia.** Non quello che fa finta di ricordare, ma quello che dice "come è andata poi con [persona/situazione specifica del diario]?"

## Usa il diario in modo naturale
- **Riferimenti specifici**: "Mi ricordo che il 15 giugno scrivevi che..."
- **Pattern notati**: "È la terza volta questo mese che menzioni..."
- **Connessioni temporali**: "Proprio come quando a marzo..."

## Stile conversazionale
- Breve e diretto (2-3 frasi di solito)
- Niente formule o template
- A volte una domanda, a volte un'osservazione
- Mai ripetere quello che l'utente ha appena scritto

# TECNICHE SPECIFICHE

## Quando l'utente chiede del passato
Non: "Cercando nel tuo diario, vedo che..."
Sì: "Ah sì, il 20 ottobre. Che casino quel giorno."

## Quando noti pattern emotivi
Non: "Ho analizzato le tue emozioni e risulta che..."
Sì: "Ultimamente sei più sereno del solito, o sbaglio?"

## Quando fare ricerche mirate
- Se chiede "quando ho parlato di X" → cerca X nel diario
- Se chiede "come mi sentivo a Y" → trova le emozioni di quel periodo
- Se chiede "chi è Z" → trova tutte le menzioni di Z

# ESEMPI PRATICI

Basati sul contesto reale del diario per rispondere, non su esempi generici. Usa sempre date, nomi e dettagli specifici dal diario dell'utente.

# COSA NON DIMENTICARE

1. **Hai una memoria vera** - non fingere di ricordare, ricorda davvero
2. **I dettagli contano** - date, nomi, luoghi danno sostanza
3. **Le emozioni si evolvono** - nota i cambiamenti nel tempo
4. **Non tutto va risolto** - a volte basta riconoscere

# IL MANTRA

Prima di rispondere chiediti: "Sto usando quello che so dal diario o sto facendo conversazione generica?"

Se è generica, ricomincia usando qualcosa di specifico dal diario.

# REGOLE FONDAMENTALI ANTI-ALLUCINAZIONE

[WARN] **IMPORTANTE**:
- **SE NON HAI INFORMAZIONI SPECIFICHE DAL DIARIO, DILLO CHIARAMENTE**
- **NON INVENTARE MAI date, nomi, luoghi, eventi o citazioni**
- **Se il contesto è vuoto o non contiene l'informazione richiesta, ammetti di non avere quella informazione**
- **Meglio dire "Non ricordo di aver letto questo nel tuo diario" che inventare dettagli**

Esempi corretti quando NON hai informazioni:
- "Non ho trovato riferimenti al viaggio in Sardegna nelle voci che riesco a vedere"
- "Mi dispiace, non riesco a trovare quella data specifica"
- "Dalle voci che ho non emerge questo dettaglio"

# NOTE IMPORTANTI

- L'utente sa che hai letto il suo diario. Non fingere di non sapere. Usa quella conoscenza con rispetto ma senza timidezza
- **MA se non hai l'informazione specifica, dillo onestamente**
- Rispondi SEMPRE in italiano
"""

    def _get_advanced_insights(self, user_message_lower: str, original_message: str) -> str:
        """Generate advanced insights based on user query patterns"""
        if self.structured_memory is None:
            return ""
        insights = []
        if any(k in user_message_lower for k in ["simile", "ricorda", "altre volte", "quando è successo"]):
            similar = self.structured_memory.get_similar_entries(original_message, top_n=3)
            if similar:
                insights.append("🔍 VOCI SIMILI TROVATE:")
                for entry in similar:
                    date = entry.get('date', 'N/A')
                    score = entry.get('score', 0)
                    insights.append(f"  • {date} (rilevanza: {score:.1f})")
        if any(k in user_message_lower for k in ["emozion", "sentiment", "come mi sentivo", "umore"]):
            timeline = self.structured_memory.get_emotional_timeline()
            if timeline:
                insights.append("😊 TIMELINE EMOTIVA RECENTE:")
                recent_emotions = sorted(timeline.items())[-5:]
                for date, emotions in recent_emotions:
                    if emotions:
                        top_emotion = max(emotions.items(), key=lambda x: x[1])
                        insights.append(f"  • {date}: {top_emotion[0]} ({top_emotion[1]}x)")
        if any(k in user_message_lower for k in ["comportament", "pattern", "abitudine", "solito"]):
            patterns = self.structured_memory.get_behavioral_patterns()
            if patterns:
                insights.append("🔄 PATTERN COMPORTAMENTALI:")
                top_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]
                insights.append("  Azioni più frequenti: " + ", ".join([f"{verb} ({count}x)" for verb, count in top_patterns]))
        return "\n".join(insights) if insights else ""

    def chat(self, user_message: str) -> str:
        """Chat with the AI using journal context and advanced memory if disponibile"""
        if not self.api_key:
            return "[ERROR] Errore: GROQ_API_KEY non configurata nel file .env"

        try:
            user_message_lower = user_message.lower()
            advanced_insight = self._get_advanced_insights(user_message_lower, user_message)

            # CAMBIATO: ora il contesto è intelligente
            context = self.load_journal_context_intelligent(user_message, days_back=30)
            if advanced_insight:
                context += "\n\n" + advanced_insight

            # Usa il nuovo system prompt avanzato
            system_prompt = self._get_system_prompt(context)

            messages = [
                {"role": "system", "content": system_prompt},
                *self.conversation_history,
                {"role": "user", "content": user_message}
            ]

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 600
            }

            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            response_data = response.json()
            ai_response = response_data['choices'][0]['message']['content']

            # Mantieni la cronologia della conversazione (ultimi 6 messaggi)
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            if len(self.conversation_history) > 6:
                self.conversation_history = self.conversation_history[-6:]

            return ai_response

        except Exception as e:
            error_msg = f"Errore durante la comunicazione con l'AI: {str(e)}"
            print(error_msg)
            return f"😓 Mi dispiace, ho avuto un problema tecnico: {str(e)}"


class ChatScreen(tk.Frame):
    def __init__(self, parent, journal_dir: Path, settings: dict, on_back_callback, memory=None):
        super().__init__(parent, bg=settings.get('bg_color', '#000000'))  # Usa colore tema
        
        self.settings = settings
        self.chatbot = JournalChatBot(journal_dir, settings, structured_memory=memory)
        self.on_back_callback = on_back_callback
        self.thinking_text = ""

        # Font definitions - Get from settings
        font_family = settings.get('font_family', 'Courier New')
        self.font_title = (font_family, 28, 'bold')
        self.font_button = (font_family, 16)
        self.font_chat = (font_family, 16)
        self.font_input = (font_family, 16)

        self.setup_ui()

    def setup_ui(self):
        """Setup minimal chat interface"""
        # Controlla se API key è configurata
        api_key = os.environ.get('GROQ_API_KEY', '')
        if not api_key or not api_key.startswith('gsk_'):
            self._show_api_key_missing()
            return

        # Title Frame - minimal design
        title_frame = tk.Frame(self, bg=self.settings['bg_color'])
        title_frame.pack(fill=tk.X, padx=30, pady=(20, 10))
        
        tk.Label(title_frame, 
                text="CHAT AI",
                bg=self.settings['bg_color'],
                fg=self.settings['fg_color'],
                font=self.font_title).pack(side=tk.LEFT)
                
        back_btn = tk.Button(title_frame,
                           text="← BACK",
                           bg=self.settings['bg_color'],
                           fg=self.settings['fg_color'],
                           font=self.font_button,
                           command=self._on_back_pressed,
                           relief=tk.FLAT,
                           borderwidth=0,
                           highlightthickness=0,
                           cursor='hand2')
        back_btn.pack(side=tk.RIGHT)

        # Input area - minimal design
        input_frame = tk.Frame(
            self, 
            bg=self.settings['bg_color'],
            relief=tk.FLAT,
            borderwidth=0,
            height=50
        )
        input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=30, pady=20)
        input_frame.pack_propagate(False)

        # Minimal input field with bottom border only
        self.message_entry = tk.Entry(
            input_frame,
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            insertbackground=self.settings['fg_color'],
            font=self.font_input,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)
        
        # Add bottom border line
        border_line = tk.Frame(input_frame, bg='#e0e0e0', height=1)
        border_line.place(x=0, y=48, relwidth=0.85)
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        # Binding diretto sull'input per intercettare le frecce
        self.message_entry.bind('<Up>', self.on_arrow_up)
        self.message_entry.bind('<Down>', self.on_arrow_down)
        
        send_btn = tk.Button(
            input_frame,
            text="SEND",
            bg='#000000',
            fg='#ffffff',
            font=self.font_button,
            command=self.send_message,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            padx=20,
            cursor='hand2'
        )
        send_btn.pack(side=tk.RIGHT, padx=0, pady=10)
        
        # Chat display area - minimal clean design
        chat_frame = tk.Frame(self, bg=self.settings['bg_color'])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=(10, 10))
        
        self.chat_display = tk.Text(
            chat_frame,
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            font=self.font_chat,
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=25,
            relief=tk.FLAT,
            borderwidth=0,
            selectbackground='#e0e0e0',
            padx=10,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Binding per navigazione con Page Up/Down
        self.master.bind('<Page_Up>', self.page_up)  # Page Up
        self.master.bind('<Page_Down>', self.page_down)  # Page Down
        # F2 binding specifico per il chat display invece che globale
        self.chat_display.bind('<F2>', lambda e: self.show_thinking())
        
        # Colori adattivi per tema chiaro/scuro
        bg_color = self.settings.get('bg_color', '#000000')
        if bg_color == '#000000' or bg_color == '#1a1a1a':  # Temi scuri (Notte e Dark Blue)
            self.chat_display.tag_config('user', foreground='#ffffff', font=(self.font_chat[0], self.font_chat[1], 'bold'))
            self.chat_display.tag_config('assistant', foreground='#90EE90')  # Verde chiaro
            self.chat_display.tag_config('system', foreground='#808080', font=(self.font_chat[0], self.font_chat[1] - 2, 'italic'))
            self.chat_display.tag_config('error', foreground='#ff6666')
            self.chat_display.tag_config('timestamp_prefix', foreground='#808080', font=(self.font_chat[0], self.font_chat[1] - 2))
        else:  # Tema chiaro (Giorno)
            self.chat_display.tag_config('user', foreground='#000000', font=(self.font_chat[0], self.font_chat[1], 'bold'))
            self.chat_display.tag_config('assistant', foreground='#008000')  # Verde scuro
            self.chat_display.tag_config('system', foreground='#666666', font=(self.font_chat[0], self.font_chat[1] - 2, 'italic'))
            self.chat_display.tag_config('error', foreground='#cc0000')
            self.chat_display.tag_config('timestamp_prefix', foreground='#666666', font=(self.font_chat[0], self.font_chat[1] - 2))

        self.add_message("Chiedimi qualcosa sul tuo diario.", 'system')
        self.add_message("Usa ↑↓ per navigare | F2 per vedere il ragionamento", 'system')
        
        # Assicurati che l'entry field abbia sempre il focus quando serve
        self.message_entry.focus_set()
        
        # Binding per dare focus all'entry quando si clicca sulla chat
        self.chat_display.bind('<Button-1>', lambda e: self.message_entry.focus_set())

    def on_arrow_up(self, event):
        """Gestisce freccia su sull'input field"""
        self.chat_display.yview_scroll(-3, "units")  # Scorre di 3 righe per volta
        return "break"  # Impedisce comportamento default (navigazione storia comandi)
    
    def on_arrow_down(self, event):
        """Gestisce freccia giù sull'input field"""
        self.chat_display.yview_scroll(3, "units")  # Scorre di 3 righe per volta
        return "break"  # Impedisce comportamento default
    
    def page_up(self, event):
        """Scorre di una pagina verso l'alto"""
        self.chat_display.yview_scroll(-1, "pages")
        return "break"
    
    def page_down(self, event):
        """Scorre di una pagina verso il basso"""
        self.chat_display.yview_scroll(1, "pages")
        return "break"

    def _on_back_pressed(self):
        # Rimuovi binding globali
        self.master.unbind('<Page_Up>')
        self.master.unbind('<Page_Down>')
        
        # Rimuovi binding dell'input
        if hasattr(self, 'message_entry'):
            self.message_entry.unbind('<Up>')
            self.message_entry.unbind('<Down>')
        
        # Rimuovi binding specifici del chat display
        if hasattr(self, 'chat_display'):
            self.chat_display.unbind('<F2>')
            self.chat_display.unbind('<Button-1>')
            
        if self.on_back_callback:
            self.on_back_callback()

    def _show_api_key_missing(self):
        """Mostra messaggio quando API key non è configurata"""
        # Clear any existing widgets
        for widget in self.winfo_children():
            widget.destroy()

        # Main container
        main_frame = tk.Frame(self, bg=self.settings['bg_color'])
        main_frame.pack(expand=True, fill=tk.BOTH, padx=40, pady=40)

        # Get font family from settings
        font_family = self.settings.get('font_family', 'Courier New')

        # Title
        title_label = tk.Label(
            main_frame,
            text="[WARN] API KEY MANCANTE",
            font=(font_family, 24, 'bold'),
            bg=self.settings['bg_color'],
            fg='#FF6B6B',  # Colore rosso per avvertimento
            pady=20
        )
        title_label.pack()

        # Message
        message_label = tk.Label(
            main_frame,
            text="Per utilizzare la chat AI è necessario\nconfigurare la chiave API di Groq.\n\nVai su IMPOSTAZIONI per configurarla.",
            font=(font_family, 18),
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            justify=tk.CENTER,
            pady=20
        )
        message_label.pack()

        # Instructions
        instruction_label = tk.Label(
            main_frame,
            text="💡 Ottieni una chiave API gratuita su:\nconsole.groq.com/keys",
            font=(font_family, 14),
            bg=self.settings['bg_color'],
            fg='#4ECDC4',  # Colore turchese per info
            justify=tk.CENTER,
            pady=20
        )
        instruction_label.pack()

        # Buttons frame
        buttons_frame = tk.Frame(main_frame, bg=self.settings['bg_color'])
        buttons_frame.pack(pady=30)

        # Back button
        back_btn = tk.Button(
            buttons_frame,
            text="← INDIETRO",
            font=(font_family, 16, 'bold'),
            bg='#2C3E50',
            fg='#FFFFFF',
            activebackground='#34495E',
            activeforeground='#FFFFFF',
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self._on_back_pressed
        )
        back_btn.pack(side=tk.LEFT, padx=10)

        # Settings button (if we can navigate there)
        if hasattr(self, 'on_back_callback') and self.on_back_callback:
            settings_btn = tk.Button(
                buttons_frame,
                text="⚙️ IMPOSTAZIONI",
                font=(font_family, 16, 'bold'),
                bg='#3498DB',
                fg='#FFFFFF',
                activebackground='#2980B9',
                activeforeground='#FFFFFF',
                relief=tk.FLAT,
                padx=20,
                pady=10,
                cursor='hand2',
                command=self._go_to_settings
            )
            settings_btn.pack(side=tk.LEFT, padx=10)

    def _go_to_settings(self):
        """Navigate to settings screen"""
        # First go back to main menu, then the parent can handle navigation to settings
        if self.on_back_callback:
            self.on_back_callback()
            # The parent (ReminorApp) should handle showing settings
            # We'll rely on the user to navigate there from the main menu

    def add_message(self, message: str, sender: str = 'user'):
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        if sender == 'assistant':
            message = re.sub(r'\\n\\s*\\n', '\\n', message).strip()

        # Minimal message format
        if sender == 'user':
            self.chat_display.insert(tk.END, f"\n[{timestamp}] YOU\n", 'timestamp_prefix')
            self.chat_display.insert(tk.END, f"{message}\n", sender)
        elif sender == 'assistant':
            self.chat_display.insert(tk.END, f"\n[{timestamp}] AI\n", 'timestamp_prefix')
            self.chat_display.insert(tk.END, f"{message}\n", sender)
        else:
            self.chat_display.insert(tk.END, f"\n{message}\n", sender)
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def show_thinking(self):
        if hasattr(self, "thinking_text") and self.thinking_text:
            win = tk.Toplevel(self)
            win.title("AI Thinking")
            win.configure(bg=self.settings['bg_color'])
            win.geometry("600x400") # Finestra molto più grande per 720x720
            win.transient(self.master)
            win.grab_set()

            st_frame = tk.Frame(win, bg=self.settings['bg_color'])
            st_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            font_family = self.settings.get('font_family', 'Courier New')

            st = tk.Text(st_frame,
                        bg=self.settings['bg_color'],
                        fg=self.settings['fg_color'],
                        font=(font_family, 14),
                        wrap=tk.WORD,
                        relief=tk.FLAT,
                        borderwidth=1,
                        padx=15, # Padding interno
                        pady=15)
            st.pack(fill=tk.BOTH, expand=True)

            # Aggiungi binding per navigazione con frecce
            st.bind('<Up>', lambda e: st.yview_scroll(-1, "units"))
            st.bind('<Down>', lambda e: st.yview_scroll(1, "units"))
            st.bind('<Prior>', lambda e: st.yview_scroll(-1, "pages"))
            st.bind('<Next>', lambda e: st.yview_scroll(1, "pages"))

            st.insert(tk.END, self.thinking_text)
            st.config(state=tk.DISABLED)

            close_button = tk.Button(win, text="CLOSE",
                                     bg='#000000',
                                     fg='#ffffff',
                                     font=(font_family, 14),
                                     relief=tk.FLAT,
                                     command=win.destroy,
                                     cursor='hand2')
            close_button.pack(pady=15) # Più spazio

            win.bind("<Escape>", lambda e: win.destroy())
            st.focus_set()
            self.wait_window(win)

    def send_message(self, event=None):
        message = self.message_entry.get().strip()
        if not message:
            return
            
        self.message_entry.delete(0, tk.END)
        self.add_message(message, 'user')
        
        # Show "thinking" only after user message, before AI response
        self.chat_display.config(state=tk.NORMAL)
        thinking_msg_start = self.chat_display.index(tk.END + " -1c linestart")
        self.chat_display.insert(tk.END, "\n... thinking ...\n", 'system')
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        self.update_idletasks()
        
        try:
            response = self.chatbot.chat(message)
            self.thinking_text = extract_thinking(response)
            cleaned_response = clean_thinking(response)
            
            # Remove "thinking" message
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(thinking_msg_start, tk.END)
            self.chat_display.config(state=tk.DISABLED)

            self.add_message(cleaned_response, 'assistant')
        except Exception as e:
            # Remove "thinking" message
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(thinking_msg_start, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.add_message(f"Ho riscontrato un problema: {str(e)}", 'error')
            print(f"Errore durante send_message/chatbot.chat: {e}")


# Utility functions
def clean_thinking(response):
    """Rimuove i tag <think> e contenuti correlati in modo più robusto"""
    if not response:
        return ""
    
    # Rimuove tag <think>...</think> completi (anche su più righe)
    cleaned = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL | re.IGNORECASE)
    
    # Rimuove tag <think> aperti ma non chiusi (può succedere con risposte troncate)
    cleaned = re.sub(r"<think>.*$", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # Rimuove eventuali tag </think> rimasti senza apertura
    cleaned = re.sub(r"</think>", "", cleaned, flags=re.IGNORECASE)
    
    # Rimuove righe vuote multiple e spazi extra
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
    
    return cleaned.strip()

def extract_thinking(response):
    """Estrae il contenuto dei tag <think> in modo più robusto"""
    if not response:
        return ""
    
    # Cerca il primo tag <think>...</think> completo
    m = re.search(r"<think>(.*?)</think>", response, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    
    # Se non trova un tag completo, cerca un tag aperto e prende tutto fino alla fine
    m = re.search(r"<think>(.*?)$", response, re.DOTALL | re.IGNORECASE)
    if m:
        content = m.group(1).strip()
        # Limita la lunghezza per evitare testi troppo lunghi
        if len(content) > 2000:
            content = content[:2000] + "...\n[Contenuto troncato - ragionamento molto lungo]"
        return content
    
    return ""


def create_chat_screen(parent, journal_dir: Path, settings: dict, on_back_callback, memory: UnifiedMemory = None):
    """Factory function to create minimal chat screen"""
    # Settings are now handled internally in ChatScreen for minimal design
    return ChatScreen(parent, journal_dir, settings, on_back_callback, memory=memory)
