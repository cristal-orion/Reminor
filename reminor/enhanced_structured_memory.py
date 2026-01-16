#!/usr/bin/env python3
"""
Enhanced structured memory with emotion and temporal analysis.
Builds upon StructuredMemory with extra semantic features.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple

import spacy
from spacy.pipeline import EntityRuler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from .structured_memory import StructuredMemory
except ImportError:
    # Fallback per quando viene eseguito come script standalone
    from structured_memory import StructuredMemory


class EnhancedStructuredMemory(StructuredMemory):
    """StructuredMemory with richer NLP analysis and caching."""

    def __init__(self, journal_dir: Path):
        super().__init__(journal_dir)
        self.entries: Dict[str, str] = {}
        self._load_entries()

        # Carica direttamente modello con word vectors
        self.nlp = spacy.load("it_core_news_md")
        print("spaCy it_core_news_md caricato - semantic similarity avanzata attiva!")

        # Entity index for fast lookup
        self.entity_index = {}  # {entity_normalized: {date: count}}

        # Stopwords italiane complete - Lista professionale per analisi semantica
        italian_stopwords = [
            # Articoli
            'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'dei', 'degli', 'delle',
            # Preposizioni semplici e articolate
            'a', 'ad', 'al', 'alla', 'allo', 'ai', 'agli', 'alle', 'da', 'dal', 'dalla', 'dallo', 
            'dai', 'dagli', 'dalle', 'di', 'del', 'della', 'dello', 'dei', 'degli', 'delle', 
            'in', 'nel', 'nella', 'nello', 'nei', 'negli', 'nelle', 'con', 'col', 'coi', 'su', 
            'sul', 'sulla', 'sullo', 'sui', 'sugli', 'sulle', 'per', 'tra', 'fra',
            # Congiunzioni
            'e', 'ed', 'o', 'od', 'ma', 'però', 'anzi', 'oppure', 'ovvero', 'ossia', 'cioè',
            'che', 'come', 'quando', 'mentre', 'se', 'perché', 'poiché', 'siccome', 'quindi',
            'dunque', 'pertanto', 'tuttavia', 'nondimeno', 'pure', 'eppure', 'neanche', 'nemmeno',
            # Pronomi personali
            'io', 'tu', 'egli', 'lui', 'ella', 'lei', 'esso', 'essa', 'noi', 'voi', 'essi', 'esse',
            'loro', 'me', 'te', 'se', 'ci', 'vi', 'si', 'ne', 'lo', 'la', 'li', 'le', 'gli',
            'mi', 'ti', 'ci', 'vi', 'si', 'mio', 'mia', 'miei', 'mie', 'tuo', 'tua', 'tuoi', 'tue',
            'suo', 'sua', 'suoi', 'sue', 'nostro', 'nostra', 'nostri', 'nostre', 'vostro', 'vostra',
            'vostri', 'vostre', 'proprio', 'propria', 'propri', 'proprie',
            # Aggettivi e pronomi dimostrativi
            'questo', 'questa', 'questi', 'queste', 'quello', 'quella', 'quelli', 'quelle',
            'stesso', 'stessa', 'stessi', 'stesse', 'tale', 'tali', 'altro', 'altra', 'altri',
            'altre', 'altrui', 'medesimo', 'medesima', 'medesimi', 'medesime',
            # Pronomi relativi e interrogativi
            'chi', 'che', 'cui', 'quale', 'quali', 'quanto', 'quanta', 'quanti', 'quante',
            'dove', 'quando', 'come', 'perché', 'cosa', 'cosaccia',
            # Avverbi comuni
            'non', 'no', 'sì', 'già', 'ancora', 'sempre', 'mai', 'più', 'meno', 'molto', 'poco',
            'tanto', 'quanto', 'troppo', 'parecchio', 'assai', 'abbastanza', 'piuttosto', 'inoltre',
            'infatti', 'invece', 'pure', 'anche', 'solo', 'soltanto', 'solamente', 'appena',
            'proprio', 'davvero', 'veramente', 'certamente', 'sicuramente', 'forse', 'magari',
            'qui', 'qua', 'lì', 'là', 'dove', 'ovunque', 'altrove', 'sopra', 'sotto', 'dentro',
            'fuori', 'davanti', 'dietro', 'presso', 'vicino', 'lontano', 'intorno', 'attorno',
            'oggi', 'ieri', 'domani', 'ora', 'adesso', 'allora', 'prima', 'dopo', 'poi', 'subito',
            'presto', 'tardi', 'spesso', 'talvolta', 'qualche', 'volta', 'bene', 'male', 'meglio',
            'peggio', 'così', 'come', 'quanto', 'alquanto', 'abbastanza', 'parecchio',
            # Verbi ausiliari e modali coniugati
            'sono', 'sei', 'è', 'siamo', 'siete', 'era', 'ero', 'eri', 'eravamo', 'eravate', 'erano',
            'sarò', 'sarai', 'sarà', 'saremo', 'sarete', 'saranno', 'sia', 'siano', 'fosse', 'fossi',
            'fossero', 'essere', 'stato', 'stata', 'stati', 'state',
            'ho', 'hai', 'ha', 'abbiamo', 'avete', 'hanno', 'avevo', 'avevi', 'aveva', 'avevamo',
            'avevate', 'avevano', 'avrò', 'avrai', 'avrà', 'avremo', 'avrete', 'avranno', 'abbia',
            'abbiano', 'avessi', 'avesse', 'avessero', 'avere', 'avuto', 'avuta', 'avuti', 'avute',
            'posso', 'puoi', 'può', 'possiamo', 'potete', 'possono', 'potevo', 'potevi', 'poteva',
            'potevamo', 'potevate', 'potevano', 'potrò', 'potrai', 'potrà', 'potremo', 'potrete',
            'potranno', 'possa', 'possano', 'potessi', 'potesse', 'potessero', 'potere', 'potuto',
            'devo', 'devi', 'deve', 'dobbiamo', 'dovete', 'devono', 'dovevo', 'dovevi', 'doveva',
            'dovevamo', 'dovevate', 'dovevano', 'dovrò', 'dovrai', 'dovrà', 'dovremo', 'dovrete',
            'dovranno', 'debba', 'debbano', 'dovessi', 'dovesse', 'dovessero', 'dovere', 'dovuto',
            'voglio', 'vuoi', 'vuole', 'vogliamo', 'volete', 'vogliono', 'volevo', 'volevi', 'voleva',
            'volevamo', 'volevate', 'volevano', 'vorrò', 'vorrai', 'vorrà', 'vorremo', 'vorrete',
            'vorranno', 'voglia', 'vogliano', 'volessi', 'volesse', 'volessero', 'volere', 'voluto',
            # Verbi comuni coniugati
            'faccio', 'fai', 'fa', 'facciamo', 'fate', 'fanno', 'facevo', 'facevi', 'faceva',
            'facevamo', 'facevate', 'facevano', 'farò', 'farai', 'farà', 'faremo', 'farete',
            'faranno', 'faccia', 'facciano', 'facessi', 'facesse', 'facessero', 'fare', 'fatto',
            'vado', 'vai', 'va', 'andiamo', 'andate', 'vanno', 'andavo', 'andavi', 'andava',
            'andavamo', 'andavate', 'andavano', 'andrò', 'andrai', 'andrà', 'andremo', 'andrete',
            'andranno', 'vada', 'vadano', 'andassi', 'andasse', 'andassero', 'andare', 'andato',
            'do', 'dai', 'dà', 'diamo', 'date', 'danno', 'davo', 'davi', 'dava', 'davamo',
            'davate', 'davano', 'darò', 'darai', 'darà', 'daremo', 'darete', 'daranno',
            'dia', 'diano', 'dessi', 'desse', 'dessero', 'dare', 'dato',
            'sto', 'stai', 'sta', 'stiamo', 'state', 'stanno', 'stavo', 'stavi', 'stava',
            'stavamo', 'stavate', 'stavano', 'starò', 'starai', 'starà', 'staremo', 'starete',
            'staranno', 'stia', 'stiano', 'stessi', 'stesse', 'stessero', 'stare', 'stato',
            # Interiezioni e esclamazioni
            'oh', 'ah', 'eh', 'boh', 'mah', 'beh', 'ecco', 'allora', 'dunque',
            # Numeri
            'zero', 'uno', 'due', 'tre', 'quattro', 'cinque', 'sei', 'sette', 'otto', 'nove', 'dieci',
            'primo', 'prima', 'secondo', 'seconda', 'terzo', 'terza', 'ultimo', 'ultima',
            # Espressioni di tempo e quantità
            'oggi', 'ieri', 'domani', 'stamattina', 'stasera', 'stanotte', 'sempre', 'mai', 'spesso',
            'raramente', 'talvolta', 'ogni', 'tutto', 'tutta', 'tutti', 'tutte', 'niente', 'nulla',
            'qualcosa', 'qualcuno', 'qualcuna', 'chiunque', 'ovunque', 'dovunque', 'comunque',
            # Particelle e congiunzioni
            'infatti', 'inoltre', 'perciò', 'dunque', 'quindi', 'pertanto', 'tuttavia', 'però',
            'nondimeno', 'anzi', 'altrimenti', 'oppure', 'ovvero', 'ossia', 'cioè', 'vale',
            'dire', 'ovviamente', 'certamente', 'sicuramente', 'probabilmente', 'forse',
            # Altre parole comuni
            'casa', 'tempo', 'anno', 'anni', 'giorno', 'giorni', 'volta', 'volte', 'modo', 'modi',
            'caso', 'casi', 'parte', 'parti', 'momento', 'momenti', 'punto', 'punti', 'fine',
            'inizio', 'mezzo', 'centro', 'posto', 'posti', 'luogo', 'luoghi', 'gente', 'persona',
            'persone', 'uomo', 'uomini', 'donna', 'donne', 'bambino', 'bambini', 'bambina', 'bambine',
            'ragazzo', 'ragazzi', 'ragazza', 'ragazze', 'signore', 'signora', 'signori', 'signore'
        ]
        self.vectorizer = TfidfVectorizer(
            stop_words=italian_stopwords,
            max_features=1000,  # Limita features per performance
            ngram_range=(1, 2)  # Unigrams + bigrams per migliore context
        )
        self._tfidf_matrix = None  # Lazy

        self.analysis_cache: Dict[str, Dict] = {}
        self.cache_path = Path(journal_dir) / "enhanced_memory_cache.json"
        self.load_enhanced_cache()

        self._setup_custom_patterns()
        self._build_entity_index()

    # --- Setup methods -------------------------------------------------
    
    def _build_entity_index(self) -> None:
        """Costruisce indice delle entità per ricerca veloce"""
        self.entity_index = {}
        
        # Controlla se esiste cache dell'indice
        cache_key = "entity_index_v4"
        if cache_key in self.analysis_cache:
            self.entity_index = self.analysis_cache[cache_key]
            print(f"Entity index caricato da cache: {len(self.entity_index)} entità")
            return
        
        for date, entry in self.entries.items():
            # Processa il testo con spaCy per estrarre entità
            doc = self.nlp(entry)
            
            # Estrai nomi propri (entità PERSON e nomi in maiuscolo)
            entities = set()
            
            # 1. Entità riconosciute da spaCy
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "GPE", "ORG"]:  # Persone, luoghi, organizzazioni
                    entities.add(ent.text.lower())
            
            # 2. Parole che iniziano con maiuscola (probabili nomi propri)
            for token in doc:
                if (token.text[0].isupper() and 
                    not token.is_stop and 
                    not token.is_punct and 
                    len(token.text) > 2 and
                    token.pos_ in ["NOUN", "PROPN"]):
                    entities.add(token.text.lower())
            
            # 3. Parole comuni che potrebbero essere entità
            common_entities = ["pizza", "mare", "moto", "cena", "pranzo", "lavoro", "casa", "sardegna"]
            for word in common_entities:
                if word in entry.lower():
                    entities.add(word)
            
            # 4. Forza l'indicizzazione di tutti i nomi propri comuni
            import re
            name_patterns = re.findall(r'\b[A-Z][a-z]{2,}\b', entry)
            for name in name_patterns:
                if name.lower() not in ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                                       "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]:
                    entities.add(name.lower())
            
            # 5. Forza nomi specifici che sappiamo esistere
            known_names = ["gerardo", "walter", "rossana", "altea", "maria", "eugenio", "eleonora", "raffaele"]
            for known_name in known_names:
                if known_name in entry.lower():
                    entities.add(known_name)
            
            # Aggiungi all'indice
            for entity in entities:
                if entity not in self.entity_index:
                    self.entity_index[entity] = {}
                self.entity_index[entity][date] = self.entity_index[entity].get(date, 0) + 1
        
        # Salva in cache
        self.analysis_cache[cache_key] = self.entity_index
        self.save_enhanced_cache()
    def _setup_custom_patterns(self) -> None:
        """Setup pattern personalizzati ottimizzati per word vectors"""
        try:
            if "emotion_ruler" in self.nlp.pipe_names:
                return
                
            # Pattern espansi per sfruttare word vectors
            patterns = [
                # Emozioni positive
                {"label": "EMOTION", "pattern": "felice"},
                {"label": "EMOTION", "pattern": "contento"},
                {"label": "EMOTION", "pattern": "gioioso"},
                {"label": "EMOTION", "pattern": "soddisfatto"},
                {"label": "EMOTION", "pattern": "sereno"},
                {"label": "EMOTION", "pattern": "grato"},
                {"label": "EMOTION", "pattern": "motivato"},
                {"label": "EMOTION", "pattern": "entusiasta"},
                
                # Emozioni negative  
                {"label": "EMOTION", "pattern": "triste"},
                {"label": "EMOTION", "pattern": "depresso"},
                {"label": "EMOTION", "pattern": "arrabbiato"},
                {"label": "EMOTION", "pattern": "ansioso"},
                {"label": "EMOTION", "pattern": "stressato"},
                {"label": "EMOTION", "pattern": "preoccupato"},
                {"label": "EMOTION", "pattern": "nervoso"},
                {"label": "EMOTION", "pattern": "sconsolato"},
                
                # Tempo
                {"label": "TIME", "pattern": "oggi"},
                {"label": "TIME", "pattern": "ieri"},
                {"label": "TIME", "pattern": "domani"},
                {"label": "TIME", "pattern": "stamattina"},
                {"label": "TIME", "pattern": "stasera"},
                {"label": "TIME", "pattern": "stanotte"}
            ]
            
            ruler = self.nlp.add_pipe("entity_ruler", name="emotion_ruler", before="ner")
            ruler.add_patterns(patterns)
            
            print(f"{len(patterns)} pattern personalizzati configurati per word vectors")
            
        except Exception as e:
            print(f"Pattern non configurati: {e}")

    def _load_entries(self) -> None:
        for file in self.journal_dir.glob("*.txt"):
            try:
                content = file.read_text(encoding="utf-8").strip()
                # Only load non-empty entries to avoid empty vector warnings
                if content:
                    self.entries[file.stem] = content
            except Exception:
                pass

    def _ensure_tfidf(self) -> None:
        if self._tfidf_matrix is None and self.entries:
            corpus = list(self.entries.values())
            self._tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def _ensure_spacy_docs(self) -> None:
        """Cache spaCy docs per evitare riprocessing"""
        if not hasattr(self, "_spacy_docs") or len(self._spacy_docs) != len(self.entries):
            self._spacy_docs = {}
            for date, text in self.entries.items():
                if text.strip():  # Additional check for non-empty text
                    doc = self.nlp(text)
                    # Only store docs that have meaningful vectors
                    if doc.has_vector and doc.vector_norm > 0:
                        self._spacy_docs[date] = doc

    # --- Public API ----------------------------------------------------
    def add_entry(self, date: str, text: str) -> None:
        # Only add non-empty entries
        if text.strip():
            super().add_entry(date, text)
            self.entries[date] = text
            self._tfidf_matrix = None
            # Reset spacy docs cache to include new entry
            if hasattr(self, '_spacy_docs'):
                delattr(self, '_spacy_docs')

    def get_all_entities(self) -> List[str]:
        return super().get_all_entities()

    def get_dates_for_entity(self, entity: str) -> List[str]:
        return super().get_dates_for_entity(entity)

    def get_rich_context(self, query: str = "", num_entries: int = 10) -> str:
        """Generate intelligent context based on query similarity or recent entries"""
        if query.strip():
            # Context intelligente basato su similarity
            similar = self.get_similar_entries(query, top_n=5)
            recent = sorted(self.entries.items(), reverse=True)[:5]

            context = f"CONTESTO INTELLIGENTE per '{query}':\n\n"

            if similar:
                context += "VOCI SIMILI (per rilevanza):\n"
                for date, score in similar:
                    snippet = self.entries[date][:200] + "..." if len(self.entries[date]) > 200 else self.entries[date]
                    context += f"• {date} (rilevanza: {score:.0%}): {snippet}\n\n"

            context += "VOCI RECENTI:\n"
            for date, text in recent:
                snippet = text[:150] + "..." if len(text) > 150 else text
                context += f"• {date}: {snippet}\n\n"

            return context
        else:
            # Comportamento default per query vuota
            recent = sorted(self.entries.items(), reverse=True)[:num_entries]
            context = "CONTESTO RECENTE:\n\n"
            for date, text in recent:
                context += f"=== {date} ===\n{text}\n\n"
            return context

    def get_similar_entries(self, text: str, top_n: int = 3) -> List[Tuple[str, float]]:
        # 1. Prima cerca nell'indice delle entità
        entity_matches = []
        query_words = text.lower().split()
        
        for word in query_words:
            clean_word = word.strip('.,!?():')  # Rimuovi punteggiatura
            if len(clean_word) >= 3 and clean_word in self.entity_index:
                for date, count in self.entity_index[clean_word].items():
                    entity_matches.append((date, count, clean_word))
        
        # Se trova entità, calcola punteggi
        if entity_matches:
            # Raggruppa per data e somma i punteggi
            date_scores = {}
            for date, count, entity in entity_matches:
                if date not in date_scores:
                    date_scores[date] = 0
                date_scores[date] += count
            
            # Converti in lista e ordina
            entity_results = [(date, score) for date, score in date_scores.items()]
            entity_results.sort(key=lambda x: x[1], reverse=True)
            return entity_results[:top_n]
        
        # 2. Fallback a ricerca keyword tradizionale
        keyword_matches = []
        
        for date, entry in self.entries.items():
            entry_lower = entry.lower()
            # Cerca parole esatte (almeno 3 caratteri per evitare match su articoli)
            valid_words = [word for word in query_words if len(word) >= 3]
            matches = sum(1 for word in valid_words if word in entry_lower)
            
            if matches > 0:
                # Punteggio basato sul numero di parole trovate
                keyword_score = matches / len(valid_words) if valid_words else 0
                keyword_matches.append((date, keyword_score))
        
        # Ordina per punteggio keyword
        keyword_matches.sort(key=lambda x: x[1], reverse=True)
        
        # 3. Se abbiamo buone corrispondenze per keyword, usale (soglia ridotta per nomi)
        if keyword_matches and keyword_matches[0][1] >= 0.25:  # Ridotto da 30% a 25%
            return keyword_matches[:top_n]
        
        # 3. Altrimenti usa la ricerca semantica tradizionale
        self._ensure_tfidf()
        self._ensure_spacy_docs()
        if self._tfidf_matrix is None or self._tfidf_matrix.shape[0] == 0:
            return []

        query_vec = self.vectorizer.transform([text])
        tfidf_scores = cosine_similarity(query_vec, self._tfidf_matrix)[0]

        # Similarity semantica con word vectors
        doc_query = self.nlp(text)
        
        # Only calculate similarity for documents that have vectors
        valid_dates = list(self._spacy_docs.keys())
        if not valid_dates:
            # Fallback to TF-IDF only if no spaCy docs are available
            ranking = sorted(zip(self.entries.keys(), tfidf_scores), key=lambda x: x[1], reverse=True)
            return ranking[:top_n]
        
        # Calculate spaCy scores only for documents with vectors
        spa_scores_dict = {}
        for date in valid_dates:
            if date in self._spacy_docs:
                score = doc_query.similarity(self._spacy_docs[date])
                spa_scores_dict[date] = score

        # Combine scores only for entries that exist in both systems
        scores = []
        entry_dates = list(self.entries.keys())
        for i, date in enumerate(entry_dates):
            tfidf_score = tfidf_scores[i]
            if date in spa_scores_dict:
                spa_score = spa_scores_dict[date]
                combined_score = 0.3 * tfidf_score + 0.7 * float(spa_score)
            else:
                # Use only TF-IDF score for entries without vectors
                combined_score = tfidf_score
            scores.append(combined_score)
        
        ranking = sorted(zip(self.entries.keys(), scores), key=lambda x: x[1], reverse=True)
        result = ranking[:top_n]

        key = hashlib.md5(text.encode("utf-8")).hexdigest()
        self.analysis_cache[key] = {"similar": result}
        self.save_enhanced_cache()
        return result

    def get_entity_cooccurrence(self) -> Dict[Tuple[str, str], int]:
        key = "cooccurrence"
        if key in self.analysis_cache:
            return self.analysis_cache[key]

        counts: Dict[Tuple[str, str], int] = {}
        for text in self.entries.values():
            doc = self.nlp(text)
            entities = list({ent.text for ent in doc.ents if ent.label_ != "TIME"})
            for i, e1 in enumerate(entities):
                for e2 in entities[i + 1 :]:
                    pair = tuple(sorted((e1, e2)))
                    counts[pair] = counts.get(pair, 0) + 1
        self.analysis_cache[key] = counts
        self.save_enhanced_cache()
        return counts

    def get_emotional_timeline(self) -> Dict[str, Dict[str, int]]:
        key = "emotional_timeline"
        if key in self.analysis_cache:
            return self.analysis_cache[key]
        timeline: Dict[str, Dict[str, int]] = {}
        for date, text in self.entries.items():
            doc = self.nlp(text)
            emo_counts: Dict[str, int] = {}
            for ent in doc.ents:
                if ent.label_ == "EMOTION":
                    emo_counts[ent.text] = emo_counts.get(ent.text, 0) + 1
            if emo_counts:
                timeline[date] = emo_counts
        self.analysis_cache[key] = timeline
        self.save_enhanced_cache()
        return timeline

    def get_behavioral_patterns(self) -> Dict[str, int]:
        key = "behavioral_patterns"
        if key in self.analysis_cache:
            return self.analysis_cache[key]
        patterns: Dict[str, int] = {}
        for text in self.entries.values():
            doc = self.nlp(text)
            for token in doc:
                if token.pos_ == "VERB":
                    lemma = token.lemma_
                    patterns[lemma] = patterns.get(lemma, 0) + 1
        self.analysis_cache[key] = patterns
        self.save_enhanced_cache()
        return patterns

    def save_enhanced_cache(self) -> None:
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.analysis_cache, f)
        except Exception:
            pass

    def load_enhanced_cache(self) -> None:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self.analysis_cache = json.load(f)
            except Exception:
                self.analysis_cache = {}
        else:
            self.analysis_cache = {}
