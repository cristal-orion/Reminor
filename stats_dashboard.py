#!/usr/bin/env python3
"""
Dashboard delle statistiche minimalista per Reminor
Sostituisce il profilo psicologico complesso con 4 card semplici e motivanti
"""

import customtkinter as ctk
import tkinter as tk
from pathlib import Path
import datetime
from collections import Counter
import json
import re
from typing import Dict, List, Tuple
import random

class StatsDashboard:
    def __init__(self, parent_frame, journal_dir: Path, bg_color='#1a1a1a', fg_color='#3B8ED0'):
        self.parent_frame = parent_frame
        self.journal_dir = journal_dir
        self.bg_color = bg_color
        self.fg_color = fg_color

        # Memory highlight fisso che non cambia con scroll
        self.fixed_memory = None

        # Stopwords italiane comuni da escludere dall'analisi dei topic
        self.italian_stopwords = {
            'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
            'e', 'è', 'sono', 'sei', 'siamo', 'siete', 'hanno', 'ho', 'hai', 'ha', 'abbiamo', 'avete', 'che', 'chi', 'cosa',
            'come', 'quando', 'dove', 'perché', 'ma', 'però', 'quindi', 'così', 'allora', 'anche', 'ancora', 'già', 'più',
            'meno', 'molto', 'tanto', 'poco', 'troppo', 'ogni', 'tutto', 'tutti', 'tutte', 'niente', 'nulla', 'qualcosa',
            'qualcuno', 'qualcuna', 'alcuni', 'alcune', 'ieri', 'oggi', 'domani', 'ora', 'adesso', 'poi', 'prima', 'dopo',
            'sempre', 'mai', 'spesso', 'volte', 'volta', 'bene', 'male', 'meglio', 'peggio', 'questo', 'questa', 'questi',
            'queste', 'quello', 'quella', 'quelli', 'quelle', 'qui', 'qua', 'lì', 'là', 'dove', 'non', 'ne', 'ci', 'si', 'mi',
            'ti', 'vi', 'lo', 'la', 'li', 'le', 'me', 'te', 'lui', 'lei', 'noi', 'voi', 'loro', 'mio', 'mia', 'miei', 'mie',
            'tuo', 'tua', 'tuoi', 'tue', 'suo', 'sua', 'suoi', 'sue', 'nostro', 'nostra', 'nostri', 'nostre', 'vostro',
            'vostra', 'vostri', 'vostre', 'sto', 'stai', 'sta', 'stiamo', 'state', 'stanno', 'fare', 'faccio', 'fai', 'fa',
            'facciamo', 'fate', 'fanno', 'dire', 'dico', 'dici', 'dice', 'diciamo', 'dite', 'dicono', 'andare', 'vado', 'vai',
            'va', 'andiamo', 'andate', 'vanno', 'essere', 'avere', 'dal', 'dello', 'della', 'dei', 'delle', 'nel', 'nello',
            'nella', 'nei', 'negli', 'nelle', 'sul', 'sullo', 'sulla', 'sui', 'sugli', 'sulle', 'dal', 'dallo', 'dalla',
            'dai', 'dagli', 'dalle', 'del', 'al', 'allo', 'alla', 'ai', 'agli', 'alle', 'per', 'tra', 'fra', 'con'
        }

        self.scroll_position = 0
        self.card_height = 180  # Aumentato per contenere meglio il contenuto
        self.card_spacing = 25  # Più spazio tra le card
        self.cards_data = []

    def create_dashboard(self, canvas: tk.Canvas):
        """Crea la dashboard con 4 card delle statistiche"""
        # Clear canvas
        canvas.delete("all")

        # Header
        canvas.create_text(360, 30, text="STATISTICHE",
                         fill=self.fg_color, font=('Courier Prime', 28, 'bold'))

        # Calcola i dati per tutte le card
        streak_data = self._calculate_streak_data()
        volume_data = self._calculate_volume_data()
        topics_data = self._calculate_top_topics()

        # Memory data fisso (non cambia con scroll)
        if self.fixed_memory is None:
            self.fixed_memory = self._get_random_memory()
        memory_data = self.fixed_memory

        self.cards_data = [
            ("STREAK 🔥", streak_data, self._draw_streak_card),
            ("VOLUME 📝", volume_data, self._draw_volume_card),
            ("TOP TOPICS 💭", topics_data, self._draw_topics_card),
            ("MEMORY HIGHLIGHT 💡", memory_data, self._draw_memory_card)
        ]

        # Calcola posizioni verticali considerando lo scroll
        start_y = 80
        visible_area_height = 580  # Altezza visibile

        for i, (title, data, draw_func) in enumerate(self.cards_data):
            card_y = start_y + i * (self.card_height + self.card_spacing) - self.scroll_position

            # Disegna solo se la card è almeno parzialmente visibile
            if card_y + self.card_height > 0 and card_y < visible_area_height:
                self._draw_card_background(canvas, 40, card_y, 640, self.card_height)

                # Titolo card
                canvas.create_text(50, card_y + 18, text=title,
                                 fill=self.fg_color, font=('Courier Prime', 18, 'bold'), anchor='w')

                # Linea separatore sotto il titolo
                canvas.create_line(50, card_y + 35, 670, card_y + 35,
                                 fill='#3B8ED0', width=1)

                draw_func(canvas, 50, card_y + 50, 600, self.card_height - 60, data)

        # Footer con più opzioni
        canvas.create_text(360, 680, text="↑↓ Scorri | R Nuovo ricordo | ESC Menu",
                         fill='#888888', font=('Courier Prime', 14))

    def _draw_card_background(self, canvas, x, y, width, height):
        """Disegna il background di una card"""
        # Card con bordi più sottili e ombra leggera
        canvas.create_rectangle(x+3, y+3, x + width+3, y + height+3,
                              fill='#0a0a0a', outline='', width=0)  # Ombra più scura
        canvas.create_rectangle(x, y, x + width, y + height,
                              fill='#252525', outline='#3B8ED0', width=2)  # Bordo colorato

    def _calculate_streak_data(self) -> Dict:
        """Calcola dati per la STREAK CARD"""
        today = datetime.date.today()

        # Trova tutti i giorni in cui è stato scritto
        written_dates = set()
        for file_path in self.journal_dir.glob("*.txt"):
            try:
                date_str = file_path.stem
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                written_dates.add(date_obj)
            except ValueError:
                continue

        # Calcola streak corrente
        current_streak = 0
        check_date = today
        while check_date in written_dates:
            current_streak += 1
            check_date = check_date - datetime.timedelta(days=1)

        # Se oggi non è stato scritto, controlla da ieri
        if today not in written_dates:
            current_streak = 0
            check_date = today - datetime.timedelta(days=1)
            while check_date in written_dates:
                current_streak += 1
                check_date = check_date - datetime.timedelta(days=1)

        # Calcola record storico
        max_streak = 0
        temp_streak = 0

        # Ordina le date e trova la sequenza più lunga
        sorted_dates = sorted(written_dates)
        if sorted_dates:
            current_check = sorted_dates[0]
            temp_streak = 1

            for i in range(1, len(sorted_dates)):
                if sorted_dates[i] == current_check + datetime.timedelta(days=1):
                    temp_streak += 1
                else:
                    max_streak = max(max_streak, temp_streak)
                    temp_streak = 1
                current_check = sorted_dates[i]

            max_streak = max(max_streak, temp_streak)

        # Ultimi 14 giorni per visualizzazione
        last_14_days = []
        for i in range(13, -1, -1):  # Da 13 giorni fa a oggi
            check_date = today - datetime.timedelta(days=i)
            last_14_days.append(check_date in written_dates)

        return {
            'current_streak': current_streak,
            'record_streak': max_streak,
            'last_14_days': last_14_days
        }

    def _calculate_volume_data(self) -> Dict:
        """Calcola dati per la VOLUME CARD"""
        today = datetime.date.today()

        # Parole scritte questo mese
        month_start = today.replace(day=1)
        month_words = 0
        days_written = 0
        daily_words = []

        # Conta parole per giorno della settimana
        weekday_words = [0] * 7  # Lunedì=0, Domenica=6
        weekday_days = [0] * 7

        for file_path in self.journal_dir.glob("*.txt"):
            try:
                date_str = file_path.stem
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

                # Leggi contenuto e conta parole
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    words = len(content.split())

                # Se è di questo mese
                if date_obj >= month_start and date_obj <= today:
                    month_words += words
                    days_written += 1
                    daily_words.append(words)

                # Statistiche per giorno della settimana (ultimi 30 giorni)
                if date_obj >= today - datetime.timedelta(days=30):
                    weekday = date_obj.weekday()
                    weekday_words[weekday] += words
                    weekday_days[weekday] += 1

            except (ValueError, FileNotFoundError):
                continue

        # Media parole/giorno
        avg_words = month_words / max(days_written, 1)

        # Giorno più produttivo
        best_weekday_idx = 0
        best_avg = 0
        weekday_names = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']

        for i in range(7):
            if weekday_days[i] > 0:
                avg = weekday_words[i] / weekday_days[i]
                if avg > best_avg:
                    best_avg = avg
                    best_weekday_idx = i

        # Progresso verso obiettivo 15.000 parole
        target = 15000
        progress = min(month_words / target, 1.0)

        return {
            'month_words': month_words,
            'avg_words': int(avg_words),
            'progress': progress,
            'best_weekday': weekday_names[best_weekday_idx],
            'target': target
        }

    def _calculate_top_topics(self) -> List[Tuple[str, int]]:
        """Calcola i 5 argomenti più ricorrenti negli ultimi 30 giorni"""
        today = datetime.date.today()
        thirty_days_ago = today - datetime.timedelta(days=30)

        all_words = []

        for file_path in self.journal_dir.glob("*.txt"):
            try:
                date_str = file_path.stem
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

                # Solo ultimi 30 giorni
                if date_obj >= thirty_days_ago:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()

                        # Rimuovi punteggiatura e split
                        content = re.sub(r'[^\w\s]', ' ', content)
                        words = content.split()

                        # Filtra parole significative (minimo 5 caratteri per evitare parole troppo comuni)
                        filtered_words = [
                            word for word in words
                            if len(word) >= 5 and word not in self.italian_stopwords and not word.isdigit()
                        ]

                        all_words.extend(filtered_words)

            except (ValueError, FileNotFoundError):
                continue

        # Conta occorrenze
        if not all_words:
            return [("Nessun dato", 0)]

        word_counts = Counter(all_words)
        return word_counts.most_common(5)

    def _get_random_memory(self) -> Dict:
        """Ottiene un ricordo casuale da più di 30 giorni fa"""
        today = datetime.date.today()
        thirty_days_ago = today - datetime.timedelta(days=30)

        old_entries = []

        for file_path in self.journal_dir.glob("*.txt"):
            try:
                date_str = file_path.stem
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

                # Solo entrate più vecchie di 30 giorni
                if date_obj < thirty_days_ago:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if len(content) > 50:  # Solo se c'è contenuto significativo
                            old_entries.append({
                                'date': date_obj,
                                'content': content
                            })

            except (ValueError, FileNotFoundError):
                continue

        if not old_entries:
            return {
                'date': 'Nessun ricordo',
                'preview': 'Continua a scrivere per creare dei ricordi da rileggere!'
            }

        # Seleziona casualmente
        selected = random.choice(old_entries)

        # Formatta la data in italiano
        months = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']

        date_str = f"{selected['date'].day} {months[selected['date'].month]} {selected['date'].year}"

        # Prime 200 caratteri
        preview = selected['content'][:200]
        if len(selected['content']) > 200:
            preview += "..."

        return {
            'date': date_str,
            'preview': preview
        }

    def _draw_streak_card(self, canvas, x, y, width, height, data):
        """Disegna la STREAK CARD"""
        # Giorni consecutivi (grande)
        canvas.create_text(x + 10, y, text=f"{data['current_streak']} giorni consecutivi",
                         fill='#ffffff', font=('Courier Prime', 17, 'bold'), anchor='w')

        # Visualizzazione ultimi 14 giorni (2 righe da 7)
        dot_spacing = 18
        start_x = x + 15
        dot_y = y + 40

        for i, written in enumerate(data['last_14_days']):
            row = i // 7
            col = i % 7
            dot_x = start_x + col * dot_spacing
            current_y = dot_y + row * 25

            symbol = "▓" if written else "░"
            color = '#4CAF50' if written else '#555555'
            canvas.create_text(dot_x, current_y, text=symbol,
                             fill=color, font=('Courier Prime', 15), anchor='w')

        # Record personale
        canvas.create_text(x + 10, y + 95, text=f"Record: {data['record_streak']} giorni",
                         fill='#999999', font=('Courier Prime', 13), anchor='w')

    def _draw_volume_card(self, canvas, x, y, width, height, data):
        """Disegna la VOLUME CARD"""
        # Parole questo mese
        canvas.create_text(x + 10, y, text=f"{data['month_words']:,} parole questo mese",
                         fill='#ffffff', font=('Courier Prime', 17, 'bold'), anchor='w')

        # Barra progresso ASCII (ridotta)
        progress_width = 25
        filled_chars = int(data['progress'] * progress_width)
        progress_bar = "█" * filled_chars + "░" * (progress_width - filled_chars)
        progress_percent = int(data['progress'] * 100)

        canvas.create_text(x + 10, y + 30, text=f"{progress_bar} {progress_percent}%",
                         fill='#3B8ED0', font=('Courier Prime', 12, 'bold'), anchor='w')

        canvas.create_text(x + 10, y + 50, text=f"Obiettivo: {data['target']:,} parole/mese",
                         fill='#777777', font=('Courier Prime', 11, 'italic'), anchor='w')

        # Media parole/giorno
        canvas.create_text(x + 10, y + 75, text=f"Media: {data['avg_words']} parole/giorno",
                         fill='#999999', font=('Courier Prime', 13), anchor='w')

        # Giorno più produttivo
        canvas.create_text(x + 10, y + 95, text=f"Giorno top: {data['best_weekday']}",
                         fill='#999999', font=('Courier Prime', 13), anchor='w')

    def _draw_topics_card(self, canvas, x, y, width, height, data):
        """Disegna la TOP TOPICS CARD"""
        if not data or data[0][0] == "Nessun dato":
            canvas.create_text(x + 10, y + 30, text="Scrivi di più per vedere i trend",
                             fill='#777777', font=('Courier Prime', 13, 'italic'), anchor='w')
            return

        for i, (topic, count) in enumerate(data):
            topic_y = y + i * 22
            # Tronca topic troppo lunghi
            display_topic = topic[:20] + "..." if len(topic) > 20 else topic
            # Colore in base alla frequenza
            color = '#ffffff' if count > 10 else '#dddddd' if count > 5 else '#aaaaaa'

            # Topic nome
            canvas.create_text(x + 10, topic_y, text=f"• {display_topic}",
                             fill=color, font=('Courier Prime', 13), anchor='w')
            # Count allineato a destra
            canvas.create_text(x + width - 30, topic_y, text=f"{count}x",
                             fill='#3B8ED0', font=('Courier Prime', 12, 'bold'), anchor='e')

    def _draw_memory_card(self, canvas, x, y, width, height, data):
        """Disegna la MEMORY HIGHLIGHT CARD"""
        # Data
        canvas.create_text(x + 10, y, text=data['date'],
                         fill='#3B8ED0', font=('Courier Prime', 15, 'bold'), anchor='w')

        # Preview del contenuto (wrap text)
        preview = data['preview']
        words = preview.split()
        lines = []
        current_line = []
        max_chars = 60  # Ridotto ulteriormente

        for word in words:
            test_line = ' '.join(current_line + [word])
            if len(test_line) > max_chars:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Parola troppo lunga, tronca
                    lines.append(word[:max_chars] + "...")
                    current_line = []
            else:
                current_line.append(word)

        if current_line:
            lines.append(' '.join(current_line))

        # Disegna le linee (max 5 righe per card più alta)
        text_y = y + 30
        for line in lines[:5]:
            canvas.create_text(x + 10, text_y, text=line,
                             fill='#bbbbbb', font=('Courier Prime', 12), anchor='w')
            text_y += 18

    def scroll_up(self):
        """Scorri verso l'alto"""
        self.scroll_position = max(0, self.scroll_position - 30)  # Scroll più smooth

    def scroll_down(self):
        """Scorri verso il basso"""
        # Calcola il max scroll basato sul contenuto effettivo
        total_height = len(self.cards_data) * (self.card_height + self.card_spacing)
        max_scroll = max(0, total_height - 500)
        self.scroll_position = min(max_scroll, self.scroll_position + 30)

    def reset_memory(self):
        """Resetta il memory highlight per mostrare un nuovo ricordo"""
        self.fixed_memory = None

    def handle_keypress(self, event):
        """Gestisce i tasti premuti"""
        if event.keysym == "Up":
            self.scroll_up()
            return "break"
        elif event.keysym == "Down":
            self.scroll_down()
            return "break"
        elif event.keysym == "r" or event.keysym == "R":
            # R per refresh del memory highlight
            self.reset_memory()
            return "break"
        return None