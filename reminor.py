#!/usr/bin/env python3
"""
MySoul Extreme Journal - Advanced Terminal-Style Journal
With home menu, calendar navigation, global search, and settings
Adapted for 400x300 display.
"""

import customtkinter as ctk
import tkinter as tk  # Manteniamo anche tkinter per alcune funzionalitÃ  specifiche
from tkinter import font as tkfont # Assicurarsi che sia importato
import os
import datetime
import time
from pathlib import Path
import json
import calendar
from tkinter import colorchooser
# Rimosse importazioni matplotlib non piÃ¹ necessarie per show_insights
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re
# import numpy as np # Rimosso se non usato altrove, altrimenti lasciare
from collections import defaultdict # Rimosso se non usato altrove, altrimenti lasciare
from chatbot import create_chat_screen 
from dotenv import load_dotenv
load_dotenv()
from enhanced_emotions_analyzer import EnhancedEmotionsAnalyzer
# Usa Memvid per memoria leggera e veloce
try:
    from memvid_memory import MemvidMemory as UnifiedMemory
    USING_MEMVID = True
except ImportError:
    from memory_system import UnifiedMemory
    USING_MEMVID = False
# GiÃ  importato sopra
from stats_dashboard import StatsDashboard

class ReminorApp: # Renamed from MySoulExtremeJournal
    """
    Main application class for Reminor, an AI-Powered Personal Journal.
    Manages the user interface, data storage, and application logic.
    (Formerly MySoulExtremeJournal. If a specific docstring existed, it should be reviewed and merged.)
    """
    def __init__(self):
        # Configurazione CustomTkinter
        ctk.set_appearance_mode("dark")  # ModalitÃ  scura
        ctk.set_default_color_theme("blue")  # Tema colore blu di CustomTkinter (più neutro per tema Notte)
        
        # Cartella journal nella directory di Reminor
        self.journal_dir = Path(__file__).parent / "journal"
        self.journal_dir.mkdir(exist_ok=True)
        self.settings_file = self.journal_dir / "settings.json"
        
        self.settings = {
            'bg_color': '#000000',  # Tema Notte come default
            'fg_color': '#ffffff',  # Bianco su nero per tema Notte
            'auto_save': True,
            'auto_save_interval': 180,
            'cloud_sync': False,
            'cloud_service': None,
            'cloud_account': None,
            'editor_font_size': 24,
            'font_family': 'Courier New',  # Font di default
            'first_run': True,  # Flag per primo avvio
            'user_name': '',    # Nome dell'utente
        }
        self.load_settings()

        self.editor_font_range = (16, 40)
        legacy_font = self.settings.get('font_size')
        if legacy_font is not None and 'editor_font_size' not in self.settings:
            self.settings['editor_font_size'] = legacy_font
        try:
            editor_font = int(self.settings.get('editor_font_size', 24))
        except (TypeError, ValueError):
            editor_font = 24
        editor_font = max(self.editor_font_range[0], min(editor_font, self.editor_font_range[1]))
        self.settings['editor_font_size'] = editor_font
        if 'font_size' in self.settings:
            del self.settings['font_size']
        self.editor_font_size = editor_font

        self.current_date = datetime.datetime.now()
        self.filename = f"{self.current_date.strftime('%Y-%m-%d')}.txt"
        self.filepath = self.journal_dir / self.filename
        self.last_save_time = time.time()
        self.current_screen = 'home'
        self.menu_selection = 0
        self.scroll_speed = 1
        self.scroll_timer_id = None
        
        self.emotions_analyzer = EnhancedEmotionsAnalyzer(self.journal_dir)
        self.memory = UnifiedMemory(self.journal_dir)
        self.chatbot_screen = None
        self.screensaver_manager = None

        # Stato per la schermata Insights
        self.insights_num_days_to_display = 7 
        self.insights_current_week_offset = 0 # 0 per la settimana corrente, 1 per la precedente, ecc.
        self.insights_matrix_frame = None # Frame che conterrÃ  la matrice
        self.insights_week_title_label = None # Label per il titolo della settimana

        self.setup_window()

        # Ottieni lista font monospace disponibili (dopo setup_window)
        self.available_fonts = self.get_monospace_fonts()

        self.setup_screensaver()

        # Controlla se è il primo avvio
        if self.settings.get('first_run', True):
            self.show_onboarding()
        else:
            self.show_home_screen()
        
    def load_settings(self):
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
            except Exception as e:
                # print(f"Error loading settings: {e}")
                pass
                
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            # print(f"Error saving settings: {e}")
            pass
            
    def setup_window(self):
        """Setup the main window"""
        self.root = ctk.CTk()  # Usa CTk invece di Tk
        self.root.title("Reminor")
        self.root.geometry("720x720")  # Target display 720x720
        self.root.configure(fg_color='black')  # fg_color invece di bg per CTk
        self.root.config(cursor="none")

        # Imposta l'icona della finestra
        import platform

        if platform.system() == 'Windows':
            # Su Windows usa direttamente il file .ico
            ico_path = Path(__file__).parent / "Rreminor.ico"
            if ico_path.exists():
                try:
                    self.root.iconbitmap(str(ico_path))

                    # Forza Windows a usare l'icona anche nella taskbar
                    try:
                        import ctypes
                        myappid = 'reminor.journal.app.1'  # arbitrary string
                        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                    except Exception as appid_error:
                        print(f"Impossibile impostare AppUserModelID: {appid_error}")
                except Exception as e:
                    print(f"Impossibile caricare l'icona .ico: {e}")
        else:
            # Su altri sistemi usa il PNG
            icon_path = Path(__file__).parent / "Rreminor.png"
            if icon_path.exists():
                try:
                    from PIL import Image, ImageTk
                    icon_image = Image.open(icon_path)
                    icon_photo = ImageTk.PhotoImage(icon_image)
                    self.root.iconphoto(True, icon_photo)
                except Exception as e:
                    print(f"Impossibile caricare l'icona: {e}")

        # Create main container con CTkFrame
        self.main_frame = ctk.CTkFrame(self.root, fg_color=self.settings['bg_color'])
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid for responsiveness (still useful for internal frame layouts)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Bind global keys
        self.root.bind('<Escape>', self.handle_escape)
        # Aggiungi combinazioni per uscire dal fullscreen e chiudere l'app
        self.root.bind('<Alt-F4>', lambda e: self.on_closing())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<F11>', self.toggle_fullscreen)
        
        # Window resize handling (less critical for fixed size, but harmless)
        self.root.bind('<Configure>', self.on_window_resize)

    def get_monospace_fonts(self):
        """Ottiene lista dei font monospace disponibili sul sistema"""
        try:
            # Lista di font monospace comuni su tutti i sistemi
            common_monospace = [
                'Courier New', 'Courier', 'Consolas', 'Monaco', 'Menlo',
                'DejaVu Sans Mono', 'Liberation Mono', 'Ubuntu Mono',
                'Roboto Mono', 'Source Code Pro', 'Fira Code', 'Fira Mono',
                'Inconsolata', 'Anonymous Pro', 'Lucida Console',
                'Cascadia Code', 'Cascadia Mono', 'JetBrains Mono',
                'Space Mono', 'Noto Mono', 'IBM Plex Mono', 'Hack',
                'OCR A Extended', 'Unispace'
            ]

            # Ottieni tutti i font disponibili sul sistema
            all_fonts = list(tkfont.families())

            # Filtra solo i font monospace disponibili
            available_monospace = []

            # Prima aggiungi i font dalla lista comune se presenti
            for font in common_monospace:
                if font in all_fonts:
                    available_monospace.append(font)

            # Poi cerca altri font monospace con pattern nel nome
            # Questo cattura varianti come "JetBrainsMonoNerdFontMono-Medium"
            monospace_keywords = ['mono', 'courier', 'console', 'code', 'cascadia',
                                 'jetbrains', 'nerd', 'hack', 'space mono', 'unispace']

            for font_name in all_fonts:
                font_lower = font_name.lower()
                # Aggiungi se contiene keyword monospace e non è già nella lista
                if font_name not in available_monospace:
                    if any(keyword in font_lower for keyword in monospace_keywords):
                        available_monospace.append(font_name)

            # Assicurati che ci sia almeno un font disponibile
            if not available_monospace:
                available_monospace = ['Courier New', 'Courier', 'TkFixedFont']

            # Rimuovi duplicati e ordina
            available_monospace = sorted(list(set(available_monospace)))

            return available_monospace
        except Exception as e:
            print(f"Errore nel recupero dei font: {e}")
            return ['Courier New', 'Courier']

    def get_font(self, size=16, style='normal'):
        """Helper per ottenere il font corrente dalle impostazioni"""
        font_family = self.settings.get('font_family', 'Courier New')
        if style == 'normal':
            return (font_family, size)
        else:
            return (font_family, size, style)

    def clear_screen(self):
        """Clear the main frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        # Reset background color based on current screen
        if hasattr(self, 'current_screen'):
            if self.current_screen == 'home':
                # Usa bianco per la home screen minimale
                self.main_frame.configure(fg_color='#ffffff')
            else:
                # Usa il colore delle impostazioni per gli altri screen
                self.main_frame.configure(fg_color=self.settings['bg_color'])
            
    def get_simple_title_text(self):
        """Return simple text title"""
        return "Reminor"
    
    def get_title_font(self, size=28, style='bold'):
        """Get title font with fallback"""
        try:
            import tkinter.font as tkFont
            # Try different variations of Gladiola font name - COMMENTED OUT FOR TESTING
            # font_variations = [
            #     'Gladiola Regular',
            #     'GladiolaRegular',
            #     'Gladiola-Regular',
            #     'GladiolaRegular-Regular',
            #     'Gladiola',
            #     'gladiola regular',
            #     'GLADIOLA REGULAR'
            # ]
            
            # for font_name in font_variations:
            #     try:
            #         font = tkFont.Font(family=font_name, size=size, weight=style)
            #         actual = font.actual()
            #         # If the actual font family contains 'gladiola', use it
            #         if 'gladiola' in actual['family'].lower():
            #             return (font_name, size, style)
            #     except:
            #         continue
            
            # Fallback to Courier New if no Gladiola variant is available
            return ('Courier New', size, style)
        except:
            # Ultimate fallback
            return ('Courier New', size, style)

    def get_personalized_greeting(self, default_message="Ciao"):
        """Ottiene un saluto personalizzato con il nome dell'utente"""
        user_name = self.settings.get('user_name', '').strip()
        if user_name:
            return f"Ciao {user_name}"
        return default_message

    def show_onboarding(self):
        """Mostra la schermata di onboarding per nuovi utenti"""
        self.current_screen = 'onboarding'
        self.onboarding_screen = OnboardingScreen(self)

    def show_home_screen(self):
        """Show the home menu screen"""
        self.current_screen = 'home'
        self.clear_screen()
        
        # Container con tkinter standard - usa tema dalle impostazioni
        container = tk.Frame(self.main_frame, 
                           bg=self.settings['bg_color'],  # Usa colore tema
                           relief=tk.FLAT,
                           borderwidth=0)
        container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Titolo minimale senza decorazioni
        self.home_title_label = tk.Label(container, 
                             text=self.get_simple_title_text(),
                             bg=self.settings['bg_color'],
                             fg=self.settings['fg_color'],  # Usa colore tema
                             font=('Courier New', 42, 'bold'))  # Font Courier New
        self.home_title_label.pack(pady=(80, 40))

        self.menu_items = [
            ("📝 Nuova pagina", self.new_journal_page),  # Shortened
            ("📅 Calendario", self.show_calendar),
            ("🔍 Ricerca", self.show_search),            # Shortened
            ("🤖 Chat Pensieri", self.show_chat),        # Shortened
            ("📊 Emozioni", self.show_insights),         # Shortened
            ("📊 Statistiche", self.show_stats_dashboard),
            ("⚙️ Impostazioni", self.show_settings)
        ]

        # Frame per centrare i menu items
        menu_frame = tk.Frame(container, bg=self.settings['bg_color'])
        menu_frame.pack(expand=True)

        self.menu_labels = []
        for i, (text, _) in enumerate(self.menu_items):
            label = tk.Label(menu_frame, 
                           text=text,
                           bg=self.settings['bg_color'],
                           fg=self.settings['fg_color'],
                           font=('Courier New', 20),
                           padx=20,
                           pady=8,  # Padding verticale ridotto
                           anchor='center',
                           width=20)  # Larghezza fissa per allineamento
            label.pack(pady=3, anchor='center')  # Spacing ridotto tra voci
            self.menu_labels.append(label)

        # Istruzioni in basso
        self.home_instructions_label = tk.Label(container,
                              text="↑↓ Naviga | ENTER Selez. | ESC Esci",  # Shortened
                              bg=self.settings['bg_color'],
                              fg=self.settings['fg_color'],  # Usa colore tema
                              font=('Courier New', 18),
                              anchor='center')
        self.home_instructions_label.pack(side=tk.BOTTOM, pady=(10, 40), anchor='center')  # PiÃ¹ spazio in basso

        
        self.menu_selection = 0
        self.update_menu_selection() # Questa chiamata dovrebbe configurare i colori correttamente
        
        # Ripristina i binding del menu principale
        # (se arrivano da altri screen che li avevano modificati)
        self.root.bind('<Up>', self.menu_up)
        self.root.bind('<Down>', self.menu_down)
        self.root.bind('<Return>', self.menu_select)
        self.root.bind('<Escape>', self.handle_escape)  # Ripristina anche ESC
        
    def update_menu_selection(self):
        """Update menu item highlighting"""
        for i, button in enumerate(self.menu_labels):
            if i == self.menu_selection:
                # Selezionato: inverte i colori del tema
                button.configure(bg=self.settings['fg_color'],
                           fg=self.settings['bg_color'],
                           relief=tk.FLAT)
            else:
                # Non selezionato: usa colori del tema
                button.configure(bg=self.settings['bg_color'],
                           fg=self.settings['fg_color'],
                           relief=tk.FLAT)
                
    def menu_up(self, event):
        if self.current_screen == 'home':
            self.menu_selection = (self.menu_selection - 1) % len(self.menu_items)
            self.update_menu_selection()
            
    def menu_down(self, event):
        if self.current_screen == 'home':
            self.menu_selection = (self.menu_selection + 1) % len(self.menu_items)
            self.update_menu_selection()
            
    def menu_select(self, event):
        if self.current_screen == 'home':
            _, action = self.menu_items[self.menu_selection]
            action()
            
    def new_journal_page(self):
        self.current_date = datetime.datetime.now()
        self.filename = f"{self.current_date.strftime('%Y-%m-%d')}.txt"
        self.filepath = self.journal_dir / self.filename
        self.show_editor()
        
    def show_editor(self):
        self.current_screen = 'editor'
        self.clear_screen()

        self.editor_frame = ctk.CTkFrame(self.main_frame, fg_color=self.settings['bg_color']) # Rinominato per chiarezza
        self.editor_frame.pack(fill=tk.BOTH, expand=True)

        # Format the date for the title
        try:
            import locale
            try:
                locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
            except locale.Error:
                locale.setlocale(locale.LC_TIME, 'Italian_Italy.1252') # For Windows
            formatted_date = self.current_date.strftime('%d %B %Y')
        except Exception: 
            formatted_date = self.current_date.strftime('%Y-%m-%d')


        self.editor_title_label = ctk.CTkLabel(self.editor_frame, text=f"📝 {formatted_date}",
                               fg_color="transparent",
                               text_color=self.settings['fg_color'],
                               font=('Courier New', 34, 'bold'))
        self.editor_title_label.pack(pady=20) # More space

        # Testo completo dei comandi (nascosto di default)
        self.full_commands_text = "↑↓ Scorri | Ctrl+/- Zoom | F2 Emozioni | Ctrl-S Salva | ESC Menu"
        # Testo semplificato (mostrato di default)
        self.simple_commands_text = "F3 per mostrare/nascondere comandi"

        self.status_label = ctk.CTkLabel(self.editor_frame,
                                  text=self.simple_commands_text,
                                  fg_color="transparent",
                                  text_color="#888888",  # Grigio più tenue
                                  font=('Courier New', 16))  # Font più piccolo
        self.status_label.pack(pady=5) # Meno spazio

        # Stato per il toggle dei comandi
        self.showing_commands = False


        # Large text frame with generous padding
        self.text_widget_frame = ctk.CTkFrame(self.editor_frame, fg_color=self.settings['bg_color'])
        self.text_widget_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20) # Padding generoso
        
        self.text = ctk.CTkTextbox(self.text_widget_frame,
                            fg_color=self.settings['bg_color'],
                            text_color=self.settings['fg_color'],
                            font=self.get_font(self.editor_font_size),
                            wrap="word", # Wrap text at word boundaries
                            height=400, # Area di testo molto piÃ¹ grande
                            corner_radius=0, # Angoli squadrati per mantenere lo stile
                            border_width=0,
                            scrollbar_button_color=self.settings['bg_color'],  # Nasconde scrollbar
                            scrollbar_button_hover_color=self.settings['bg_color'])  # Nasconde scrollbar anche su hover
        self.text.pack(fill=tk.BOTH, expand=True)
        self.apply_editor_font_size()

        # Frame per la visualizzazione delle emozioni (inizialmente vuoto e non packato direttamente sotto text_widget_frame)
        self.emotions_display_frame = tk.Frame(self.editor_frame, bg=self.settings['bg_color'])
        # Non fare .pack() qui, verrÃ  gestito dal toggle

        self.editor_showing_emotions = False # Stato per il toggle

        # Rimuoviamo la scrollbar laterale come richiesto, useremo tasti freccia
        
        # Binding per i tasti freccia su/giÃ¹ per scorrere il testo
        self.text.bind('<Up>', self.scroll_text_up)
        self.text.bind('<Down>', self.scroll_text_down)
        # Per rilevare rilascio tasti ed evitare accelerazione continua
        self.text.bind('<KeyRelease-Up>', self.reset_scroll_speed)
        self.text.bind('<KeyRelease-Down>', self.reset_scroll_speed)
        
        self.root.bind('<Control-s>', self.save_file)
        self.root.bind('<F2>', self.toggle_emotion_display_in_editor) # Nuovo Binding
        self.root.bind('<F3>', self.toggle_commands_display) # Toggle comandi
        self.root.bind('<Control-plus>', self.increase_editor_font)
        self.root.bind('<Control-equal>', self.increase_editor_font)
        self.root.bind('<Control-KP_Add>', self.increase_editor_font)
        self.root.bind('<Control-minus>', self.decrease_editor_font)
        self.root.bind('<Control-KP_Subtract>', self.decrease_editor_font)

        self.load_file()
        self.text.focus_set()

    def toggle_emotion_display_in_editor(self, event=None):
        if self.current_screen != 'editor':
            return

        if not self.editor_showing_emotions:
            # Nascondi testo, mostra emozioni
            self.text_widget_frame.pack_forget() # Nasconde il frame che contiene il text widget
            
            self.load_and_display_emotions_for_entry() # Popola il frame delle emozioni
            self.emotions_display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # Mostra il frame delle emozioni
            
            self.editor_showing_emotions = True
            if hasattr(self, 'emotions_display_frame_content') and self.emotions_display_frame_content: # Nuovo sub-frame per focus
                self.emotions_display_frame_content.focus_set()
            elif self.emotions_display_frame.winfo_children(): # Fallback se il sub-frame non c'Ã¨ o Ã¨ vuoto
                 self.emotions_display_frame.winfo_children()[0].focus_set() # Focus sul primo elemento
            else:
                self.emotions_display_frame.focus_set()


        else:
            # Nascondi emozioni, mostra testo
            self.emotions_display_frame.pack_forget()
            self.text_widget_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # Rimostra il frame del testo
            self.editor_showing_emotions = False
            self.text.focus_set()
        return "break" # Per evitare che l'evento F2 si propaghi ulteriormente


    def apply_editor_font_size(self):
        """Aggiorna il font del campo testo dell'editor in base alla dimensione corrente"""
        try:
            if hasattr(self, 'text') and self.text and self.text.winfo_exists():
                self.text.configure(font=self.get_font(self.editor_font_size))
        except tk.TclError:
            pass

    def adjust_editor_font(self, delta):
        """Modifica la dimensione del font dell'editor rispettando i limiti"""
        if self.current_screen != 'editor':
            return 'break'

        new_size = self.editor_font_size + delta
        new_size = max(self.editor_font_range[0], min(new_size, self.editor_font_range[1]))
        if new_size == self.editor_font_size:
            return 'break'

        self.editor_font_size = new_size
        self.settings['editor_font_size'] = new_size
        self.apply_editor_font_size()
        self.save_settings()
        self.show_status(f"Zoom {new_size}pt")
        return 'break'

    def increase_editor_font(self, event=None):
        return self.adjust_editor_font(1)

    def decrease_editor_font(self, event=None):
        return self.adjust_editor_font(-1)

    def toggle_commands_display(self, event=None):
        """Toggle tra visualizzazione comandi completi e semplificati"""
        if self.current_screen != 'editor':
            return

        self.showing_commands = not self.showing_commands

        if self.showing_commands:
            # Mostra comandi completi
            self.status_label.configure(
                text=self.full_commands_text,
                text_color=self.settings['fg_color'],  # Colore normale
                font=('Courier New', 22)  # Font normale
            )
        else:
            # Mostra solo hint F3
            self.status_label.configure(
                text=self.simple_commands_text,
                text_color="#888888",  # Grigio tenue
                font=('Courier New', 16)  # Font più piccolo
            )

    def load_and_display_emotions_for_entry(self):
        """Carica e visualizza le emozioni per la pagina di diario corrente."""
        # Pulisci il contenuto precedente del frame delle emozioni
        for widget in self.emotions_display_frame.winfo_children():
            widget.destroy()

        # Nuovo sub-frame per permettere lo scroll se necessario e per il focus
        # Questo frame interno conterrÃ  effettivamente le etichette delle emozioni
        self.emotions_display_frame_content = tk.Frame(self.emotions_display_frame, bg=self.settings['bg_color'])
        self.emotions_display_frame_content.pack(fill=tk.BOTH, expand=True)

        # Estrai data dal nome file
        date_str = self.filepath.stem  # Es: "2025-01-13"

        # Carica emozioni da Memvid (nuovo sistema)
        emotion_scores = None
        if hasattr(self, 'memory') and self.memory:
            emotion_scores = self.memory.get_emotions(date_str)

        if emotion_scores:
            try:
                if not hasattr(self, 'emotions_analyzer') or not hasattr(self.emotions_analyzer, 'emotions_list'):
                    error_label = tk.Label(self.emotions_display_frame_content,
                                           text="Analizzatore emozioni non pronto.",
                                           bg=self.settings['bg_color'], fg=self.settings['fg_color'],
                                           font=('Courier New', 12))
                    error_label.pack(pady=10)
                    return

                emotions_title_label = tk.Label(self.emotions_display_frame_content,
                                              text="--- Analisi Emozioni del Giorno ---",
                                              bg=self.settings['bg_color'],
                                              fg=self.settings['fg_color'],
                                              font=('Courier New', 24, 'bold'))
                emotions_title_label.pack(anchor='center', pady=(20,30))

                for emotion_name in self.emotions_analyzer.emotions_list:
                    score = emotion_scores.get(emotion_name, 0.0)
                    bar_length = 10
                    filled_chars = round(score * bar_length)
                    empty_chars = bar_length - filled_chars
                    bar = "=" * filled_chars + "-" * empty_chars  # ASCII compatibile
                    emotion_text = f"{emotion_name.capitalize():<12}: |{bar}|"
                    label = tk.Label(self.emotions_display_frame_content,
                                     text=emotion_text,
                                     bg=self.settings['bg_color'],
                                     fg=self.settings['fg_color'],
                                     font=('Courier New', 22),
                                     anchor='w')
                    label.pack(fill=tk.X, padx=40, pady=5)
            except Exception as e:
                error_label = tk.Label(self.emotions_display_frame_content,
                                       text=f"Errore caricando emozioni: {e}",
                                       bg=self.settings['bg_color'], fg=self.settings['fg_color'],
                                       font=('Courier New', 20))
                error_label.pack(pady=20)
        else:
            no_file_label = tk.Label(self.emotions_display_frame_content,
                                     text="Emozioni non ancora analizzate per questo giorno.",
                                     bg=self.settings['bg_color'], fg=self.settings['fg_color'],
                                     font=('Courier New', 20))
            no_file_label.pack(pady=20)
        
        # Aggiungi istruzioni per tornare indietro
        instructions_label = tk.Label(self.emotions_display_frame_content,
                                      text="F2 per tornare al testo | ESC per Menu",
                                      bg=self.settings['bg_color'], fg=self.settings['fg_color'],
                                      font=('Courier New', 20)) # Font piÃ¹ grande
        instructions_label.pack(side=tk.BOTTOM, pady=15) # PiÃ¹ spazio
        
        # Binding per lo scroll con frecce anche nella vista emozioni (se diventa scrollabile)
        # Per ora, non implemento uno scroll complesso qui, ma il focus Ã¨ importante.
        # Il focus sul frame stesso o sul primo figlio puÃ² aiutare con i binding globali se necessario.
        # self.emotions_display_frame_content.bind('<Up>', lambda e: print("Up in emotions")) # Esempio
        # self.emotions_display_frame_content.bind('<Down>', lambda e: print("Down in emotions")) # Esempio


    def show_calendar(self):
        self.current_screen = 'calendar'
        self.clear_screen()
        
        cal_frame_container = tk.Frame(self.main_frame, bg=self.settings['bg_color'],
                           highlightbackground=self.settings['fg_color'],
                           highlightthickness=2) # Border piÃ¹ spesso
        cal_frame_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30) # Padding generoso
        
        title = tk.Label(cal_frame_container, text="📅 CALENDARIO",  # Shortened
                        bg=self.settings['bg_color'],
                        fg=self.settings['fg_color'],
                        font=('Courier', 24, 'bold')) # Titolo molto piÃ¹ grande
        title.pack(pady=20) # PiÃ¹ spazio
        
        self.cal_year = self.current_date.year
        self.cal_month = self.current_date.month
        self.cal_day = self.current_date.day
        self.cal_mode = 'day'
        
        # Variabili per tracciare il mese/anno corrente del calendario
        self.current_cal_month = None
        self.current_cal_year = None
        
        nav_frame = tk.Frame(cal_frame_container, bg=self.settings['bg_color'])
        nav_frame.pack(pady=15) # PiÃ¹ spazio
        
        self.month_label = tk.Label(nav_frame,
                                  text=f"{calendar.month_name[self.cal_month]} {self.cal_year}",
                                  bg=self.settings['bg_color'],
                                  fg=self.settings['fg_color'],
                                  font=('Courier New', 24, 'bold')) # Font molto piÃ¹ grande
        self.month_label.pack(pady=10) # PiÃ¹ spazio
        
        self.cal_frame = tk.Frame(cal_frame_container, bg=self.settings['bg_color'])
        self.cal_frame.pack(pady=20, fill=tk.BOTH, expand=True) # PiÃ¹ spazio
        
        self.cal_instructions = tk.Label(cal_frame_container,
                              text="Naviga | ENTER Apri | ESC Menu", # Shortened
                              bg=self.settings['bg_color'],
                              fg=self.settings['fg_color'],
                              font=('Courier New', 20)) # Font piÃ¹ grande
        self.cal_instructions.pack(pady=15) # PiÃ¹ spazio
        
        self.show_month_calendar()
        
        self.root.bind('<Left>', self.cal_navigate)
        self.root.bind('<Right>', self.cal_navigate)
        self.root.bind('<Up>', self.cal_navigate)
        self.root.bind('<Down>', self.cal_navigate)
        self.root.bind('<Return>', self.open_selected_day)
        
    def update_calendar_selection(self):
        """Aggiorna solo la selezione del calendario senza ricreare tutto"""
        # Aggiorna solo il label del mese se necessario
        if self.cal_mode == 'month':
            self.month_label.config(bg=self.settings['fg_color'], fg=self.settings['bg_color'])
            self.cal_instructions.config(text="←→ Mese | ↓ Giorni | ESC Menu")
        else:
            self.month_label.config(bg=self.settings['bg_color'], fg=self.settings['fg_color'])
            self.cal_instructions.config(text="Naviga | ENTER Apri | ESC Menu")
        
        # Se abbiamo cambiato mese o anno, dobbiamo ricreare il calendario
        if not hasattr(self, 'current_cal_month') or not hasattr(self, 'current_cal_year') or \
           self.current_cal_month != self.cal_month or self.current_cal_year != self.cal_year:
            self.current_cal_month = self.cal_month
            self.current_cal_year = self.cal_year
            self.show_month_calendar()
            return
        
        # Altrimenti aggiorna solo l'evidenziazione dei giorni
        if hasattr(self, 'day_labels') and self.day_labels:
            for day, label in self.day_labels.items():
                if day == self.cal_day and self.cal_mode == 'day':
                    label.config(bg=self.settings['fg_color'], fg=self.settings['bg_color'])
                else:
                    label.config(bg=self.settings['bg_color'], fg=self.settings['fg_color'])
    
    def show_month_calendar(self):
        for widget in self.cal_frame.winfo_children():
            widget.destroy()
        
        grid_container = tk.Frame(self.cal_frame, bg=self.settings['bg_color'])
        grid_container.pack(expand=True)
            
        if self.cal_mode == 'month':
            self.month_label.config(bg=self.settings['fg_color'], fg=self.settings['bg_color'])
            self.cal_instructions.config(text="←→ Mese | ↓ Giorni | ESC Menu")  # Shortened
        else:
            self.month_label.config(bg=self.settings['bg_color'], fg=self.settings['fg_color'])
            self.cal_instructions.config(text="Naviga | ENTER Apri | ESC Menu") # Shortened
            
        days = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'] # 3-letter days
        for i, day_name in enumerate(days):
            label = tk.Label(grid_container, text=day_name,
                           bg=self.settings['bg_color'],
                           fg=self.settings['fg_color'],
                           font=('Courier', 16, 'bold'), # Font molto piÃ¹ grande
                           width=8, # Larghezza raddoppiata (era 4)
                           height=2) # Altezza aumentata
            label.grid(row=0, column=i, padx=3, pady=3, sticky='nsew') # Padding aumentato
            
        calendar.setfirstweekday(0)
        cal = calendar.monthcalendar(self.cal_year, self.cal_month)
        
        self.day_labels = {}
        self.cal_grid = {}
        
        for week_num, week in enumerate(cal, 1):
            for day_num_idx, day_val in enumerate(week):
                if day_val == 0:
                    empty_label = tk.Label(grid_container, text="",
                                         bg=self.settings['bg_color'],
                                         width=8, height=2) # Dimensioni aumentate
                    empty_label.grid(row=week_num, column=day_num_idx, padx=3, pady=3)
                    continue
                    
                self.cal_grid[day_val] = (week_num, day_num_idx)
                
                date_str = f"{self.cal_year}-{self.cal_month:02d}-{day_val:02d}"
                file_path = self.journal_dir / f"{date_str}.txt"
                has_content = file_path.exists() and file_path.stat().st_size > 0
                
                text_content = f"{day_val:2d}"
                if has_content:
                    text_content = f"[{day_val:2d}]" # Keep brackets for indication
                    
                label = tk.Label(grid_container, text=text_content,
                               bg=self.settings['bg_color'],
                               fg=self.settings['fg_color'],
                               font=('Courier New', 22), # Font molto piÃ¹ grande (era 9)
                               width=8, # Larghezza raddoppiata (era 4)
                               height=2, # Altezza aumentata (era 1)
                               relief=tk.FLAT)
                               
                if day_val == self.cal_day and self.cal_mode == 'day':
                    label.config(bg=self.settings['fg_color'], fg=self.settings['bg_color'])
                    
                label.grid(row=week_num, column=day_num_idx, padx=3, pady=3, sticky='nsew') # Padding aumentato
                self.day_labels[day_val] = label
                
        for i in range(7):
            grid_container.columnconfigure(i, weight=1)
                
    def show_search(self):
        self.current_screen = 'search'
        self.clear_screen()
        
        search_frame = tk.Frame(self.main_frame, bg=self.settings['bg_color'],
                              highlightbackground=self.settings['fg_color'],
                              highlightthickness=2) # Border piÃ¹ spesso
        search_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30) # Padding generoso
        
        title = tk.Label(search_frame, text="🔍 RICERCA",  # Shortened
                        bg=self.settings['bg_color'],
                        fg=self.settings['fg_color'],
                        font=('Courier', 24, 'bold')) # Font molto piÃ¹ grande
        title.pack(pady=20) # PiÃ¹ spazio
        
        input_frame = tk.Frame(search_frame, bg=self.settings['bg_color'])
        input_frame.pack(pady=15) # PiÃ¹ spazio
        
        tk.Label(input_frame, text="Cerca:",
                bg=self.settings['bg_color'],
                fg=self.settings['fg_color'],
                font=('Courier New', 20)).pack(side=tk.LEFT, padx=10) # Font e padding maggiori
                
        self.search_entry = tk.Entry(input_frame,
                                   bg=self.settings['bg_color'],
                                   fg=self.settings['fg_color'],
                                   insertbackground=self.settings['fg_color'],
                                   font=('Courier New', 22), # Font piÃ¹ grande
                                   width=40) # Larghezza raddoppiata
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.focus_set()
        
        results_frame = tk.Frame(search_frame, bg=self.settings['bg_color'])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20) # PiÃ¹ padding
        
        # Container per i risultati di ricerca navigabili
        self.results_canvas = tk.Canvas(results_frame, bg=self.settings['bg_color'], highlightthickness=0, bd=0)
        self.results_canvas.pack(fill=tk.BOTH, expand=True)

        self.results_container = tk.Frame(self.results_canvas, bg=self.settings['bg_color'])
        self.results_window = self.results_canvas.create_window((0, 0), window=self.results_container, anchor='nw')

        def _sync_results_width(event):
            try:
                self.results_canvas.itemconfigure(self.results_window, width=event.width)
            except tk.TclError:
                pass

        def _update_results_scrollregion(event=None):
            try:
                self.results_canvas.configure(scrollregion=self.results_canvas.bbox('all'))
            except tk.TclError:
                pass

        self.results_canvas.bind('<Configure>', _sync_results_width)
        self.results_container.bind('<Configure>', _update_results_scrollregion)

        # Inizializza variabili per la navigazione dei risultati
        self.search_results = []  # Lista dei risultati trovati
        self.search_selection = 0  # Indice del risultato selezionato
        self.search_labels = []   # Labels dei risultati per l'highlighting
        
        instructions = tk.Label(search_frame,
                              text="ENTER Cerca | ↑↓ Naviga risultati | ENTER Apri | ESC Menu",
                              bg=self.settings['bg_color'],
                              fg=self.settings['fg_color'],
                              font=('Courier New', 20)) # Font piÃ¹ grande
        instructions.pack(pady=15) # PiÃ¹ spazio
        
        self.search_entry.bind('<Return>', self.perform_search)
        
        # Bind per navigazione risultati
        self.root.bind('<Up>', self.search_navigate_up)
        self.root.bind('<Down>', self.search_navigate_down)
        self.root.bind('<Return>', self.search_open_selected)
        
    def perform_search(self, event=None):
        query = self.search_entry.get().lower()
        if not query:
            return
            
        # Pulisce i risultati precedenti
        for widget in self.results_container.winfo_children():
            widget.destroy()

        if hasattr(self, 'results_canvas') and self.results_canvas.winfo_exists():
            try:
                self.results_canvas.yview_moveto(0)
            except tk.TclError:
                pass

        self.search_results = []
        self.search_labels = []
        self.search_selection = 0
        
        # Cerca nei file
        for file_path in self.journal_dir.glob("*.txt"):
            # Skip settings file if it's in the journal directory
            if file_path.name == "settings.json":
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                    
                for i, line in enumerate(lines):
                    if query in line.lower():
                        # Trunca le righe lunghe per la visualizzazione
                        display_line = line.strip()
                        if len(display_line) > 50:
                            display_line = display_line[:47] + "..."

                        self.search_results.append({
                            'file': file_path.name,
                            'file_path': file_path,
                            'line_num': i + 1,
                            'line': display_line,
                            'full_line': line.strip()
                        })
            except Exception as e:
                pass
                
        if self.search_results:
            # Crea le label per ogni risultato
            for i, result in enumerate(self.search_results):
                # Accorcia il nome del file per la visualizzazione
                display_file = result['file']
                if len(display_file) > 18:
                    display_file = "..." + display_file[-15:]
                
                result_text = f"📄 {display_file}({result['line_num']}): {result['line']}"
                
                label = tk.Label(self.results_container,
                               text=result_text,
                               bg=self.settings['bg_color'],
                               fg=self.settings['fg_color'],
                               font=('Courier New', max(16, self.editor_font_size - 2)),
                               anchor='w',
                               justify=tk.LEFT,
                               wraplength=600)
                label.pack(fill=tk.X, padx=5, pady=2)
                self.search_labels.append(label)
            
            # Evidenzia il primo risultato
            self.update_search_selection()
            
            # Sposta il focus dalla casella di ricerca ai risultati
            if hasattr(self, 'results_canvas'):
                self.results_canvas.focus_set()
        else:
            no_results_label = tk.Label(self.results_container,
                                      text="Nessun risultato trovato.",
                                      bg=self.settings['bg_color'],
                                      fg=self.settings['fg_color'],
                                      font=('Courier New', max(16, self.editor_font_size - 2)))
            no_results_label.pack(pady=20)
    
    def update_search_selection(self):
        """Aggiorna l'evidenziazione del risultato selezionato"""
        if not self.search_labels:
            return
            
        for i, label in enumerate(self.search_labels):
            if i == self.search_selection:
                label.config(bg=self.settings['fg_color'], fg=self.settings['bg_color'])
            else:
                label.config(bg=self.settings['bg_color'], fg=self.settings['fg_color'])

        self.ensure_search_selection_visible()

    def ensure_search_selection_visible(self):
        """Garantisce che il risultato selezionato sia visibile nel canvas"""
        if not getattr(self, 'results_canvas', None) or not self.search_labels:
            return

        try:
            self.results_canvas.update_idletasks()
            label = self.search_labels[self.search_selection]
            if not label.winfo_exists():
                return

            label_y = label.winfo_y()
            label_h = label.winfo_height()
            canvas_y = self.results_canvas.canvasy(0)
            canvas_h = self.results_canvas.winfo_height()
            canvas_bottom = canvas_y + canvas_h

            if label_y < canvas_y:
                total_height = max(1, self.results_container.winfo_height())
                self.results_canvas.yview_moveto(label_y / total_height)
            elif label_y + label_h > canvas_bottom:
                total_height = max(1, self.results_container.winfo_height())
                target = (label_y + label_h - canvas_h) / total_height
                self.results_canvas.yview_moveto(max(0, target))
        except tk.TclError:
            pass
    
    def search_navigate_up(self, event):
        """Naviga verso l'alto nei risultati di ricerca"""
        if self.current_screen == 'search' and self.search_results:
            self.search_selection = (self.search_selection - 1) % len(self.search_results)
            if hasattr(self, 'results_canvas'):
                self.results_canvas.focus_set()
            self.update_search_selection()
            return "break"
    
    def search_navigate_down(self, event):
        """Naviga verso il basso nei risultati di ricerca"""
        if self.current_screen == 'search' and self.search_results:
            self.search_selection = (self.search_selection + 1) % len(self.search_results)
            if hasattr(self, 'results_canvas'):
                self.results_canvas.focus_set()
            self.update_search_selection()
            return "break"
    
    def search_open_selected(self, event):
        """Apre il file selezionato nell'editor"""
        if self.current_screen == 'search' and self.search_results and len(self.search_results) > self.search_selection:
            # Se il focus Ã¨ sulla casella di ricerca, esegui la ricerca
            if event.widget == self.search_entry:
                self.perform_search()
                return "break"
            
            # Altrimenti apri il risultato selezionato
            selected_result = self.search_results[self.search_selection]
            
            # Imposta la data e il file da aprire
            try:
                # Estrae la data dal nome del file (formato: YYYY-MM-DD.txt)
                date_str = selected_result['file'].replace('.txt', '')
                date_parts = date_str.split('-')
                if len(date_parts) == 3:
                    year, month, day = map(int, date_parts)
                    self.current_date = datetime.datetime(year, month, day)
                    self.filename = selected_result['file']
                    self.filepath = selected_result['file_path']
                    
                    # Apri l'editor per quel giorno
                    self.show_editor()
                    
                    # Opzionalmente, sposta il cursore alla riga trovata
                    if hasattr(self, 'text') and self.text:
                        # Vai alla riga specifica
                        line_num = selected_result['line_num']
                        self.text.mark_set(tk.INSERT, f"{line_num}.0")
                        self.text.see(f"{line_num}.0")
                        
            except Exception as e:
                print(f"Errore nell'apertura del file: {e}")
            
            return "break"

    def show_chat(self):
        self.current_screen = 'chat'
        self.clear_screen()

        # Pass smaller font settings to chatbot if it uses them
        # self.editor_font_size gestisce lo zoom dell'editor
        self.chatbot_screen = create_chat_screen(
            self.main_frame,
            self.journal_dir,
            self.settings, # Chatbot might use these for styling
            self.show_home_screen,
            memory=self.memory
        )
        self.chatbot_screen.pack(fill=tk.BOTH, expand=True)

        self.root.unbind('<Up>')
        self.root.unbind('<Down>')
        self.root.unbind('<Return>')

    def show_psychological_profile(self):
        """Mostra il profilo psicologico dell'utente con rettangoli colorati"""
        self.current_screen = 'psychological_profile'
        self.clear_screen()
        
        profile_container = tk.Frame(self.main_frame, bg=self.settings['bg_color'],
                                   highlightbackground=self.settings['fg_color'],
                                   highlightthickness=2)
        profile_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Titolo
        title = tk.Label(profile_container, text="PROFILO PSICOLOGICO",
                        bg=self.settings['bg_color'],
                        fg=self.settings['fg_color'],
                        font=('Courier', 24, 'bold'))
        title.pack(pady=20)
        
        # Area di contenuto scrollabile SENZA scrollbar (keyboard-only)
        content_frame = tk.Frame(profile_container, bg=self.settings['bg_color'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Text widget per contenuto scrollabile con solo tastiera
        profile_text = tk.Text(content_frame,
                              bg=self.settings['bg_color'],
                              fg=self.settings['fg_color'],
                              font=('Courier', 16),
                              wrap=tk.WORD,
                              relief=tk.FLAT,
                              padx=15, pady=15,
                              state=tk.DISABLED)
        profile_text.pack(fill=tk.BOTH, expand=True)
        
        # Carica il profilo e inserisci nel text widget
        try:
            profile_data = self.emotions_analyzer.get_psychological_profile()
            profile_content = self._generate_colored_profile_text(profile_data)
            
            profile_text.config(state=tk.NORMAL)
            profile_text.insert(tk.END, profile_content)
            profile_text.config(state=tk.DISABLED)
            
        except Exception as e:
            profile_text.config(state=tk.NORMAL)
            profile_text.insert(tk.END, f"Errore nel caricamento del profilo: {e}\n\n")
            profile_text.insert(tk.END, "Il profilo si costruisce automaticamente analizzando le tue voci.")
            profile_text.config(state=tk.DISABLED)
        
        # Binding per navigazione SOLO da tastiera
        profile_text.bind('<Up>', lambda e: profile_text.yview_scroll(-1, "units"))
        profile_text.bind('<Down>', lambda e: profile_text.yview_scroll(1, "units"))
        profile_text.bind('<Prior>', lambda e: profile_text.yview_scroll(-1, "pages"))
        profile_text.bind('<Next>', lambda e: profile_text.yview_scroll(1, "pages"))
        
        # Istruzioni
        instructions = tk.Label(profile_container,
                              text="↑↓ Scorri | PgUp/PgDn Pagina | ESC Menu",
                              bg=self.settings['bg_color'],
                              fg=self.settings['fg_color'],
                              font=('Courier', 16))
        instructions.pack(pady=15)
        
        profile_text.focus_set()

    def _generate_colored_profile_text(self, profile_data):
        """Genera il testo del profilo con separatori colorati (solo testo, no widget)"""
        total_entries = profile_data.get("total_entries_analyzed", 0)
        
        if total_entries < 3:
            greeting = self.get_personalized_greeting()
            return f"""                      PROFILO IN COSTRUZIONE

{greeting}! Il tuo profilo psicologico si sta formando.

Ogni volta che scrivi nel diario, analizzo i tuoi pensieri,
emozioni e pattern comportamentali per costruire un quadro
sempre piÃ¹ accurato di chi sei.

Scrivi ancora qualche voce per vedere emergere
i tuoi tratti di personalitÃ  unici!"""
        
        content = []
        
        # === CHI SEI ===
        personality_traits = profile_data.get("personality_traits", {})
        if personality_traits:
            content.append("                            CHI SEI")
            content.append("")
            
            identity_desc = self._generate_identity_description(personality_traits)
            content.append(identity_desc)
            content.append("")
        
        # === FATTORI DI STRESS ===
        stress_triggers = profile_data.get("stress_triggers", [])
        if stress_triggers:
            content.append("                      FATTORI DI STRESS")
            content.append("")
            content.append("Le situazioni che ti mettono piÃ¹ alla prova:")
            content.append("")
            for trigger in stress_triggers[:5]:
                content.append(f"• {trigger}")
            content.append("")
        
        # === STRATEGIE DI GESTIONE ===
        coping_mechanisms = profile_data.get("coping_mechanisms", [])
        if coping_mechanisms:
            content.append("                   STRATEGIE DI GESTIONE")
            content.append("")
            content.append("Le tue strategie piÃ¹ efficaci per gestire lo stress:")
            content.append("")
            for mechanism in coping_mechanisms[:5]:
                content.append(f"• {mechanism}")
            content.append("")
        
        # === DINAMICHE RELAZIONALI ===
        relationships = profile_data.get("relationship_dynamics", {})
        if relationships:
            content.append("                   DINAMICHE RELAZIONALI")
            content.append("")
            content.append("Le tue relazioni piÃ¹ significative:")
            content.append("")
            for person, data in list(relationships.items())[:5]:
                if data["interactions"]:
                    latest = data["interactions"][-1]["quality_indicator"]
                    content.append(f"• {person}: {latest}")
                else:
                    content.append(f"• {person}: relazione in via di definizione")
            content.append("")
        
        # === CRESCITA PERSONALE ===
        growth_indicators = profile_data.get("growth_indicators", [])
        if growth_indicators:
            content.append("                     CRESCITA PERSONALE")
            content.append("")
            content.append("Segnali di evoluzione e crescita che hai mostrato:")
            content.append("")
            for i, indicator in enumerate(growth_indicators[:5], 1):
                content.append(f"{i}. {indicator}")
            content.append("")
        
        # === STATISTICHE ===
        content.append("                         STATISTICHE")
        content.append("")
        last_updated = profile_data.get("last_updated", "")[:10]
        content.append(f"Basato su {total_entries} voci del diario analizzate")
        content.append(f"Ultimo aggiornamento: {last_updated}")
        content.append(f"Versione profilo: {profile_data.get('version', '1.0')}")
        
        return "\n".join(content)

    def _generate_identity_description(self, personality_traits):
        """Genera una descrizione human-readable dei tratti di personalitÃ """
        descriptions = []
        
        for trait, data in personality_traits.items():
            value = data.get("value", 0)
            confidence = data.get("confidence", 0)
            
            if confidence < 0.3:  # Skip low-confidence traits
                continue
                
            if trait == "introversion_tendency":
                if value > 0.6:
                    descriptions.append("Sei una persona prevalentemente introversa")
                elif value < 0.4:
                    descriptions.append("Sei una persona prevalentemente estroversa")
                else:
                    descriptions.append("Hai un equilibrio tra introversione ed estroversione")
            
            elif "stress_response" in trait.lower():
                if "calm" in data.get("description", "").lower():
                    descriptions.append("Mantieni la calma sotto pressione")
                elif "active" in data.get("description", "").lower():
                    descriptions.append("Affronti lo stress in modo proattivo")
            
            elif "resilience" in trait.lower():
                if value > 0.6:
                    descriptions.append("Mostri buona resilienza nelle difficoltÃ ")
                elif value < 0.4:
                    descriptions.append("Tendi ad essere sensibile ai cambiamenti")
            
            elif "analytical" in trait.lower() or "reflection" in trait.lower():
                if value > 0.5:
                    descriptions.append("Tendi ad essere riflessivo e analitico")
            
            elif "energy" in trait.lower():
                if value > 0.6:
                    descriptions.append("Hai generalmente un buon livello di energia")
                elif value < 0.4:
                    descriptions.append("Il tuo livello di energia varia con l'ambiente")
        
        if not descriptions:
            descriptions.append("Il tuo profilo di personalitÃ  sta ancora emergendo")
            descriptions.append("Continua a scrivere per rivelare i tuoi tratti unici")
        
        return "\n".join(f"• {desc}" for desc in descriptions)

    def show_stats_dashboard(self):
        """Mostra la dashboard delle statistiche minimalista"""
        self.current_screen = 'stats_dashboard'
        self.clear_screen()

        # Container principale
        stats_frame = tk.Frame(self.main_frame, bg=self.settings['bg_color'])
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Canvas per le statistiche
        canvas = tk.Canvas(stats_frame, bg=self.settings['bg_color'],
                          highlightthickness=0, width=720, height=720)
        canvas.pack(fill=tk.BOTH, expand=True)

        # Inizializza la dashboard
        self.stats_dashboard = StatsDashboard(stats_frame, self.journal_dir,
                                            self.settings['bg_color'],
                                            self.settings['fg_color'])

        # Crea la dashboard
        self.stats_dashboard.create_dashboard(canvas)

        # Binding tasti
        self.root.unbind('<Up>')
        self.root.unbind('<Down>')
        self.root.unbind('<Left>')
        self.root.unbind('<Right>')
        self.root.unbind('<Return>')

        def handle_key(event):
            result = self.stats_dashboard.handle_keypress(event)
            if result != "break":  # Se non è stato gestito dalla dashboard
                if event.keysym == "Escape":
                    self.show_home_screen()
            else:
                # Aggiorna la dashboard dopo lo scroll
                self.stats_dashboard.create_dashboard(canvas)

        self.root.bind('<Up>', handle_key)
        self.root.bind('<Down>', handle_key)
        self.root.bind('<Escape>', handle_key)
        self.root.bind('r', handle_key)
        self.root.bind('R', handle_key)

        stats_frame.focus_set()

    def _check_api_key_status(self):
        """Controlla lo stato dell'API key"""
        api_key = os.environ.get('GROQ_API_KEY', '')
        if api_key and api_key.startswith('gsk_'):
            return "Configurata"
        return "Non configurata"

    def _show_api_key_input(self):
        """Mostra dialog per inserire API key"""
        # Crea una finestra popup semplice per l'input
        dialog = tk.Toplevel(self.root)
        dialog.title("Configura API Key Groq")
        dialog.geometry("500x300")
        dialog.configure(bg=self.settings['bg_color'])
        dialog.transient(self.root)
        dialog.grab_set()

        # Centra la finestra
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"500x300+{x}+{y}")

        # Titolo
        title_label = tk.Label(dialog,
            text="🔑 Configura API Key Groq",
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            font=('Courier New', 16, 'bold'))
        title_label.pack(pady=20)

        # Informazioni
        info_label = tk.Label(dialog,
            text="Ottieni una chiave gratuita da:\nconsole.groq.com/keys",
            bg=self.settings['bg_color'],
            fg='#aaaaaa',
            font=('Courier New', 12))
        info_label.pack(pady=10)

        # Campo input
        entry_frame = tk.Frame(dialog, bg=self.settings['bg_color'])
        entry_frame.pack(pady=20, padx=20, fill='x')

        tk.Label(entry_frame,
            text="API Key:",
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            font=('Courier New', 12)).pack(anchor='w')

        api_entry = tk.Entry(entry_frame,
            font=('Courier New', 12),
            width=50,
            show="*")  # Nasconde la chiave
        api_entry.pack(fill='x', pady=5)
        api_entry.focus()

        # Mostra chiave attuale se presente
        current_key = os.environ.get('GROQ_API_KEY', '')
        if current_key:
            api_entry.insert(0, current_key)

        # Pulsanti
        button_frame = tk.Frame(dialog, bg=self.settings['bg_color'])
        button_frame.pack(pady=20)

        def save_api_key():
            new_key = api_entry.get().strip()
            if new_key and not new_key.startswith('gsk_'):
                # Mostra errore
                error_label = tk.Label(dialog,
                    text="❌ La API key deve iniziare con 'gsk_'",
                    bg=self.settings['bg_color'],
                    fg='#ff4444',
                    font=('Courier New', 10))
                error_label.pack()
                dialog.after(3000, error_label.destroy)
                return

            # Salva in .env
            self._save_api_key_to_env(new_key)

            # Aggiorna la visualizzazione
            self.api_key_status = self._check_api_key_status()
            self.api_key_label.config(text=f"🔑 API Key: {self.api_key_status}")

            dialog.destroy()

        def cancel():
            dialog.destroy()

        save_btn = tk.Button(button_frame,
            text="💾 Salva",
            command=save_api_key,
            bg=self.settings['fg_color'],
            fg=self.settings['bg_color'],
            font=('Courier New', 12))
        save_btn.pack(side='left', padx=10)

        cancel_btn = tk.Button(button_frame,
            text="❌ Annulla",
            command=cancel,
            bg='#666666',
            fg='white',
            font=('Courier New', 12))
        cancel_btn.pack(side='left', padx=10)

        # Bind keyboard events
        dialog.bind('<Return>', lambda e: save_api_key())
        dialog.bind('<Escape>', lambda e: cancel())

    def _show_font_selector(self):
        """Mostra dialog per selezionare font con lista scrollabile"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Seleziona Font")
        dialog.geometry("450x500")
        dialog.configure(bg=self.settings['bg_color'])
        dialog.transient(self.root)
        dialog.grab_set()

        # Centra la finestra
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"450x500+{x}+{y}")

        # Titolo
        title_label = tk.Label(dialog,
            text="📝 Seleziona Font",
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            font=self.get_font(20, 'bold'))
        title_label.pack(pady=15)

        # Info
        info_label = tk.Label(dialog,
            text="↑↓ Naviga | ENTER Seleziona | ESC Annulla",
            bg=self.settings['bg_color'],
            fg='#888888',
            font=self.get_font(12))
        info_label.pack(pady=5)

        # Frame per lista con scrollbar
        list_frame = tk.Frame(dialog, bg=self.settings['bg_color'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Listbox per i font
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        font_listbox = tk.Listbox(list_frame,
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            selectbackground=self.settings['fg_color'],
            selectforeground=self.settings['bg_color'],
            font=self.get_font(16),
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            borderwidth=2,
            highlightthickness=1,
            highlightbackground=self.settings['fg_color'])
        font_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=font_listbox.yview)

        # Popola la lista con i font disponibili
        current_font = self.settings.get('font_family', 'Courier New')
        selected_index = 0

        for i, font_name in enumerate(self.available_fonts):
            font_listbox.insert(tk.END, font_name)
            if font_name == current_font:
                selected_index = i

        # Seleziona il font corrente
        font_listbox.selection_set(selected_index)
        font_listbox.see(selected_index)
        font_listbox.activate(selected_index)
        font_listbox.focus_set()

        # Preview del font selezionato
        preview_frame = tk.Frame(dialog, bg=self.settings['bg_color'])
        preview_frame.pack(fill=tk.X, padx=20, pady=10)

        preview_label = tk.Label(preview_frame,
            text="Preview: The quick brown fox jumps",
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            font=(current_font, 14))
        preview_label.pack()

        def update_preview(event=None):
            """Aggiorna preview quando cambia selezione"""
            try:
                selection = font_listbox.curselection()
                if selection:
                    selected_font = font_listbox.get(selection[0])
                    preview_label.config(font=(selected_font, 14))
            except:
                pass

        def select_font():
            """Seleziona il font e chiudi dialog"""
            selection = font_listbox.curselection()
            if selection:
                new_font = font_listbox.get(selection[0])
                self.settings['font_family'] = new_font
                self.font_label.config(text=f"📝 Font: {new_font}")
                self.apply_font_changes()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        # Bind events
        font_listbox.bind('<<ListboxSelect>>', update_preview)
        font_listbox.bind('<Return>', lambda e: select_font())
        font_listbox.bind('<Double-Button-1>', lambda e: select_font())
        dialog.bind('<Escape>', lambda e: cancel())

        # Pulsanti
        button_frame = tk.Frame(dialog, bg=self.settings['bg_color'])
        button_frame.pack(pady=15)

        select_btn = tk.Button(button_frame,
            text="✓ Seleziona",
            command=select_font,
            bg=self.settings['fg_color'],
            fg=self.settings['bg_color'],
            font=self.get_font(14, 'bold'),
            padx=20,
            pady=5)
        select_btn.pack(side='left', padx=10)

        cancel_btn = tk.Button(button_frame,
            text="✗ Annulla",
            command=cancel,
            bg='#666666',
            fg='white',
            font=self.get_font(14),
            padx=20,
            pady=5)
        cancel_btn.pack(side='left', padx=10)

    def _save_api_key_to_env(self, api_key):
        """Salva API key nel file .env"""
        env_file = Path(__file__).parent / '.env'
        try:
            # Leggi contenuto esistente
            env_content = ""
            if env_file.exists():
                env_content = env_file.read_text(encoding='utf-8')

            # Aggiorna o aggiungi GROQ_API_KEY
            lines = env_content.split('\n')
            found = False
            for i, line in enumerate(lines):
                if line.startswith('GROQ_API_KEY='):
                    if api_key:
                        lines[i] = f'GROQ_API_KEY={api_key}'
                    else:
                        lines[i] = '# GROQ_API_KEY='  # Commenta se vuoto
                    found = True
                    break

            if not found and api_key:
                lines.append(f'GROQ_API_KEY={api_key}')

            # Scrivi il file
            env_file.write_text('\n'.join(lines), encoding='utf-8')

            # Aggiorna variabile d'ambiente
            if api_key:
                os.environ['GROQ_API_KEY'] = api_key
            else:
                os.environ.pop('GROQ_API_KEY', None)

        except Exception as e:
            print(f"Errore nel salvataggio API key: {e}")

    def show_settings(self):
        self.current_screen = 'settings'
        self.clear_screen()
        
        settings_frame = tk.Frame(self.main_frame, bg=self.settings['bg_color'],
                                highlightbackground=self.settings['fg_color'],
                                highlightthickness=2) # Border piÃ¹ spesso
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30) # Padding generoso
        
        title = tk.Label(settings_frame, text="⚙️ IMPOSTAZIONI",
                        bg=self.settings['bg_color'],
                        fg=self.settings['fg_color'],
                        font=('Courier', 24, 'bold')) # Font molto piÃ¹ grande
        title.pack(pady=20) # PiÃ¹ spazio
        
        self.settings_options = []
        self.settings_selection = 0
        
        options_container = tk.Frame(settings_frame, bg=self.settings['bg_color'])
        options_container.pack(pady=20) # PiÃ¹ spazio
        
        self.theme_modes = [
            ("🌙 Notte", {'bg_color': '#000000', 'fg_color': '#ffffff'}),
            ("☀️ Giorno", {'bg_color': '#ffffff', 'fg_color': '#000000'}),
            ("🔵 Dark Blue", {'bg_color': '#1a1a1a', 'fg_color': '#3B8ED0'})
        ]
        # Seleziona il tema corretto in base al bg_color attuale
        if self.settings['bg_color'] == '#000000':
            self.theme_index = 0  # Notte
        elif self.settings['bg_color'] == '#ffffff':
            self.theme_index = 1  # Giorno
        else:
            self.theme_index = 2  # Dark Blue

        self.theme_label = tk.Label(options_container,
            text=f"Tema: {self.theme_modes[self.theme_index][0]}",
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            font=(self.settings.get('font_family', 'Courier New'), 20))
        self.theme_label.pack(pady=8) # PiÃ¹ spazio
        self.settings_options.append(('theme', self.theme_label, 'theme'))

        # Font selection
        current_font = self.settings.get('font_family', 'Courier New')
        try:
            self.font_index = self.available_fonts.index(current_font)
        except ValueError:
            self.font_index = 0
            self.settings['font_family'] = self.available_fonts[0] if self.available_fonts else 'Courier New'

        self.font_label = tk.Label(options_container,
            text=f"📝 Font: {self.settings['font_family']}",
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            font=(self.settings.get('font_family', 'Courier New'), 20))
        self.font_label.pack(pady=8)
        self.settings_options.append(('font', self.font_label, 'font'))

        # API Key Groq
        self.api_key_status = self._check_api_key_status()
        api_key_text = f"🔑 API Key: {self.api_key_status}"
        self.api_key_label = tk.Label(options_container,
            text=api_key_text,
            bg=self.settings['bg_color'],
            fg=self.settings['fg_color'],
            font=self.get_font(20))
        self.api_key_label.pack(pady=8)
        self.settings_options.append(('api_key', self.api_key_label, 'api_key'))

        auto_save_text = "✓ AutoSave" if self.settings['auto_save'] else "✗ AutoSave"  # Shortened
        self.auto_save_label = tk.Label(options_container, text=auto_save_text,
                                      bg=self.settings['bg_color'],
                                      fg=self.settings['fg_color'],
                                      font=self.get_font(20))
        self.auto_save_label.pack(pady=8) # PiÃ¹ spazio
        self.settings_options.append(('auto_save', self.auto_save_label, 'bool'))

        # Aggiungiamo il pulsante per la guida
        help_label = tk.Label(options_container, text="❓ Guida",
                              bg=self.settings['bg_color'],
                              fg=self.settings['fg_color'],
                              font=self.get_font(20))
        help_label.pack(pady=8) # PiÃ¹ spazio
        self.settings_options.append(('help', help_label, 'action'))

        cloud_label = tk.Label(options_container, text="☁️ Cloud (futuro)",  # Shortened
                             bg=self.settings['bg_color'],
                             fg='#666666', # Keep muted
                             font=self.get_font(9, 'italic')) # Reduced
        cloud_label.pack(pady=2) # Reduced

        self.save_settings_btn = tk.Label(options_container,
                                        text="💾 SALVA",  # Shortened
                                        bg=self.settings['bg_color'],
                                        fg=self.settings['fg_color'],
                                        font=self.get_font(24, 'bold')) # Font piÃ¹ grande
        self.save_settings_btn.pack(pady=20) # PiÃ¹ spazio
        self.settings_options.append(('save', self.save_settings_btn, 'action'))

        instructions = tk.Label(settings_frame,
                              text="↑↓ Nav | ←→ Mod. | ENTER OK | ESC Menu",  # Shortened
                              bg=self.settings['bg_color'],
                              fg=self.settings['fg_color'],
                              font=self.get_font(20)) # Font piÃ¹ grande
        instructions.pack(pady=15) # PiÃ¹ spazio
        
        self.update_settings_selection()
        
        self.root.bind('<Up>', self.settings_up)
        self.root.bind('<Down>', self.settings_down)
        self.root.bind('<Left>', self.settings_change)
        self.root.bind('<Right>', self.settings_change)
        self.root.bind('<Return>', self.settings_activate)
    
    def choose_bg_color(self):
        color = colorchooser.askcolor(initialcolor=self.settings['bg_color'])
        if color and color[1]:
            self.settings['bg_color'] = color[1]
            self.apply_color_changes()
            
    def choose_fg_color(self):
        color = colorchooser.askcolor(initialcolor=self.settings['fg_color'])
        if color and color[1]:
            self.settings['fg_color'] = color[1]
            self.apply_color_changes()
            
    def apply_color_changes(self):
        self.root.configure(bg=self.settings['bg_color'])
        # Re-render current screen to apply colors
        if self.current_screen == 'settings':
            self.show_settings()
        elif self.current_screen == 'editor':
            self.show_editor() # Editor needs specific redraw for text widget
        elif self.current_screen == 'home':
            self.show_home_screen() # Menu principale
        elif self.current_screen == 'chat':
            self.show_chat() # Chat AI
        elif self.current_screen == 'calendar':
            self.show_calendar() # Calendario
        elif self.current_screen == 'search':
            self.show_search() # Ricerca
        elif self.current_screen == 'insights':
            self.show_insights() # Emozioni settimanali
        # Salva le impostazioni per persistenza
        self.save_settings()

    def apply_font_changes(self):
        """Applica il cambio di font a tutta l'applicazione"""
        # Re-render current screen to apply font
        if self.current_screen == 'settings':
            self.show_settings()
        elif self.current_screen == 'editor':
            self.show_editor() # Editor needs specific redraw for text widget
        elif self.current_screen == 'home':
            self.show_home_screen() # Menu principale
        elif self.current_screen == 'chat':
            self.show_chat() # Chat AI
        elif self.current_screen == 'calendar':
            self.show_calendar() # Calendario
        elif self.current_screen == 'search':
            self.show_search() # Ricerca
        elif self.current_screen == 'insights':
            self.show_insights() # Emozioni settimanali
        # Salva le impostazioni per persistenza
        self.save_settings()

    def save_all_settings(self):
        self.save_settings()
        self.show_home_screen()
        
    def on_window_resize(self, event=None):
        if hasattr(self, 'main_frame'):
            self.main_frame.update_idletasks()
            
    def open_selected_day(self, event):
        if self.current_screen == 'calendar' and self.cal_mode == 'day':
            self.current_date = datetime.datetime(self.cal_year, self.cal_month, self.cal_day)
            self.filename = f"{self.current_date.strftime('%Y-%m-%d')}.txt"
            self.filepath = self.journal_dir / self.filename
            self.show_editor()
            
    def load_file(self):
        if self.filepath.exists():
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text.insert('1.0', content)
            except Exception as e:
                # print(f"Error loading file {self.filepath}: {e}")
                self.text.insert('1.0', f"Errore caricamento: {e}")
    
    def save_file(self, event=None, show_message=True):
        if self.current_screen == 'editor':
            content = self.text.get('1.0', 'end-1c')
            try:
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.last_save_time = time.time()
                self.memory.add_entry(self.filename[:-4], content) # Assumendo che self.filename sia YYYY-MM-DD.txt
                
                # Analizza e salva le emozioni in Memvid
                if hasattr(self, 'emotions_analyzer') and self.emotions_analyzer.api_key:
                    full_analysis = self.emotions_analyzer.analyze_full_entry(content)
                    emotion_scores = full_analysis.get("emotions", {})
                    daily_insights = full_analysis.get("daily_insights", {})
                    profile_updates = full_analysis.get("profile_updates", {})

                    if emotion_scores:  # Se l'analisi ha prodotto risultati
                        date_str = self.filepath.stem  # YYYY-MM-DD
                        try:
                            # Salva in Memvid
                            if hasattr(self, 'memory') and self.memory:
                                self.memory.save_emotions(
                                    date_str, emotion_scores, daily_insights, profile_updates
                                )
                        except Exception as e_emotions:
                            print(f"Errore salvataggio emozioni in Memvid: {e_emotions}")

                if show_message:
                    self.show_status("Salvato!")
            except Exception as e:
                # print(f"Error saving file {self.filepath}: {e}")
                if show_message:
                    self.show_status("Errore Salva!")
        return 'break'

    def show_status(self, message, timeout=3000):
        """Mostra un messaggio di stato temporaneo"""
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            # Cancella eventuali timer di restore precedenti
            if hasattr(self, 'status_restore_timer'):
                try:
                    self.root.after_cancel(self.status_restore_timer)
                except:
                    pass
            
            # Salva il testo originale se non Ã¨ giÃ  salvato
            if not hasattr(self, 'original_status_text'):
                self.original_status_text = "↑↓ Scorri | Ctrl+/- Zoom | F2 Emozioni | Ctrl-S Salva | ESC Menu"
            
            # Sostituisce temporaneamente tutto il testo con il messaggio
            self.status_label.configure(text=message)
            
            def restore():
                try:
                    if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                        self.status_label.configure(text=self.original_status_text)
                    # Rimuovi il timer di riferimento
                    if hasattr(self, 'status_restore_timer'):
                        delattr(self, 'status_restore_timer')
                except tk.TclError:
                    pass # Widget might be destroyed
            
            # Programma il restore con timeout personalizzabile
            self.status_restore_timer = self.root.after(timeout, restore)
            
    def auto_save(self):
        # L'auto save Ã¨ ora gestito solo quando si esce dall'editor
        # Non piÃ¹ durante la scrittura per evitare blocchi
        pass
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
        if current_state:  # Se stiamo uscendo da fullscreen
            self.root.geometry("720x720")
    
    def on_closing(self):
        """Gestisce la chiusura dell'applicazione"""
        print("on_closing called...")
        # Pulisce eventuali timer attivi
        if self.scroll_timer_id:
            self.root.after_cancel(self.scroll_timer_id)
        # Stop screensaver monitoring
        if hasattr(self, 'screensaver_manager') and self.screensaver_manager:
            self.screensaver_manager.stop_monitoring()
        # Qui potresti aggiungere altre operazioni di pulizia se necessario,
        # ad esempio salvare lo stato, chiudere connessioni, ecc.
        self.root.destroy()
        print("Reminor application closed.")
        
    def handle_escape(self, event):
        if self.current_screen == 'home':
            # ESC nella schermata home chiude completamente l'applicazione
            self.on_closing() 
        else:
            # Common unbinds or actions before going home
            if self.scroll_timer_id: # From editor scrolling
                self.root.after_cancel(self.scroll_timer_id)
                self.scroll_timer_id = None

            if self.current_screen == 'editor':
                # Auto save quando si esce dall'editor (se abilitato)
                if self.settings['auto_save']:
                    self.save_file(show_message=False)
                
                # Assicurati che il testo sia visibile prima di uscire dall'editor
                if self.editor_showing_emotions:
                    self.toggle_emotion_display_in_editor() # Riporta alla vista testo
                
                # Unbind keys specifici dell'editor
                if hasattr(self, 'text'):
                    self.text.unbind('<Up>')
                    self.text.unbind('<Down>')
                    self.text.unbind('<KeyRelease-Up>')
                    self.text.unbind('<KeyRelease-Down>')
                self.root.unbind('<F2>') # Unbind F2
                self.root.unbind('<Control-s>') # Unbind Ctrl-S
            
            elif self.current_screen == 'calendar':
                self.root.unbind('<Left>')
                self.root.unbind('<Right>')
                # <Up> and <Down> are rebound by show_home_screen if needed for menu
            elif self.current_screen == 'search':
                if hasattr(self, 'search_entry'): self.search_entry.unbind('<Return>')
                # Unbind search navigation keys
                self.root.unbind('<Up>')
                self.root.unbind('<Down>')
                self.root.unbind('<Return>')
            elif self.current_screen == 'settings':
                self.root.unbind('<Left>')
                self.root.unbind('<Right>')
                # <Up>, <Down>, <Return> are rebound by show_home_screen
            elif self.current_screen == 'insights': # Aggiunto per insights
                self.root.unbind('<Left>')
                self.root.unbind('<Right>')
            elif self.current_screen == 'chat':
                 if self.chatbot_screen and hasattr(self.chatbot_screen, 'handle_escape_to_menu'):
                     self.chatbot_screen.handle_escape_to_menu()
            
            self.show_home_screen() # This rebinds Up, Down, Return for home menu
        return 'break'
        
    def cal_navigate(self, event):
        if self.current_screen != 'calendar': return
        
        # Salva lo stato precedente per determinare se Ã¨ necessario un refresh completo
        prev_month = self.cal_month
        prev_year = self.cal_year
        prev_mode = self.cal_mode
            
        if self.cal_mode == 'month':
            if event.keysym == 'Left':
                self.cal_month -= 1
                if self.cal_month == 0: self.cal_month = 12; self.cal_year -= 1
            elif event.keysym == 'Right':
                self.cal_month += 1
                if self.cal_month == 13: self.cal_month = 1; self.cal_year += 1
            elif event.keysym == 'Down': self.cal_mode = 'day'
        else: # Day navigation
            _, max_days_in_month = calendar.monthrange(self.cal_year, self.cal_month)
            if event.keysym == 'Left':
                self.cal_day -= 1
                if self.cal_day == 0:
                    self.cal_month -= 1
                    if self.cal_month == 0: self.cal_month = 12; self.cal_year -= 1
                    self.cal_day = calendar.monthrange(self.cal_year, self.cal_month)[1]
            elif event.keysym == 'Right':
                self.cal_day += 1
                if self.cal_day > max_days_in_month:
                    self.cal_day = 1
                    self.cal_month += 1
                    if self.cal_month == 13: self.cal_month = 1; self.cal_year += 1
            elif event.keysym == 'Up':
                # Simplified: try to go up 7 days, or switch to month mode if at top
                current_row, _ = self.cal_grid.get(self.cal_day, (None,None))
                cal_data = calendar.monthcalendar(self.cal_year, self.cal_month)
                is_first_week_visual = False
                if current_row is not None: # current_row is 1-based from grid creation
                     # Check if day is in the first displayed row that contains numbers
                    first_active_row_idx = 0
                    for r_idx, r_data in enumerate(cal_data):
                        if any(d != 0 for d in r_data):
                            first_active_row_idx = r_idx
                            break
                    if current_row -1 == first_active_row_idx : # current_row from grid is 1-based
                         is_first_week_visual = True

                if is_first_week_visual : #current_row == 1 or (current_row is not None and cal_data[current_row-1].count(0) > 0 and self.cal_day <=7) : # Crude check for first visual week
                    self.cal_mode = 'month'
                else:
                    self.cal_day -= 7
                    if self.cal_day < 1: # Went to previous month
                        self.cal_month -= 1
                        if self.cal_month == 0: self.cal_month = 12; self.cal_year -= 1
                        prev_month_days = calendar.monthrange(self.cal_year, self.cal_month)[1]
                        self.cal_day += prev_month_days # approx landing
                        # Ensure cal_day is valid, try to land on similar column
                        # This logic can be complex; for small screen, this might be enough
                        self.cal_day = max(1, min(self.cal_day, prev_month_days))

            elif event.keysym == 'Down':
                self.cal_day += 7
                if self.cal_day > max_days_in_month: # Went to next month
                    self.cal_day -= max_days_in_month
                    self.cal_month += 1
                    if self.cal_month == 13: self.cal_month = 1; self.cal_year += 1
                    # Ensure cal_day is valid for new month
                    new_max_days = calendar.monthrange(self.cal_year, self.cal_month)[1]
                    self.cal_day = max(1, min(self.cal_day, new_max_days))
        
        # Aggiorna solo se necessario
        month_changed = (prev_month != self.cal_month or prev_year != self.cal_year)
        mode_changed = (prev_mode != self.cal_mode)
        
        if month_changed or mode_changed:
            # Refresh completo necessario
            self.update_calendar_display()
        else:
            # Solo aggiornamento della selezione
            self.update_calendar_selection()
            
    def update_calendar_display(self):
        self.month_label.config(text=f"{calendar.month_name[self.cal_month][:3]} {self.cal_year}") # Shorten month name
        self.update_calendar_selection()
        
    def update_settings_selection(self):
        for i, (key, widget_container, widget_type) in enumerate(self.settings_options):
            # Determine the actual label widget (could be widget_container or its child)
            actual_widget_to_style = widget_container
            if isinstance(widget_container, tk.Frame):  # Gestisce eventuali opzioni racchiuse in frame
                 # Style all children of the frame, or a specific one if identifiable
                for child in widget_container.winfo_children():
                    if i == self.settings_selection:
                        child.config(bg=self.settings['fg_color'], fg=self.settings['bg_color'])
                    else:
                        child.config(bg=self.settings['bg_color'], fg=self.settings['fg_color'])
                continue # Skip styling the frame itself directly after children

            if i == self.settings_selection:
                actual_widget_to_style.config(bg=self.settings['fg_color'], fg=self.settings['bg_color'])
            else:
                actual_widget_to_style.config(bg=self.settings['bg_color'], fg=self.settings['fg_color'])
                                
    def settings_up(self, event):
        if self.current_screen == 'settings':
            self.settings_selection = (self.settings_selection - 1) % len(self.settings_options)
            self.update_settings_selection()
            
    def settings_down(self, event):
        if self.current_screen == 'settings':
            self.settings_selection = (self.settings_selection + 1) % len(self.settings_options)
            self.update_settings_selection()
            
    def settings_change(self, event):
        if self.current_screen == 'settings':
            key, widget, widget_type = self.settings_options[self.settings_selection]
            if widget_type == 'theme':
                if event.keysym in ('Left', 'Right'):
                    # Cambia tema
                    if event.keysym == 'Left':
                        self.theme_index = (self.theme_index - 1) % len(self.theme_modes)
                    else:
                        self.theme_index = (self.theme_index + 1) % len(self.theme_modes)
                    theme = self.theme_modes[self.theme_index][1]
                    self.settings['bg_color'] = theme['bg_color']
                    self.settings['fg_color'] = theme['fg_color']
                    self.theme_label.config(text=f"Tema: {self.theme_modes[self.theme_index][0]}")
                    self.apply_color_changes()
            elif widget_type == 'font':
                # Rimuovo navigazione orizzontale, usa solo ENTER per aprire popup
                pass
    def settings_activate(self, event):
        if self.current_screen == 'settings':
            key, widget, widget_type = self.settings_options[self.settings_selection]
            
            if key == 'save':
                self.save_all_settings()
            elif widget_type == 'color':
                if key == 'bg_color': self.choose_bg_color()
                elif key == 'fg_color': self.choose_fg_color()
            elif widget_type == 'bool' and key == 'auto_save':
                self.settings['auto_save'] = not self.settings['auto_save']
                new_text = "✓ AutoSave" if self.settings['auto_save'] else "✗ AutoSave"
                self.auto_save_label.config(text=new_text)
                self.update_settings_selection() # Re-highlight correctly
            elif widget_type == 'theme' and key == 'theme':
                # Toggle between theme modes
                self.theme_index = (self.theme_index + 1) % len(self.theme_modes)
                new_theme = self.theme_modes[self.theme_index][1]
                self.settings['bg_color'] = new_theme['bg_color']
                self.settings['fg_color'] = new_theme['fg_color']
                
                # Update label text to show current theme
                self.theme_label.config(text=f"Tema: {self.theme_modes[self.theme_index][0]}")
                
                # Apply new theme colors
                self.apply_color_changes()
            elif widget_type == 'api_key' and key == 'api_key':
                # Mostra dialog per configurare API key
                self._show_api_key_input()
            elif widget_type == 'font' and key == 'font':
                # Mostra dialog per selezionare font
                self._show_font_selector()
            elif key == 'help':
                self.show_help()
    
    def show_help(self, event=None): # Aggiunto event=None per coerenza se chiamato da binding
        """Mostra la schermata di aiuto con le istruzioni per l'utilizzo dell'app"""
        self.current_screen = 'help'
        self.clear_screen()
        
        help_frame = tk.Frame(self.main_frame, bg=self.settings['bg_color'],
                            highlightbackground=self.settings['fg_color'],
                            highlightthickness=2) # Border piÃ¹ spesso
        help_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30) # Padding generoso
        
        title = tk.Label(help_frame, text="❓ GUIDA REMINOR",
                        bg=self.settings['bg_color'],
                        fg=self.settings['fg_color'],
                        font=('Courier', 24, 'bold')) # Font molto piÃ¹ grande
        title.pack(pady=20) # PiÃ¹ spazio
        
        # Contenitore per il testo dell'aiuto
        content_frame = tk.Frame(help_frame, bg=self.settings['bg_color'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20) # PiÃ¹ padding
        
        # Testo della guida SENZA scrollbar
        help_text = tk.Text(content_frame,
                          bg=self.settings['bg_color'],
                          fg=self.settings['fg_color'],
                          font=('Courier', 20), # Font coerente con i menu
                          wrap=tk.WORD,
                          relief=tk.FLAT,
                          padx=15, pady=15) # PiÃ¹ padding interno
        
        help_text.pack(fill=tk.BOTH, expand=True)
        
        # Contenuto della guida
        guida = """GUIDA ALL'UTILIZZO DI REMINOR

---------- MENU PRINCIPALE ----------
Usa le frecce SU/GIU per navigare e INVIO per selezionare.
ESC per tornare al menu principale da qualsiasi schermata.

---------- CONTROLLI SCHERMO ----------
F11: Entra/Esci dalla modalità schermo intero
ESC (nel menu principale): Chiudi l'applicazione
Ctrl+Q: Chiudi l'applicazione
Alt+F4: Chiudi l'applicazione

---------- NUOVA PAGINA (EDITOR) ----------
• Scrivi liberamente le tue riflessioni del giorno
• Usa Ctrl+ e Ctrl- per regolare lo zoom del testo
• Tasti freccia SU/GIU: Scorri il testo
• CTRL+S: Salva il diario
• Il testo viene salvato automaticamente ogni 30 secondi
• ESC: Torna al menu principale

---------- CALENDARIO ----------
• Usa le frecce direzionali per navigare tra i giorni
• Freccia SU: Passa alla visualizzazione mensile/settimana precedente
• Freccia GIU: Passa alla visualizzazione giornaliera/settimana successiva
• Frecce SINISTRA/DESTRA: Giorno precedente/successivo
• INVIO: Apri l'editor per il giorno selezionato
• I giorni con contenuto sono indicati con [n]
• ESC: Torna al menu principale

---------- RICERCA ----------
• Digita il testo da cercare nei tuoi diari
• INVIO: Avvia la ricerca
• Le frecce SU/GIU permettono di scorrere i risultati
• ESC: Torna al menu principale

---------- CHAT PENSIERI ----------
• Parla con l'AI che ha analizzato il tuo diario
• Shift+Freccia SU/GIU: Scorri la conversazione
• PgUp/PgDn: Scorri più velocemente
• INVIO: Invia il messaggio
• F2: Visualizza il ragionamento dell'AI
• ESC o pulsante "← Menu": Torna al menu principale

---------- ANALISI EMOZIONI ----------
• Visualizza un grafico delle emozioni rilevate nel diario
• Le emozioni sono analizzate tramite AI
• ESC: Torna al menu principale

---------- IMPOSTAZIONI ----------
• Tema: Scegli tra modalità Notte e Giorno
• Font: Modifica dimensione del carattere (7-16)
• AutoSave: Attiva/disattiva salvataggio automatico
• ESC: Torna al menu principale

Reminor è progettato per funzionare interamente da tastiera, senza necessità di usare il mouse.
"""
        
        help_text.insert(tk.END, guida)
        help_text.config(state=tk.DISABLED)  # Rende il testo non modificabile
        
        # Binding per navigazione
        help_text.bind('<Up>', lambda e: help_text.yview_scroll(-1, "units"))
        help_text.bind('<Down>', lambda e: help_text.yview_scroll(1, "units"))
        help_text.bind('<Prior>', lambda e: help_text.yview_scroll(-1, "pages"))
        help_text.bind('<Next>', lambda e: help_text.yview_scroll(1, "pages"))
        
        # Istruzioni
        instructions = tk.Label(help_frame,
                              text="↑↓ Scorri | ESC Menu",
                              bg=self.settings['bg_color'],
                              fg=self.settings['fg_color'],
                              font=('Courier New', 20)) # Font piÃ¹ grande
        instructions.pack(pady=15) # PiÃ¹ spazio
        
        # Diamo il focus al widget del testo per permettere lo scorrimento immediato
        help_text.focus_set()
                
    def _generate_text_bar(self, score, length=3):
        # score is 0.0 to 1.0 - lunghezza ridotta a 3 per far stare meglio sullo schermo
        filled_chars = round(score * length)
        empty_chars = length - filled_chars
        bar = f"|{'■' * filled_chars}{'□' * empty_chars}|" 
        return bar

    def _navigate_insights_week(self, direction):
        if self.current_screen != 'insights':
            return "break"

        if direction == 'prev': # Settimana precedente (piÃ¹ vecchia)
            self.insights_current_week_offset += 1
        elif direction == 'next': # Settimana successiva (piÃ¹ recente)
            self.insights_current_week_offset = max(0, self.insights_current_week_offset - 1)
        
        if hasattr(self, 'insights_matrix_frame') and self.insights_matrix_frame and self.insights_matrix_frame.winfo_exists():
            self._display_insights_matrix()
        return "break" 

    def _display_insights_matrix(self):
        if not self.insights_matrix_frame or not self.insights_matrix_frame.winfo_exists():
            return
            
        for widget in self.insights_matrix_frame.winfo_children():
            widget.destroy()

        today = datetime.date.today()
        
        current_week_monday_if_offset_zero = today - datetime.timedelta(days=today.weekday())
        target_week_start_date = current_week_monday_if_offset_zero - datetime.timedelta(weeks=self.insights_current_week_offset)
        target_week_end_date = target_week_start_date + datetime.timedelta(days=6)
        
        start_date_str = target_week_start_date.strftime('%d %b')
        end_date_str = target_week_end_date.strftime('%d %b')
        if hasattr(self, 'insights_week_title_label') and self.insights_week_title_label and self.insights_week_title_label.winfo_exists():
             self.insights_week_title_label.config(text=f"--- Emozioni: {start_date_str} - {end_date_str} ---")

        dates_in_week = [target_week_start_date + datetime.timedelta(days=i) for i in range(self.insights_num_days_to_display)]
        
        # Carica emozioni da Memvid
        weekly_emotion_data = {}
        if hasattr(self, 'memory') and self.memory:
            date_strings = [d.strftime('%Y-%m-%d') for d in dates_in_week]
            memvid_emotions = self.memory.get_emotions_for_week(date_strings)
            for date_obj in dates_in_week:
                date_str = date_obj.strftime('%Y-%m-%d')
                weekly_emotion_data[date_obj] = memvid_emotions.get(date_str, {})
        else:
            for date_obj in dates_in_week:
                weekly_emotion_data[date_obj] = {}

        base_font_tuple = ('Courier New', 14)
        bold_font_tuple = ('Courier New', 14, 'bold')
        header_font_tuple = ('Courier New', 14, 'bold')
        emotion_label_width = 10
        bar_width = 6
        day_header_width = 4

        days_locale = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
        tk.Label(self.insights_matrix_frame, text="", bg=self.settings['bg_color'], fg=self.settings['fg_color'], font=base_font_tuple, width=emotion_label_width, anchor='w').grid(row=0, column=0, padx=0, pady=0, sticky='w')
        for i, day_name in enumerate(days_locale):
            tk.Label(self.insights_matrix_frame, text=day_name, bg=self.settings['bg_color'], fg=self.settings['fg_color'], font=header_font_tuple, width=day_header_width, anchor='center').grid(row=0, column=i+1, padx=0, pady=0)

        tk.Label(self.insights_matrix_frame, text="", bg=self.settings['bg_color'], fg=self.settings['fg_color'], font=base_font_tuple, width=emotion_label_width, anchor='w').grid(row=1, column=0, padx=0, pady=0, sticky='w')
        for i, date_obj in enumerate(dates_in_week):
            tk.Label(self.insights_matrix_frame, text=date_obj.strftime('%d'), bg=self.settings['bg_color'], fg=self.settings['fg_color'], font=header_font_tuple, width=day_header_width, anchor='center').grid(row=1, column=i+1, padx=0, pady=0)
        
        if not hasattr(self.emotions_analyzer, 'emotions_list') or not self.emotions_analyzer.emotions_list:
            tk.Label(self.insights_matrix_frame, text="Lista emozioni non definita.", bg=self.settings['bg_color'], fg=self.settings['fg_color'], font=base_font_tuple).grid(row=2, column=0, columnspan=8, pady=10)
            return

        # Controlla se ci sono dati per la settimana
        has_any_emotions = any(weekly_emotion_data.get(date_obj) for date_obj in dates_in_week)
        all_data_missing_for_this_week = not has_any_emotions

        emotion_start_row = 2 # Default start row for emotions

        if all_data_missing_for_this_week:
             tk.Label(self.insights_matrix_frame, text="(Nessun dato per questa settimana)",
                      bg=self.settings['bg_color'], fg='#666666',
                      font=('Courier New', 14, 'italic'), justify=tk.CENTER).grid(
                          row=2, column=0, columnspan=self.insights_num_days_to_display + 1,
                          pady=(3,6), sticky='ew', ipady=0)
             emotion_start_row = 3
        # else: # This else is implicitly handled by emotion_start_row defaulting to 2
             # emotion_start_row = 2

        for row_idx, emotion_name in enumerate(self.emotions_analyzer.emotions_list, start=emotion_start_row):
            tk.Label(self.insights_matrix_frame, text=f"{emotion_name.capitalize()[:8]}:", bg=self.settings['bg_color'], fg=self.settings['fg_color'], font=base_font_tuple, width=emotion_label_width, anchor='w', justify=tk.LEFT).grid(row=row_idx, column=0, padx=1, pady=0, sticky='w', ipady=0) # Interlinea ridotta con ipady=0
            for col_idx, date_obj in enumerate(dates_in_week):
                emotion_scores_for_day = weekly_emotion_data.get(date_obj, {})
                score = emotion_scores_for_day.get(emotion_name, 0.0)
                bar = self._generate_text_bar(score, 3) # Barra ridotta a 3 caselle per risparmiare spazio
                tk.Label(self.insights_matrix_frame, text=bar, bg=self.settings['bg_color'], fg=self.settings['fg_color'], font=bold_font_tuple, width=bar_width, anchor='w').grid(row=row_idx, column=col_idx+1, padx=0, pady=0, sticky='w', ipady=0) # Interlinea ridotta con ipady=0
        
        # Configura minsize per le colonne per un layout piÃ¹ compatto
        # Ã necessario tkfont per .measure()
        font_for_measure_base = tkfont.Font(family='Courier New', size=14) # Font aumentato a 11px
        font_for_measure_bold = tkfont.Font(family='Courier New', size=14, weight='bold') # Font aumentato a 11px
        
        self.insights_matrix_frame.grid_columnconfigure(0, minsize=font_for_measure_base.measure("Stressato:")) # Spazio ridotto
        for i in range(1, self.insights_num_days_to_display + 1): 
            self.insights_matrix_frame.grid_columnconfigure(i, minsize=font_for_measure_bold.measure("|■■■|")) # Rimosso "A" extra per ridurre spazio tra colonne 
        
        # Configura row weights per espandere verticalmente se necessario (anche se con font fissi Ã¨ meno critico)
        for i in range(2 + len(self.emotions_analyzer.emotions_list)): # 2 righe header + righe emozioni
            self.insights_matrix_frame.grid_rowconfigure(i, weight=1)


    def show_insights(self):
        self.current_screen = 'insights'
        self.clear_screen()
        
        insights_container_frame = tk.Frame(self.main_frame, bg=self.settings['bg_color'])
        insights_container_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10) # Padding ridotto per piÃ¹ spazio

        title = tk.Label(insights_container_frame, text="📊 EMOZIONI SETTIMANALI",
                         bg=self.settings['bg_color'],
                         fg=self.settings['fg_color'],
                         font=('Courier New', 24, 'bold'))
        title.pack(pady=(5,3)) 

        self.insights_week_title_label = tk.Label(insights_container_frame, text="--- Caricamento Settimana ---",
                                 bg=self.settings['bg_color'],
                                 fg=self.settings['fg_color'],
                                 font=('Courier New', 14, 'italic'))
        self.insights_week_title_label.pack(pady=(0,2))

        self.insights_matrix_frame = tk.Frame(insights_container_frame, bg=self.settings['bg_color'])
        self.insights_matrix_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # Padding minimo per massimizzare lo spazio 
        
        self._display_insights_matrix() 
        
        instructions = tk.Label(insights_container_frame,
                                text="← Sett. Prec. | → Sett. Succ. | ESC Menu",
                                bg=self.settings['bg_color'],
                                fg=self.settings['fg_color'],
                                font=('Courier New', 16)) # Font ridotto
        instructions.pack(side=tk.BOTTOM, pady=(10,5)) # Padding ridotto
        
        # Unbind vecchi tasti se presenti da altre schermate
        self.root.unbind('<Up>')
        self.root.unbind('<Down>')
        self.root.unbind('<Return>')
        # Lega i nuovi tasti per la navigazione settimanale
        self.root.bind('<Left>', lambda event: self._navigate_insights_week('prev'))
        self.root.bind('<Right>', lambda event: self._navigate_insights_week('next'))
        
        insights_container_frame.focus_set()
    
    def scroll_text_up(self, event=None):
        """Scorre il testo verso l'alto quando si preme la freccia su"""
        if self.current_screen == 'editor' and hasattr(self, 'text'):
            # Interrompe eventuali scorrimenti precedenti
            if self.scroll_timer_id:
                self.root.after_cancel(self.scroll_timer_id)
                
            # Scorre il testo
            self.text.yview_scroll(-self.scroll_speed, "units")
            
            # Aumenta gradualmente la velocitÃ  e continua lo scorrimento se il tasto Ã¨ ancora premuto
            self.scroll_speed = min(10, self.scroll_speed + 1)  # Limita a max 10
            self.scroll_timer_id = self.root.after(100, lambda: self.scroll_text_up(None))
            
    def scroll_text_down(self, event=None):
        """Scorre il testo verso il basso quando si preme la freccia giÃ¹"""
        if self.current_screen == 'editor' and hasattr(self, 'text'):
            # Interrompe eventuali scorrimenti precedenti
            if self.scroll_timer_id:
                self.root.after_cancel(self.scroll_timer_id)
                
            # Scorre il testo
            self.text.yview_scroll(self.scroll_speed, "units")
            
            # Aumenta gradualmente la velocitÃ  e continua lo scorrimento se il tasto Ã¨ ancora premuto
            self.scroll_speed = min(10, self.scroll_speed + 1)  # Limita a max 10
            self.scroll_timer_id = self.root.after(100, lambda: self.scroll_text_down(None))
            
    def reset_scroll_speed(self, event=None):
        """Resetta la velocitÃ  di scorrimento quando si rilascia un tasto"""
        if self.current_screen == 'editor':
            # Interrompe lo scorrimento quando il tasto viene rilasciato
            if self.scroll_timer_id:
                self.root.after_cancel(self.scroll_timer_id)
                self.scroll_timer_id = None
            self.scroll_speed = 1  # Ripristina la velocitÃ  iniziale


    def setup_screensaver(self):
        """Setup the screensaver manager"""
        self.screensaver_manager = ScreensaverManager(self)
        # Bind F12 for manual screensaver toggle
        self.root.bind('<F12>', lambda e: self.toggle_screensaver())
        # Start automatic monitoring
        self.screensaver_manager.start_monitoring()
        
    def toggle_screensaver(self):
        """Toggle screensaver on/off manually"""
        if (self.screensaver_manager and 
            self.screensaver_manager.screensaver and
            self.screensaver_manager.screensaver.is_active):
            self.screensaver_manager.reset_activity_timer()
        else:
            self.screensaver_manager.activate_screensaver()

    def run(self):
        """Starts the Tkinter main event loop."""
        # Configurazione per la chiusura pulita dell'applicazione
        def on_closing():
            print("on_closing called...") 
            # Pulisce eventuali timer attivi
            if self.scroll_timer_id:
                self.root.after_cancel(self.scroll_timer_id)
            # Stop screensaver monitoring
            if self.screensaver_manager:
                self.screensaver_manager.stop_monitoring()
            # Qui potresti aggiungere altre operazioni di pulizia se necessario,
            # ad esempio salvare lo stato, chiudere connessioni, ecc.
            self.root.destroy()
            print("Reminor application closed via WM_DELETE_WINDOW.") 
            
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        print("Starting Tkinter mainloop...") 
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Error during mainloop: {e}") 
            import traceback
            traceback.print_exc() 
        finally:
            print("Tkinter mainloop finished.")


