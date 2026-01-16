#!/usr/bin/env python3
"""
Reminor Memory Server - API REST per structured memory e analisi NLP
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from flask import Flask, request, jsonify
from flask_cors import CORS

# Import delle classi esistenti di Reminor
import sys
from pathlib import Path

# Aggiungi la directory corrente al Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from enhanced_structured_memory import EnhancedStructuredMemory
    from enhanced_emotions_analyzer import EnhancedEmotionsAnalyzer
    spacy_available = True
except ImportError:
    EnhancedStructuredMemory = None
    EnhancedEmotionsAnalyzer = None
    spacy_available = False

app = Flask(__name__)
CORS(app)  # Permetti richieste da Go

# Configurazione
JOURNAL_DIR = Path.home() / ".mysoul_journal"
JOURNAL_DIR.mkdir(exist_ok=True)

# Istanze globali (inizializzate al primo uso)
structured_memory = None
emotions_analyzer = None

def get_structured_memory():
    """Lazy loading della structured memory"""
    global structured_memory
    if structured_memory is None:
        if EnhancedStructuredMemory:
            try:
                structured_memory = EnhancedStructuredMemory(JOURNAL_DIR)
            except Exception as e:
                print(f"[ERROR] Errore EnhancedStructuredMemory: {e}")
                structured_memory = MockStructuredMemory(JOURNAL_DIR)
        else:
            structured_memory = MockStructuredMemory(JOURNAL_DIR)
    return structured_memory

def get_emotions_analyzer():
    """Lazy loading dell'emotions analyzer"""
    global emotions_analyzer
    if emotions_analyzer is None:
        if EnhancedEmotionsAnalyzer:
            emotions_analyzer = EnhancedEmotionsAnalyzer(JOURNAL_DIR)
        else:
            emotions_analyzer = MockEmotionsAnalyzer()
    return emotions_analyzer

@dataclass
class ContextData:
    """Struttura per il contesto da inviare al chatbot"""
    relevant_entries: List[Dict]
    keywords: List[str]
    emotions: Dict[str, float]
    entities: List[Dict]
    time_patterns: Dict[str, any]
    summary: str

class MockStructuredMemory:
    """Mock per quando spaCy non è disponibile"""
    def __init__(self, journal_dir):
        self.journal_dir = Path(journal_dir)
        self.entries = {}
        self._load_entries()
    
    def _load_entries(self):
        if not self.journal_dir.exists():
            self.journal_dir.mkdir(parents=True, exist_ok=True)
            return
            
        for file in self.journal_dir.glob("*.txt"):
            try:
                content = file.read_text(encoding="utf-8").strip()
                if content:
                    self.entries[file.stem] = content
            except Exception:
                pass
    
    def get_rich_context(self, query: str, num_entries: int = 5) -> str:
        # Ricerca semplice per parole chiave
        results = []
        query_lower = query.lower()
        
        for date, content in self.entries.items():
            if any(word in content.lower() for word in query_lower.split()):
                results.append(f"=== {date} ===\n{content[:200]}...\n")
        
        return "\n".join(results[:num_entries])
    
    def get_keywords(self, text: str) -> List[str]:
        # Estrazione keyword semplice
        words = text.lower().split()
        # Rimuovi parole comuni
        stopwords = {'il', 'la', 'di', 'che', 'e', 'a', 'un', 'in', 'con', 'per', 'da'}
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        return list(set(keywords))[:10]

class MockEmotionsAnalyzer:
    """Mock per emotions analyzer"""
    def analyze_emotion(self, text: str) -> Dict[str, float]:
        # Analisi emozioni semplificata
        emotions = {
            "gioia": 0.0,
            "tristezza": 0.0,
            "rabbia": 0.0,
            "paura": 0.0,
            "sorpresa": 0.0
        }
        
        # Parole chiave emotive base
        if any(word in text.lower() for word in ['felice', 'contento', 'gioia', 'bene']):
            emotions["gioia"] = 0.7
        if any(word in text.lower() for word in ['triste', 'male', 'depresso', 'dolore']):
            emotions["tristezza"] = 0.7
        if any(word in text.lower() for word in ['arrabbiato', 'furioso', 'odio', 'rabbia']):
            emotions["rabbia"] = 0.7
        
        return emotions

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint per verificare che il server sia attivo"""
    memory = get_structured_memory()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "spacy_available": EnhancedStructuredMemory is not None,
        "memory_type": type(memory).__name__,
        "entries_count": len(memory.entries) if hasattr(memory, 'entries') else 0,
        "journal_dir": str(JOURNAL_DIR)
    })

@app.route('/context', methods=['POST'])
def get_context():
    """
    Endpoint principale per ottenere contesto semantico
    Richiesta: {"query": "come mi sento oggi", "days_back": 30}
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        days_back = data.get('days_back', 30)
        
        memory = get_structured_memory()
        emotions = get_emotions_analyzer()
        
        # Ottieni contesto semantico
        try:
            relevant_text = memory.get_rich_context(query, num_entries=5)
        except Exception as e:
            relevant_text = "Nessun contesto disponibile"
        
        # Analizza le emozioni della query
        try:
            query_emotions = emotions.analyze_emotion(query)
        except Exception as e:
            query_emotions = {}
        
        # Estrai keywords dalla query
        try:
            keywords = memory.get_keywords(query) if hasattr(memory, 'get_keywords') else []
        except Exception as e:
            keywords = []
        
        # Prepara risposta
        context = {
            "relevant_entries": relevant_text,
            "keywords": keywords,
            "emotions": query_emotions,
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(context)
        
    except Exception as e:
        print(f"[ERROR] ERRORE GENERALE /context: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze_text():
    """
    Analizza un testo e restituisce insights
    Richiesta: {"text": "Oggi mi sento..."}
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "Testo richiesto"}), 400
        
        memory = get_structured_memory()
        emotions = get_emotions_analyzer()
        
        # Analisi completa del testo
        result = {
            "emotions": emotions.analyze_emotion(text),
            "keywords": memory.get_keywords(text) if hasattr(memory, 'get_keywords') else [],
            "word_count": len(text.split()),
            "sentiment_score": 0.5,  # Placeholder
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/entries', methods=['GET'])
def get_entries():
    """
    Ottieni lista delle entries con metadati
    Query params: ?start_date=2024-01-01&end_date=2024-12-31
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        memory = get_structured_memory()
        
        entries = []
        for date, content in memory.entries.items():
            # Filtro per date se specificato
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
            
            entries.append({
                "date": date,
                "word_count": len(content.split()),
                "preview": content[:100] + "..." if len(content) > 100 else content,
                "has_emotions": os.path.exists(JOURNAL_DIR / f"{date}_emotions.json")
            })
        
        # Ordina per data decrescente
        entries.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            "entries": entries,
            "total": len(entries)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Statistiche generali del diario"""
    try:
        memory = get_structured_memory()
        
        total_entries = len(memory.entries)
        total_words = sum(len(content.split()) for content in memory.entries.values())
        
        # Calcola streak (giorni consecutivi)
        dates = sorted(memory.entries.keys(), reverse=True)
        streak = 0
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        for i, date in enumerate(dates):
            expected_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if date == expected_date:
                streak += 1
            else:
                break
        
        stats = {
            "total_entries": total_entries,
            "total_words": total_words,
            "average_words": total_words // max(total_entries, 1),
            "current_streak": streak,
            "first_entry": min(dates) if dates else None,
            "last_entry": max(dates) if dates else None
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Avvia server silenziosamente
    app.run(
        host='127.0.0.1',
        port=8080,
        debug=False
    )