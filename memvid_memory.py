#!/usr/bin/env python3
"""
Memvid-based Memory System for Reminor
Drop-in replacement for UnifiedMemory using Memvid V2
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    import memvid_sdk
    HAS_MEMVID = True
except ImportError:
    HAS_MEMVID = False
    print("ATTENZIONE: memvid-sdk non installato. pip install memvid-sdk")

# Modello embedding italiano ottimizzato
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_EMBEDDINGS = True
    # Modello italiano specifico con Matryoshka (può essere troncato a dimensioni minori)
    EMBEDDING_MODEL = "nickprock/sentence-bert-base-italian-uncased-sts-matryoshka"
except ImportError:
    HAS_EMBEDDINGS = False
    EMBEDDING_MODEL = None
    print("ATTENZIONE: sentence-transformers non installato per ricerca semantica")


class MemvidMemory:
    """
    Memory system basato su Memvid V2 + sentence-transformers.
    - Memvid: storage documenti + ricerca BM25
    - Sentence-transformers: ricerca semantica
    """

    def __init__(self, journal_dir: Path, memvid_file: Optional[Path] = None):
        """
        Inizializza il sistema di memoria Memvid + Embeddings.

        Args:
            journal_dir: Directory contenente i file .txt del diario
            memvid_file: Path al file .mv2 (default: journal_dir/../reminor_memory.mv2)
        """
        self.journal_dir = Path(journal_dir)

        if memvid_file:
            self.memvid_path = Path(memvid_file)
        else:
            self.memvid_path = self.journal_dir.parent / "reminor_memory.mv2"

        # Path per embeddings (stesso nome, estensione .npz)
        self.embeddings_path = self.memvid_path.with_suffix('.npz')

        self.mem = None
        self.entries: Dict[str, str] = {}

        # Embeddings
        self.embedding_model = None
        self.embeddings: Dict[str, Any] = {}  # date -> embedding vector

        if not HAS_MEMVID:
            print("ATTENZIONE: Memvid non disponibile")
            return

        # Inizializza modello embeddings
        self._initialize_embeddings()

        # Carica o crea il file Memvid
        self._initialize_memvid()

        # Carica entries per compatibilità
        self._load_entries()

        # Carica embeddings esistenti o rigenerali se mancano
        self._load_embeddings()
        self._ensure_embeddings()

        print(f"MemvidMemory inizializzato: {self.memvid_path}")
        if HAS_EMBEDDINGS and self.embedding_model:
            print(f"  Ricerca semantica: {len(self.embeddings)} embeddings")

    def _initialize_embeddings(self):
        """Inizializza il modello di embedding per ricerca semantica"""
        if not HAS_EMBEDDINGS:
            return

        try:
            print(f"Caricamento modello embeddings: {EMBEDDING_MODEL}...")
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            print(f"  Modello caricato: {self.embedding_model.get_sentence_embedding_dimension()}D")
        except Exception as e:
            print(f"  Errore caricamento modello: {e}")
            self.embedding_model = None

    def _load_embeddings(self):
        """Carica embeddings salvati da file .npz"""
        if not self.embeddings_path.exists():
            return

        try:
            data = np.load(self.embeddings_path, allow_pickle=True)
            if 'dates' in data and 'vectors' in data:
                dates = data['dates']
                vectors = data['vectors']
                self.embeddings = {d: v for d, v in zip(dates, vectors)}
        except Exception as e:
            print(f"Errore caricamento embeddings: {e}")

    def _save_embeddings(self):
        """Salva embeddings su file .npz"""
        if not self.embeddings:
            return

        try:
            dates = list(self.embeddings.keys())
            vectors = np.array(list(self.embeddings.values()))
            np.savez_compressed(self.embeddings_path, dates=dates, vectors=vectors)
        except Exception as e:
            print(f"Errore salvataggio embeddings: {e}")

    def _ensure_embeddings(self):
        """Genera embeddings mancanti per entries esistenti"""
        if not self.embedding_model or not self.entries:
            return

        missing = [date for date in self.entries if date not in self.embeddings]

        if not missing:
            return

        print(f"Generazione {len(missing)} embeddings mancanti...")
        for date in missing:
            content = self.entries[date]
            try:
                embedding = self.embedding_model.encode(content, convert_to_numpy=True)
                self.embeddings[date] = embedding
            except Exception as e:
                print(f"  Errore embedding per {date}: {e}")

        if missing:
            self._save_embeddings()
            print(f"  Embeddings aggiornati: {len(self.embeddings)} totali")

    def _initialize_memvid(self):
        """Inizializza il file Memvid (crea se non esiste, altrimenti apri)"""
        if self.memvid_path.exists():
            # Apri file esistente
            self.mem = memvid_sdk.use("basic", str(self.memvid_path))
            stats = self.mem.stats()
            print(f"Memvid caricato: {stats['frame_count']} frame, {stats['size_bytes']/1024:.1f}KB")
        else:
            # Crea nuovo file e indicizza i .txt esistenti
            print("Creazione nuovo file Memvid...")
            self._create_and_index()

    def _create_and_index(self):
        """Crea un nuovo file Memvid e indicizza tutti i file .txt"""
        self.mem = memvid_sdk.create(
            str(self.memvid_path),
            enable_lex=True,
            enable_vec=False  # Usiamo nostri embeddings separati
        )

        documents = []
        for file_path in sorted(self.journal_dir.glob("*.txt")):
            if file_path.name.startswith("."):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()

                if not content:
                    continue

                # Estrai data dal nome file
                date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', file_path.name)
                if date_match:
                    entry_date = datetime(
                        int(date_match.group(1)),
                        int(date_match.group(2)),
                        int(date_match.group(3))
                    )
                else:
                    entry_date = datetime.now()

                date_str = entry_date.strftime("%Y-%m-%d")

                doc = {
                    "title": f"Diario {date_str}",
                    "label": "diary",
                    "text": content,
                    "metadata": {"date": date_str, "full_text": content},  # Salva testo completo
                    "tags": ["diario"],
                    "timestamp": int(entry_date.timestamp())
                }
                documents.append(doc)

                # Carica anche in entries dict
                self.entries[date_str] = content

            except Exception as e:
                print(f"Errore file {file_path.name}: {e}")

        if documents:
            self.mem.put_many(documents)
            self.mem.seal()

            # Genera embeddings per ricerca semantica
            if self.embedding_model:
                print("Generazione embeddings semantici...")
                for doc in documents:
                    date_str = doc['metadata']['date']
                    text = doc['text']
                    try:
                        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
                        self.embeddings[date_str] = embedding
                    except Exception as e:
                        print(f"  Errore embedding per {date_str}: {e}")

                self._save_embeddings()
                print(f"  Salvati {len(self.embeddings)} embeddings")

        print(f"Indicizzati {len(documents)} documenti")

    def _load_entries(self):
        """Carica entries dict da Memvid (non più da file .txt)"""
        if not self.mem:
            return

        try:
            # Ottieni tutti i frame dalla timeline
            stats = self.mem.stats()
            frame_count = stats.get('frame_count', 0)

            timeline = self.mem.timeline(limit=frame_count)

            for item in timeline:
                uri = item.get('uri', '')
                if not uri:
                    continue

                # Ottieni frame completo per metadata
                frame = self.mem.frame(uri)
                metadata = frame.get('extra_metadata', {})

                # Estrai data e full_text dai metadata
                date_str = metadata.get('date', '').strip('"')
                full_text = metadata.get('full_text', '').strip('"')

                if date_str and full_text:
                    self.entries[date_str] = full_text

            print(f"  Caricate {len(self.entries)} entries da Memvid")

        except Exception as e:
            print(f"Errore caricamento entries da Memvid: {e}")
            # Fallback ai file .txt se Memvid fallisce
            self._load_entries_from_files()

    def _load_entries_from_files(self):
        """Fallback: carica entries dai file .txt"""
        for file_path in self.journal_dir.glob("*.txt"):
            if file_path.name.startswith(".") or "_emotions" in file_path.name:
                continue

            date_match = re.match(r'(\d{4}-\d{2}-\d{2})', file_path.name)
            if date_match:
                date_str = date_match.group(1)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.entries[date_str] = f.read().strip()
                except:
                    pass

    def get_rich_context(self, query: Optional[str] = None, num_entries: int = 10) -> str:
        """
        Ottiene contesto ricco per il chatbot.
        Compatibile con l'interfaccia UnifiedMemory.
        Usa ricerca ibrida: BM25 + fallback a ricerca diretta.

        Args:
            query: Query opzionale per ricerca semantica
            num_entries: Numero massimo di entries da restituire

        Returns:
            Stringa con contesto formattato
        """
        if not self.mem:
            return self._fallback_context(num_entries)

        context_parts = []

        if query:
            # Usa ricerca ibrida (BM25 + fallback diretto)
            similar_results = self.get_similar_entries(query, top_n=num_entries)

            for result in similar_results:
                date_str = result.get('date', 'N/A')
                content = result.get('content', '')
                score = result.get('score', 0)

                context_parts.append(f"[{date_str}] (rilevanza: {score:.1f})\n{content}")
        else:
            # Ultime entries per timeline
            timeline = self.mem.timeline(limit=num_entries, reverse=True)

            for entry in timeline:
                if hasattr(entry, 'title'):
                    title = entry.title
                    text = getattr(entry, 'text', '')[:500]
                else:
                    # Fallback per entries recenti dai file
                    dates = sorted(self.entries.keys(), reverse=True)[:num_entries]
                    for date in dates:
                        content = self.entries.get(date, '')[:500]
                        context_parts.append(f"[{date}]\n{content}")
                    break

        if not context_parts:
            return self._fallback_context(num_entries)

        return "\n\n---\n\n".join(context_parts)

    def _fallback_context(self, num_entries: int) -> str:
        """Fallback al contesto basato su file quando Memvid non disponibile"""
        dates = sorted(self.entries.keys(), reverse=True)[:num_entries]
        parts = []
        for date in dates:
            content = self.entries.get(date, '')[:500]
            if content:
                parts.append(f"[{date}]\n{content}")
        return "\n\n---\n\n".join(parts)

    def get_similar_entries(self, query: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Trova entries simili a una query.
        Usa ricerca ibrida: COMBINA semantica + BM25 + ricerca diretta.

        Args:
            query: Testo da cercare
            top_n: Numero di risultati

        Returns:
            Lista di dizionari con date, content, score
        """
        all_results = {}  # Usa dict per deduplicare per data

        # 1. Ricerca SEMANTICA (priorità massima per comprensione concettuale)
        if self.embedding_model and self.embeddings:
            semantic_results = self._semantic_search(query, top_n * 2)
            for r in semantic_results:
                date = r['date']
                # Score semantico moltiplicato per avere priorità
                r['score'] = r['score'] * 20  # Scala a valori comparabili
                if date not in all_results or r['score'] > all_results[date]['score']:
                    all_results[date] = r

        # 2. Ricerca diretta (match esatti di parole)
        direct_results = self._direct_text_search(query, top_n * 2)
        for r in direct_results:
            date = r['date']
            if date not in all_results or r['score'] > all_results[date]['score']:
                all_results[date] = r

        # 3. BM25 (aggiunge risultati se non già presenti)
        if self.mem:
            try:
                results = self.mem.find(query, k=top_n)
                hits = results.get('hits', [])

                for hit in hits:
                    title = hit.get('title', '')
                    date_match = re.search(r'\d{4}-\d{2}-\d{2}', title)
                    date_str = date_match.group(0) if date_match else 'unknown'

                    # Aggiungi solo se non già trovato
                    if date_str not in all_results:
                        all_results[date_str] = {
                            'date': date_str,
                            'content': hit.get('snippet', ''),
                            'score': hit.get('score', 0),
                            'title': title
                        }
            except Exception as e:
                print(f"BM25 search error: {e}")

        # Ordina per score decrescente e restituisci top_n
        similar = sorted(all_results.values(), key=lambda x: -x['score'])
        return similar[:top_n]

    def _semantic_search(self, query: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Ricerca semantica usando embeddings.
        Trova entries concettualmente simili alla query.
        """
        if not self.embedding_model or not self.embeddings:
            return []

        try:
            # Genera embedding della query
            query_embedding = self.embedding_model.encode(query, convert_to_numpy=True)

            # Calcola similarità coseno con tutti gli embeddings
            results = []
            for date, doc_embedding in self.embeddings.items():
                # Similarità coseno
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )

                # Aggiungi solo se similarità significativa (> 0.2)
                if similarity > 0.2:
                    content = self.entries.get(date, '')[:500]
                    results.append({
                        'date': date,
                        'content': content + "..." if len(self.entries.get(date, '')) > 500 else content,
                        'score': float(similarity),
                        'title': f"Diario {date}"
                    })

            # Ordina per similarità decrescente
            results.sort(key=lambda x: -x['score'])
            return results[:top_n]

        except Exception as e:
            print(f"Errore ricerca semantica: {e}")
            return []

    def get_emotional_timeline(self) -> List[Dict[str, Any]]:
        """
        Ottiene la timeline emozionale.
        Placeholder - restituisce lista vuota se non implementato.
        """
        # TODO: Implementare con enrichment Memvid
        return []

    def get_behavioral_patterns(self) -> Dict[str, Any]:
        """
        Ottiene pattern comportamentali.
        Placeholder - restituisce dict vuoto se non implementato.
        """
        # TODO: Implementare con memories() di Memvid
        return {}

    def add_entry(self, date: str, content: str) -> bool:
        """
        Aggiunge una nuova voce al diario.

        Args:
            date: Data in formato YYYY-MM-DD
            content: Contenuto della voce

        Returns:
            True se aggiunto con successo
        """
        if not self.mem or not content.strip():
            return False

        try:
            # Aggiungi a Memvid con full_text nei metadata
            self.mem.put(
                title=f"Diario {date}",
                label="diary",
                text=content,
                metadata={"date": date, "full_text": content},
                tags=["diario"]
            )

            # Aggiorna entries dict
            self.entries[date] = content

            # Genera e salva embedding per ricerca semantica
            if self.embedding_model:
                try:
                    embedding = self.embedding_model.encode(content, convert_to_numpy=True)
                    self.embeddings[date] = embedding
                    self._save_embeddings()
                except Exception as e:
                    print(f"Errore generazione embedding: {e}")

            return True
        except Exception as e:
            print(f"Errore aggiunta entry: {e}")
            return False

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Ricerca full-text nel diario.
        Usa ricerca ibrida: BM25 + fallback a ricerca diretta per parole corte.

        Args:
            query: Testo da cercare
            limit: Numero massimo di risultati

        Returns:
            Lista di risultati con snippet e score
        """
        # Prima prova BM25
        results = self.get_similar_entries(query, top_n=limit)

        # Se BM25 non trova nulla, usa ricerca diretta nel testo
        if not results:
            results = self._direct_text_search(query, limit)

        return results

    def _direct_text_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Ricerca diretta nel testo delle entries.
        Estrae parole chiave dalla query e cerca ciascuna.
        Supporta anche ricerca per mese (ottobre, settembre, etc.)
        """
        query_lower = query.lower()
        results = []

        # Mappa mesi italiani a numeri
        mesi_map = {
            'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
            'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
            'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
        }

        # Stopwords italiane da ignorare
        stopwords = {'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una',
                     'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
                     'che', 'chi', 'cosa', 'come', 'dove', 'quando', 'perché',
                     'e', 'o', 'ma', 'se', 'non', 'più', 'anche', 'solo',
                     'mi', 'ti', 'ci', 'vi', 'si', 'me', 'te', 'lui', 'lei',
                     'noi', 'voi', 'loro', 'mio', 'tuo', 'suo', 'nostro',
                     'questo', 'quello', 'quale', 'quanto', 'tutto', 'ogni',
                     'conosci', 'sai', 'dimmi', 'parlami', 'raccontami', 'dici'}

        # Estrai parole chiave significative dalla query
        words = re.findall(r'\b[a-zA-ZàèéìòùÀÈÉÌÒÙ]+\b', query_lower)
        keywords = [w for w in words if w not in stopwords and len(w) >= 3]

        # Controlla se c'è un mese nella query
        month_filter = None
        for mese, num in mesi_map.items():
            if mese in query_lower:
                month_filter = f"-{num}-"
                keywords.append(mese)  # Aggiungi anche il mese come keyword
                break

        for date, content in self.entries.items():
            matched = False
            score = 0
            best_idx = 0

            # Se c'è filtro per mese, controlla la data
            if month_filter and month_filter in date:
                matched = True
                score = 15.0

            # Cerca ogni keyword nel contenuto
            content_lower = content.lower()
            for keyword in keywords:
                if keyword in content_lower:
                    count = content_lower.count(keyword)
                    # Parole più lunghe = più specifiche = score più alto
                    word_score = count * (5.0 + len(keyword))
                    score += word_score
                    matched = True
                    # Trova la posizione per lo snippet
                    idx = content_lower.find(keyword)
                    if idx > best_idx:
                        best_idx = idx

            if matched:
                # Estrai snippet intorno al match migliore
                start = max(0, best_idx - 100)
                end = min(len(content), best_idx + 300)
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."

                results.append({
                    'date': date,
                    'content': snippet if snippet.strip() else content[:300] + "...",
                    'score': score,
                    'title': f"Diario {date}"
                })

        # Ordina per score decrescente
        results.sort(key=lambda x: -x['score'])
        return results[:limit]

    def stats(self) -> Dict[str, Any]:
        """Restituisce statistiche del sistema di memoria"""
        if not self.mem:
            return {"error": "Memvid non inizializzato"}

        return self.mem.stats()

    # ==================== GESTIONE EMOZIONI ====================

    def save_emotions(self, date: str, emotions: Dict[str, float],
                      daily_insights: Optional[Dict] = None,
                      profile_updates: Optional[Dict] = None) -> bool:
        """
        Salva le emozioni per una data specifica in Memvid.

        Args:
            date: Data in formato YYYY-MM-DD
            emotions: Dizionario emozione -> score (0-1)
            daily_insights: Insights giornalieri opzionali
            profile_updates: Aggiornamenti profilo opzionali

        Returns:
            True se salvato con successo
        """
        if not self.mem or not emotions:
            return False

        try:
            import json

            # Prepara metadata con emozioni
            metadata = {
                'date': date,
                'type': 'emotions',
                'emotions': json.dumps(emotions)
            }

            if daily_insights:
                metadata['daily_insights'] = json.dumps(daily_insights)
            if profile_updates:
                metadata['profile_updates'] = json.dumps(profile_updates)

            # Crea testo leggibile per la ricerca
            emotion_text = ", ".join([f"{k}: {v:.1f}" for k, v in emotions.items() if v > 0])

            # Inserisci come frame con label 'emotions'
            self.mem.put(
                title=f"Emozioni {date}",
                label="emotions",
                text=f"Emozioni del {date}: {emotion_text}",
                metadata=metadata,
                tags=["emozioni", date]
            )

            return True

        except Exception as e:
            print(f"Errore salvataggio emozioni: {e}")
            return False

    def get_emotions(self, date: str) -> Optional[Dict[str, float]]:
        """
        Recupera le emozioni per una data specifica.

        Args:
            date: Data in formato YYYY-MM-DD

        Returns:
            Dizionario emozioni o None se non trovato
        """
        if not self.mem:
            return None

        try:
            import json

            # Cerca frame emozioni per questa data
            results = self.mem.find(f"Emozioni {date}", k=5)
            hits = results.get('hits', [])

            for hit in hits:
                # Verifica che sia il frame giusto
                if hit.get('title') == f"Emozioni {date}":
                    uri = hit.get('uri', '')
                    if uri:
                        frame = self.mem.frame(uri)
                        metadata = frame.get('extra_metadata', {})
                        emotions_str = metadata.get('emotions', '')
                        if emotions_str:
                            # Memvid aggiunge virgolette extra, decodifica due volte se necessario
                            try:
                                # Prima decodifica (rimuove escape delle virgolette)
                                decoded = json.loads(emotions_str)
                                # Se è ancora una stringa, decodifica ancora
                                if isinstance(decoded, str):
                                    decoded = json.loads(decoded)
                                return decoded
                            except:
                                # Fallback: prova a pulire manualmente
                                clean = emotions_str.strip('"').replace('\\"', '"')
                                return json.loads(clean)

            return None

        except Exception as e:
            print(f"Errore recupero emozioni per {date}: {e}")
            return None

    def get_emotions_for_week(self, dates: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Recupera le emozioni per una lista di date (per la matrice settimanale).

        Args:
            dates: Lista di date in formato YYYY-MM-DD

        Returns:
            Dizionario {date: {emozione: score}}
        """
        result = {}
        for date in dates:
            emotions = self.get_emotions(date)
            if emotions:
                result[date] = emotions
            else:
                result[date] = {}
        return result

    def get_full_analysis(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Recupera l'analisi completa (emozioni + insights + profile) per una data.

        Args:
            date: Data in formato YYYY-MM-DD

        Returns:
            Dizionario con emotions, daily_insights, profile_updates
        """
        if not self.mem:
            return None

        def decode_json_field(value: str):
            """Decodifica un campo JSON che potrebbe essere doppiamente codificato"""
            if not value:
                return None
            try:
                decoded = json.loads(value)
                if isinstance(decoded, str):
                    decoded = json.loads(decoded)
                return decoded
            except:
                try:
                    clean = value.strip('"').replace('\\"', '"')
                    return json.loads(clean)
                except:
                    return None

        try:
            import json

            results = self.mem.find(f"Emozioni {date}", k=5)
            hits = results.get('hits', [])

            for hit in hits:
                if hit.get('title') == f"Emozioni {date}":
                    uri = hit.get('uri', '')
                    if uri:
                        frame = self.mem.frame(uri)
                        metadata = frame.get('extra_metadata', {})

                        result = {}

                        # Parse emotions
                        emotions = decode_json_field(metadata.get('emotions', ''))
                        if emotions:
                            result['emotions'] = emotions

                        # Parse daily_insights
                        insights = decode_json_field(metadata.get('daily_insights', ''))
                        if insights:
                            result['daily_insights'] = insights

                        # Parse profile_updates
                        profile = decode_json_field(metadata.get('profile_updates', ''))
                        if profile:
                            result['profile_updates'] = profile

                        return result if result else None

            return None

        except Exception as e:
            print(f"Errore recupero analisi per {date}: {e}")
            return None

    def close(self):
        """Chiude la connessione al file Memvid"""
        if self.mem:
            self.mem.close()
            self.mem = None


# Alias per compatibilità
UnifiedMemory = MemvidMemory


def create_memvid_memory(journal_dir: Path) -> MemvidMemory:
    """Factory function per creare istanza MemvidMemory"""
    return MemvidMemory(journal_dir)