class ChronosScreensaver:
    def __init__(self, parent_frame: tk.Frame, journal_dir: Path, settings: dict):
        self.parent_frame = parent_frame
        self.journal_dir = journal_dir
        self.settings = settings
        self.screensaver_frame = None
        self.clock_update_id = None
        self.is_active = False
        
        # Font configurations - usando Courier New Regular e Bold
        try:
            # Testa se Courier New Ã¨ disponibile
            test_font = tkfont.Font(family='Courier New', size=12)
            if 'courier prime' in test_font.actual()['family'].lower():
                self.font_family_regular = 'Courier New'
                self.font_family_bold = 'Courier New Bold'
            else:
                # Fallback a Courier New se Courier New non Ã¨ disponibile
                self.font_family_regular = 'Courier New'
                self.font_family_bold = 'Courier New'
        except:
            # Fallback sicuro
            self.font_family_regular = 'Courier New'
            self.font_family_bold = 'Courier New'
            
        self.font_time = (self.font_family_bold, 72)      # Ora principale - Bold
        self.font_date = (self.font_family_regular, 28)   # Data - Regular
        self.font_month = (self.font_family_regular, 24)  # Mese/anno - Regular
        
    def activate(self):
        """Attiva lo screensaver"""
        if self.is_active:
            return
            
        self.is_active = True
        
        # Pulisce il frame genitore e crea il screensaver
        for widget in self.parent_frame.winfo_children():
            widget.pack_forget()
            
        self.screensaver_frame = tk.Frame(
            self.parent_frame,
            bg=self.settings.get('bg_color', '#000000')
        )
        self.screensaver_frame.pack(fill=tk.BOTH, expand=True)
        
        self.setup_screensaver_ui()
        self.update_clock()
        
        # Bind per disattivazione con qualsiasi tasto
        self.screensaver_frame.bind('<Key>', self.deactivate)
        self.screensaver_frame.bind('<Button-1>', self.deactivate)
        self.screensaver_frame.focus_set()
        
    def deactivate(self, event=None):
        """Disattiva lo screensaver"""
        if not self.is_active:
            return
            
        self.is_active = False
        
        # Cancella timer di aggiornamento
        if self.clock_update_id:
            self.parent_frame.after_cancel(self.clock_update_id)
            self.clock_update_id = None
            
        # Rimuove il frame dello screensaver
        if self.screensaver_frame:
            self.screensaver_frame.destroy()
            self.screensaver_frame = None
            
        # Restituisce il controllo al chiamante
        return "deactivated"
        
    def setup_screensaver_ui(self):
        """Crea l'interfaccia dello screensaver"""
        # Container principale centrato
        main_container = tk.Frame(
            self.screensaver_frame,
            bg=self.settings.get('bg_color', '#000000')
        )
        main_container.pack(expand=True)
        
        # Ora principale
        self.time_label = tk.Label(
            main_container,
            text="--:--",
            font=self.font_time,
            bg=self.settings.get('bg_color', '#000000'),
            fg=self.settings.get('fg_color', '#3B8ED0')
        )
        self.time_label.pack(pady=(50, 10))
        
        # Giorno e data
        self.date_label = tk.Label(
            main_container,
            text="Giorno Data",
            font=self.font_date,
            bg=self.settings.get('bg_color', '#000000'),
            fg=self.settings.get('fg_color', '#3B8ED0')
        )
        self.date_label.pack(pady=5)
        
        # Mese e anno
        self.month_label = tk.Label(
            main_container,
            text="Mese Anno",
            font=self.font_month,
            bg=self.settings.get('bg_color', '#000000'),
            fg=self.settings.get('fg_color', '#3B8ED0')
        )
        self.month_label.pack(pady=5)
        
        # Spazio prima degli indicatori
        spacer = tk.Frame(
            main_container,
            height=40,
            bg=self.settings.get('bg_color', '#000000')
        )
        spacer.pack()
        
        # Frame per gli indicatori di attivitÃ  settimanale
        self.activity_frame = tk.Frame(
            main_container,
            bg=self.settings.get('bg_color', '#000000')
        )
        self.activity_frame.pack(pady=20)
        
        # Crea gli indicatori (7 giorni)
        self.activity_indicators = []
        for i in range(7):
            indicator = tk.Label(
                self.activity_frame,
                text="●",
                font=(self.font_family_regular, 40),
                bg=self.settings.get('bg_color', '#000000'),
                fg='#333333'  # Colore di default (inattivo)
            )
            indicator.pack(side=tk.LEFT, padx=12)
            self.activity_indicators.append(indicator)
            
            
        # Istruzioni discrete in basso
        instruction_label = tk.Label(
            main_container,
            text="Premi un tasto per continuare",
            font=(self.font_family_regular, 22),
            bg=self.settings.get('bg_color', '#000000'),
            fg='#666666'
        )
        instruction_label.pack(pady=(80, 30))
        
    def get_week_activity(self):
        """Analizza l'attivitÃ  di scrittura degli ultimi 7 giorni"""
        today = datetime.date.today()
        activity = []
        
        # Calcola l'inizio della settimana (LunedÃ¬)
        days_since_monday = today.weekday()
        monday = today - datetime.timedelta(days=days_since_monday)
        
        for i in range(7):
            day = monday + datetime.timedelta(days=i)
            date_str = day.strftime('%Y-%m-%d')
            file_path = self.journal_dir / f"{date_str}.txt"
            
            # Controlla se esiste il file e ha contenuto
            has_content = (
                file_path.exists() and 
                file_path.stat().st_size > 10  # Almeno 10 caratteri
            )
            activity.append(has_content)
            
        return activity
        
    def update_activity_indicators(self):
        """Aggiorna gli indicatori di attivitÃ  settimanale"""
        activity = self.get_week_activity()
        
        for i, (indicator, has_activity) in enumerate(zip(self.activity_indicators, activity)):
            if has_activity:
                # Colore attivo - gradazione basata sulla quantitÃ 
                try:
                    day = datetime.date.today() - datetime.timedelta(
                        days=datetime.date.today().weekday() - i
                    )
                    date_str = day.strftime('%Y-%m-%d')
                    file_path = self.journal_dir / f"{date_str}.txt"
                    
                    if file_path.exists():
                        size = file_path.stat().st_size
                        if size > 1000:  # Molto contenuto
                            color = self.settings.get('fg_color', '#3B8ED0')
                        elif size > 500:  # Contenuto medio
                            color = '#88ff88'
                        else:  # Poco contenuto
                            color = '#44ff44'
                    else:
                        color = '#444444'
                        
                except Exception:
                    color = self.settings.get('fg_color', '#3B8ED0')
                    
                indicator.config(fg=color)
            else:
                # Colore inattivo
                indicator.config(fg='#333333')
                
    def update_clock(self):
        """Aggiorna ora, data e indicatori"""
        if not self.is_active:
            return
            
        now = datetime.datetime.now()
        
        # Aggiorna ora
        time_str = now.strftime('%H:%M')
        self.time_label.config(text=time_str)
        
        # Aggiorna data con localizzazione italiana corretta
        try:
            # Mappa con giorni italiani grammaticalmente corretti con accenti
            italian_days = {
                0: 'Lunedì',
                1: 'Martedì',
                2: 'Mercoledì',
                3: 'Giovedì',
                4: 'Venerdì',
                5: 'Sabato',
                6: 'Domenica'
            }

            italian_months = {
                1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile',
                5: 'Maggio', 6: 'Giugno', 7: 'Luglio', 8: 'Agosto',
                9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'
            }
            
            # Nome del giorno e numero con encoding UTF-8 esplicito
            day_name = italian_days.get(now.weekday(), 'Giorno')
            day_num = now.strftime('%d')
            
            # Verifica che il carattere sia visualizzabile correttamente
            try:
                # Test se il font puÃ² renderizzare correttamente gli accenti
                test_label = tk.Label(self.screensaver_frame, text="GiovedÃ¬", font=self.font_date)
                date_str = f"{day_name} {day_num}"
                test_label.destroy()  # Pulisce il test
            except:
                # Fallback se ci sono problemi con il rendering
                fallback_days = {
                    0: 'Lunedi', 1: 'Martedi', 2: 'Mercoledi',
                    3: 'Giovedi', 4: 'Venerdi', 5: 'Sabato', 6: 'Domenica'
                }
                day_name = fallback_days.get(now.weekday(), 'Giorno')
                date_str = f"{day_name} {day_num}"
            
            # Mese e anno
            month_name = italian_months.get(now.month, 'Mese')
            year = now.strftime('%Y')
            month_year = f"{month_name} {year}"
            
        except Exception:
            # Fallback in inglese se localizzazione fallisce
            date_str = now.strftime('%A %d')
            month_year = now.strftime('%B %Y')
            
        self.date_label.config(text=date_str)
        self.month_label.config(text=month_year)
        
        # Aggiorna indicatori di attivitÃ 
        self.update_activity_indicators()
        
        # Programma prossimo aggiornamento ogni 30 secondi
        self.clock_update_id = self.parent_frame.after(30000, self.update_clock)


class ScreensaverManager:
    """Gestisce l'attivazione automatica dello screensaver"""

    def __init__(self, app_instance):
        self.app = app_instance
        self.screensaver = None
        self.last_activity_time = datetime.datetime.now()
        self.check_timer_id = None
        self.screensaver_delay = 180  # 3 minuti di inattività
        self.is_monitoring = False

    def start_monitoring(self):
        """Inizia il monitoraggio per l'attivazione automatica"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.last_activity_time = datetime.datetime.now()
        self.check_for_inactivity()

        # Bind eventi di attività sulla finestra principale
        self.app.root.bind('<Any-KeyPress>', self.reset_activity_timer)
        self.app.root.bind('<Button>', self.reset_activity_timer)
        self.app.root.bind('<Motion>', self.reset_activity_timer)

    def stop_monitoring(self):
        """Ferma il monitoraggio"""
        self.is_monitoring = False

        if self.check_timer_id:
            self.app.root.after_cancel(self.check_timer_id)
            self.check_timer_id = None

        # Rimuovi bind eventi
        try:
            self.app.root.unbind('<Any-KeyPress>')
            self.app.root.unbind('<Button>')
            self.app.root.unbind('<Motion>')
        except Exception:
            pass

    def reset_activity_timer(self, event=None):
        """Resetta il timer di attività"""
        self.last_activity_time = datetime.datetime.now()

        # Se lo screensaver è attivo, disattivalo
        if self.screensaver and self.screensaver.is_active:
            result = self.screensaver.deactivate()
            if result == "deactivated":
                # Ripristina la schermata precedente
                self.app.show_home_screen()

    def check_for_inactivity(self):
        """Controlla se attivare lo screensaver per inattività"""
        if not self.is_monitoring:
            return

        elapsed = (datetime.datetime.now() - self.last_activity_time).total_seconds()

        if elapsed >= self.screensaver_delay:
            # Attiva lo screensaver solo se non stiamo scrivendo
            if (
                hasattr(self.app, 'current_screen')
                and self.app.current_screen in ['home', 'calendar', 'search', 'settings', 'insights']
            ):
                self.activate_screensaver()

        # Controlla di nuovo tra 30 secondi
        self.check_timer_id = self.app.root.after(30000, self.check_for_inactivity)

    def activate_screensaver(self):
        """Attiva lo screensaver"""
        if not self.screensaver:
            self.screensaver = ChronosScreensaver(
                self.app.main_frame,
                self.app.journal_dir,
                self.app.settings
            )

        self.screensaver.activate()
        self.app.current_screen = 'screensaver'


class OnboardingScreen:
    """
    Schermata di onboarding per nuovi utenti.
    Raccoglie nome utente e API key Groq al primo avvio.
    """

    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.completed = False
        self.user_name = ""
        self.api_key = ""

        # Pulisce il frame principale
        for widget in app.main_frame.winfo_children():
            widget.destroy()

        self.setup_onboarding_ui()
        self.bind_events()

    def setup_onboarding_ui(self):
        """Crea l'interfaccia di onboarding"""

        # Container principale centrato
        self.main_container = ctk.CTkFrame(
            self.app.main_frame,
            fg_color=self.app.settings['bg_color'],
            corner_radius=20
        )
        self.main_container.pack(expand=True, fill='both', padx=40, pady=40)

        # Titolo di benvenuto
        self.title_label = ctk.CTkLabel(
            self.main_container,
            text="🎉 Benvenuto in Reminor!",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.app.settings['fg_color']
        )
        self.title_label.pack(pady=(30, 10))

        # Sottotitolo
        self.subtitle_label = ctk.CTkLabel(
            self.main_container,
            text="Il tuo diario digitale intelligente con AI integrata",
            font=ctk.CTkFont(size=18),
            text_color="#bbbbbb"  # Grigio più chiaro per tema Notte
        )
        self.subtitle_label.pack(pady=(0, 30))

        # Frame per i campi di input
        self.form_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.form_frame.pack(pady=20, padx=40, fill='x')

        # Campo Nome Utente
        self.name_label = ctk.CTkLabel(
            self.form_frame,
            text="👤 Come ti chiami?",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.app.settings['fg_color']
        )
        self.name_label.pack(pady=(20, 10), anchor='w')

        self.name_entry = ctk.CTkEntry(
            self.form_frame,
            placeholder_text="Inserisci il tuo nome...",
            font=ctk.CTkFont(size=16),
            height=40,
            corner_radius=10
        )
        self.name_entry.pack(pady=(0, 20), fill='x')

        # Campo API Key
        self.api_label = ctk.CTkLabel(
            self.form_frame,
            text="🔑 API Key Groq (opzionale)",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.app.settings['fg_color']
        )
        self.api_label.pack(pady=(20, 10), anchor='w')

        self.api_info_label = ctk.CTkLabel(
            self.form_frame,
            text="Per usare l'AI integrata, ottieni una chiave gratuita da console.groq.com",
            font=ctk.CTkFont(size=14),
            text_color="#aaaaaa",  # Grigio più chiaro per tema Notte
            wraplength=500
        )
        self.api_info_label.pack(pady=(0, 10), anchor='w')

        self.api_entry = ctk.CTkEntry(
            self.form_frame,
            placeholder_text="gsk_... (lascia vuoto per usare solo l'editor)",
            font=ctk.CTkFont(size=16),
            height=40,
            corner_radius=10,
            show="*"  # Nasconde la chiave
        )
        self.api_entry.pack(pady=(0, 30), fill='x')

        # Pulsanti
        self.button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.button_frame.pack(pady=20, fill='x')

        self.skip_button = ctk.CTkButton(
            self.button_frame,
            text="⏭️ Salta (solo editor)",
            font=ctk.CTkFont(size=16),
            height=40,
            width=200,
            fg_color="#666666",
            hover_color="#777777",
            command=self.skip_setup
        )
        self.skip_button.pack(side='left', padx=(20, 10))

        self.continue_button = ctk.CTkButton(
            self.button_frame,
            text="✅ Inizia!",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            width=200,
            fg_color=self.app.settings['fg_color'],
            command=self.complete_setup
        )
        self.continue_button.pack(side='right', padx=(10, 20))

        # Area aiuto keyboard
        self.help_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.help_frame.pack(pady=(20, 10), fill='x')

        self.help_label = ctk.CTkLabel(
            self.help_frame,
            text="🎹 Navigazione: FRECCE/TAB per spostarsi • ENTER per confermare • ESC per saltare",
            font=ctk.CTkFont(size=12),
            text_color="#999999"
        )
        self.help_label.pack()


    def bind_events(self):
        """Associa eventi keyboard"""
        self.root.bind('<Escape>', lambda e: self.skip_setup())

        # Lista di elementi navigabili (ordine di navigazione)
        self.focusable_elements = [
            ('entry', self.name_entry),
            ('entry', self.api_entry),
            ('button', self.continue_button, self.complete_setup),
            ('button', self.skip_button, self.skip_setup)
        ]
        self.current_focus_index = 0

        # Binding per navigazione con frecce
        self.root.bind('<Up>', self.navigate_up)
        self.root.bind('<Down>', self.navigate_down)
        self.root.bind('<Left>', self.navigate_up)
        self.root.bind('<Right>', self.navigate_down)
        self.root.bind('<Return>', self.handle_enter)

        # Tab navigation
        self.name_entry.bind('<Tab>', lambda e: self.navigate_down(e))
        self.api_entry.bind('<Tab>', lambda e: self.navigate_down(e))

        # Memorizza i colori originali dei pulsanti PRIMA del focus
        self.original_button_colors = {
            'continue': {
                'fg_color': self.continue_button.cget('fg_color'),
                'hover_color': self.continue_button.cget('hover_color')
            },
            'skip': {
                'fg_color': self.skip_button.cget('fg_color'),
                'hover_color': self.skip_button.cget('hover_color')
            }
        }

        # Focus iniziale
        self.focus_element(0)

    def navigate_up(self, event=None):
        """Naviga all'elemento precedente"""
        self.current_focus_index = (self.current_focus_index - 1) % len(self.focusable_elements)
        self.focus_element(self.current_focus_index)
        return "break"  # Previene comportamento default

    def navigate_down(self, event=None):
        """Naviga all'elemento successivo"""
        self.current_focus_index = (self.current_focus_index + 1) % len(self.focusable_elements)
        self.focus_element(self.current_focus_index)
        return "break"  # Previene comportamento default

    def focus_element(self, index):
        """Mette il focus sull'elemento specificato"""
        if 0 <= index < len(self.focusable_elements):
            # Reset di tutti i pulsanti ai colori originali
            self.continue_button.configure(
                fg_color=self.original_button_colors['continue']['fg_color']
            )
            self.skip_button.configure(
                fg_color=self.original_button_colors['skip']['fg_color']
            )

            element_info = self.focusable_elements[index]
            element_type = element_info[0]
            element = element_info[1]

            if element_type == 'entry':
                # Per le entry, usa il focus normale
                element.focus()
            elif element_type == 'button':
                # Per i pulsanti, cambia il colore per indicare focus
                if element == self.continue_button:
                    element.configure(fg_color="#4CAF50")  # Verde brillante
                elif element == self.skip_button:
                    element.configure(fg_color="#FF9800")  # Arancione brillante
                # Rimuovi focus da eventuali entry
                self.root.focus()

            self.current_focus_index = index

    def handle_enter(self, event=None):
        """Gestisce il tasto ENTER in base all'elemento attualmente focalizzato"""
        if 0 <= self.current_focus_index < len(self.focusable_elements):
            element_info = self.focusable_elements[self.current_focus_index]
            element_type = element_info[0]

            if element_type == 'button':
                # Se è un pulsante, chiama la sua funzione
                callback = element_info[2]
                callback()
            elif element_type == 'entry':
                # Se è una entry, passa al prossimo elemento
                self.navigate_down()
        return "break"

    def skip_setup(self):
        """Salta l'onboarding - solo nome richiesto"""
        name = self.name_entry.get().strip()
        if not name:
            name = "Utente"

        self.user_name = name
        self.api_key = ""
        self.save_onboarding_data()
        self.complete_onboarding()

    def complete_setup(self):
        """Completa l'onboarding con validazione"""
        name = self.name_entry.get().strip()
        api_key = self.api_entry.get().strip()

        if not name:
            # Mostra errore per nome mancante
            self.show_error("Il nome è obbligatorio!")
            self.name_entry.focus()
            return

        # Validazione API key (opzionale ma se presente deve essere valida)
        if api_key and not api_key.startswith('gsk_'):
            self.show_error("La API key deve iniziare con 'gsk_'")
            self.api_entry.focus()
            return

        self.user_name = name
        self.api_key = api_key
        self.save_onboarding_data()
        self.complete_onboarding()

    def show_error(self, message):
        """Mostra un messaggio di errore temporaneo"""
        if hasattr(self, 'error_label'):
            self.error_label.destroy()

        self.error_label = ctk.CTkLabel(
            self.form_frame,
            text=f"❌ {message}",
            font=ctk.CTkFont(size=14),
            text_color="#ff4444"
        )
        self.error_label.pack(pady=5)

        # Rimuovi l'errore dopo 3 secondi
        self.root.after(3000, lambda: self.error_label.destroy() if hasattr(self, 'error_label') else None)

    def save_onboarding_data(self):
        """Salva i dati di onboarding nelle impostazioni e .env"""
        # Aggiorna settings
        self.app.settings['first_run'] = False
        self.app.settings['user_name'] = self.user_name
        self.app.save_settings()

        # Salva API key in .env se fornita
        if self.api_key:
            # File .env nella directory del progetto
            env_file = Path(__file__).parent / '.env'
            try:
                # Leggi .env esistente o crea nuovo
                env_content = ""
                if env_file.exists():
                    env_content = env_file.read_text(encoding='utf-8')

                # Aggiorna o aggiungi GROQ_API_KEY
                lines = env_content.split('\n')
                found = False
                for i, line in enumerate(lines):
                    if line.startswith('GROQ_API_KEY='):
                        lines[i] = f'GROQ_API_KEY={self.api_key}'
                        found = True
                        break

                if not found:
                    lines.append(f'GROQ_API_KEY={self.api_key}')

                # Scrivi il file .env
                env_file.write_text('\n'.join(lines), encoding='utf-8')

                # Ricarica le variabili d'ambiente
                os.environ['GROQ_API_KEY'] = self.api_key

            except Exception as e:
                print(f"Errore nel salvataggio API key: {e}")

    def complete_onboarding(self):
        """Completa l'onboarding e passa alla schermata principale"""
        self.completed = True

        # Rimuovi gli event handlers temporanei
        self.root.unbind('<Return>')
        self.root.unbind('<Escape>')

        # Pulisce l'interfaccia di onboarding
        for widget in self.app.main_frame.winfo_children():
            widget.destroy()

        # Inizializza il resto dell'app
        self.app.show_home_screen()


def main():
    """Punto di ingresso per inizializzare ed eseguire l'app Reminor."""
    print("Application starting...")
    try:
        app = ReminorApp()
        print("ReminorApp instance created.")
        app.run()
    except Exception as e:
        print(f"A critical error occurred during app initialization or run: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Application __main__ block finished.")


if __name__ == "__main__":
    main()

