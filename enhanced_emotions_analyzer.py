#!/usr/bin/env python3
"""
Enhanced EmotionsAnalyzer per MySoul Extreme Journal
Combina analisi emozioni + profilo psicologico cumulativo
"""

import os
import datetime
import requests
import json
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import hashlib

class EnhancedEmotionsAnalyzer:
    def __init__(self, journal_dir: Path):
        self.journal_dir = journal_dir
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            print("[WARNING] GROQ_API_KEY non trovata per EnhancedEmotionsAnalyzer")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"  # Updated to better model

        # Lista emozioni standard (per retrocompatibilità)
        self.emotions_list = [
            "felice", "triste", "arrabbiato", "ansioso",
            "sereno", "stressato", "grato", "motivato"
        ]

        # Cache version - increment when prompt changes to invalidate old cache
        self.cache_version = "2.0"

        # Cache per evitare rianalisi
        self._analysis_cache = {}
        self.load_cache()
        
        # Profilo psicologico
        self.profile_file = self.journal_dir / "personality_profile.json"
        self.profile_data = self.load_profile()

    def _get_cache_path(self):
        return Path(self.journal_dir) / "enhanced_emotions_cache.json"

    def load_cache(self):
        cache_path = self._get_cache_path()
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    # Check cache version - invalidate if outdated
                    if cache_data.get("_version") != self.cache_version:
                        print(f"Cache versione {cache_data.get('_version')} obsoleta, rigenerazione con v{self.cache_version}")
                        self._analysis_cache = {}
                    else:
                        self._analysis_cache = cache_data.get("entries", {})
            except Exception as e:
                print(f"Errore caricamento cache: {e}")
                self._analysis_cache = {}
        else:
            self._analysis_cache = {}

    def save_cache(self):
        cache_path = self._get_cache_path()
        try:
            cache_data = {
                "_version": self.cache_version,
                "entries": self._analysis_cache
            }
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Errore salvataggio cache: {e}")

    def load_profile(self) -> Dict:
        """Carica il profilo psicologico esistente"""
        if self.profile_file.exists():
            try:
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Errore caricamento profilo: {e}")
        
        # Profilo iniziale vuoto con sistema Top 5 rotating
        return {
            "version": "2.0",  # Aggiornata per supportare Top 5 system
            "created": datetime.datetime.now().isoformat(),
            "last_updated": datetime.datetime.now().isoformat(),
            "total_entries_analyzed": 0,
            
            # 🎭 Profilo Emotivo - Distribuzione percentuale emozioni
            "emotional_profile": {
                "happiness": 0.0, "sadness": 0.0, "anger": 0.0, "anxiety": 0.0,
                "serenity": 0.0, "stress": 0.0, "gratitude": 0.0, "motivation": 0.0
            },
            
            # 🧠 Tratti Personalità - 6 dimensioni psicologiche (radar)
            "personality_traits": {
                "openness": 0.0, "conscientiousness": 0.0, "extraversion": 0.0,
                "agreeableness": 0.0, "neuroticism": 0.0, "resilience": 0.0
            },
            
            # ⚡ Fattori di Stress - Top 5 con intensità
            "stress_factors": [],  # Lista di {"factor": str, "intensity": float, "timestamp": str}
            
            # 🌿 Strategie Efficaci - Top 5 con efficacia
            "effective_strategies": [],  # Lista di {"strategy": str, "efficacy": float, "timestamp": str}
            
            # 👥 Relazioni Chiave - Top 5 con qualità relazione
            "key_relationships": [],  # Lista di {"person": str, "quality": float, "timestamp": str}
            
            # 💡 Insight Principale - Summary card
            "main_insight": {
                "text": "Profilo in costruzione...",
                "confidence": 0.0,
                "last_updated": datetime.datetime.now().isoformat()
            },
            
            # Backward compatibility
            "behavioral_patterns": {},
            "relationship_dynamics": {},
            "growth_trends": {},
            "recommendations": []
        }

    def save_profile(self):
        """Salva il profilo psicologico aggiornato"""
        try:
            self.profile_data["last_updated"] = datetime.datetime.now().isoformat()
            with open(self.profile_file, "w", encoding="utf-8") as f:
                json.dump(self.profile_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio profilo: {e}")

    def analyze_emotions_from_text(self, text_content: str) -> Dict[str, float]:
        """
        Analisi completa che restituisce sia emozioni che aggiorna il profilo psicologico
        Mantiene retrocompatibilità restituendo solo le emozioni
        """
        full_analysis = self.analyze_full_entry(text_content)
        return full_analysis.get("emotions", {emotion: 0.0 for emotion in self.emotions_list})

    def analyze_full_entry(self, text_content: str) -> Dict:
        """
        Analisi completa di una voce del diario
        Restituisce: emozioni + profilo insights + aggiorna DB psicologico
        """
        if not self.api_key:
            return self._get_empty_analysis()

        # Cache check
        text_hash = hashlib.md5(text_content.encode('utf-8')).hexdigest()
        if text_hash in self._analysis_cache:
            return self._analysis_cache[text_hash]

        if len(text_content.strip()) < 50:
            return self._get_empty_analysis()

        # Limita la lunghezza del testo per evitare errori di token
        # Groq ha limiti sui token, circa 4000 caratteri sono sicuri
        MAX_TEXT_LENGTH = 4000
        if len(text_content) > MAX_TEXT_LENGTH:
            text_content = text_content[:MAX_TEXT_LENGTH] + "..."
            print(f"Testo troncato a {MAX_TEXT_LENGTH} caratteri per limiti API")
        
        # Costruisci il prompt per l'analisi completa
        prompt = self._build_analysis_prompt(text_content)
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Sei un esperto psicologo specializzato nell'analisi emotiva di testi autobiografici. Il tuo compito è identificare le emozioni presenti nei diari personali con precisione e sensibilità. Rispondi SEMPRE e SOLO con JSON valido, senza alcun testo aggiuntivo prima o dopo. Se non riesci ad analizzare il testo, restituisci comunque un JSON valido con valori 0.0."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,  # Slightly higher for more nuanced analysis
            "max_tokens": 1500
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            api_response = response.json()
            response_content = api_response['choices'][0]['message']['content']
            
            # Pulisci il contenuto per rimuovere possibili problemi di formato
            # Rimuovi eventuali testi prima/dopo il JSON
            response_content = response_content.strip()
            
            # Se c'è del testo prima del JSON, prova a estrarre solo il JSON
            if not response_content.startswith('{'):
                # Cerca il primo { e l'ultimo }
                start_idx = response_content.find('{')
                end_idx = response_content.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    response_content = response_content[start_idx:end_idx+1]
            
            # Prova a parsare il JSON
            try:
                analysis_result = json.loads(response_content)
            except json.JSONDecodeError as je:
                print(f"JSON malformato ricevuto: {response_content[:100]}...")
                print(f"Errore parsing: {je}")
                # Fallback: usa analisi vuota
                return self._get_empty_analysis()
            
            # Valida e normalizza le emozioni
            emotions = self._validate_emotions(analysis_result.get("emotions", {}))
            
            # Costruisci risultato strutturato
            structured_result = {
                "emotions": emotions,
                "daily_insights": analysis_result.get("daily_insights", {}),
                "profile_updates": analysis_result.get("profile_updates", {})
            }
            
            # Aggiorna il profilo psicologico
            self._update_psychological_profile(structured_result["profile_updates"])
            
            # Aggiorna anche il profilo emotivo cumulativo
            self.update_emotional_profile(emotions)
            
            # Salva in cache
            self._analysis_cache[text_hash] = structured_result
            self.save_cache()
            
            return structured_result

        except Exception as e:
            print(f"Errore analisi completa: {e}")
            return self._get_empty_analysis()

    def _build_analysis_prompt(self, text_content: str) -> str:
        """Costruisce il prompt per l'analisi emotiva approfondita"""
        # Limita il testo per evitare problemi di token
        text_excerpt = text_content[:2500]

        return f"""Sei un esperto psicologo. Analizza attentamente questa voce di diario personale e identifica le emozioni presenti.

CRITERI DI ANALISI:
- felice: gioia, contentezza, soddisfazione, entusiasmo, euforia
- triste: tristezza, malinconia, nostalgia, scoraggiamento, dolore emotivo
- arrabbiato: rabbia, frustrazione, irritazione, risentimento, indignazione
- ansioso: ansia, preoccupazione, nervosismo, agitazione, inquietudine
- sereno: calma, tranquillità, pace interiore, rilassatezza, equilibrio
- stressato: stress, pressione, sovraccarico, tensione, esaurimento
- grato: gratitudine, riconoscenza, apprezzamento, fortuna percepita
- motivato: motivazione, determinazione, energia positiva, voglia di fare

ISTRUZIONI:
1. Leggi il testo con attenzione cercando indicatori emotivi espliciti e impliciti
2. Considera il tono generale, le parole chiave, e il contesto
3. Assegna punteggi da 0.0 a 1.0 dove 0.0 = assente, 0.3 = lieve, 0.5 = moderato, 0.7 = forte, 1.0 = intensissimo
4. Più emozioni possono essere presenti contemporaneamente
5. Se il testo è neutro o descrittivo, assegna punteggi bassi ma non zero a sereno

TESTO DA ANALIZZARE:
---
{text_excerpt}
---

Rispondi SOLO con questo JSON esatto (nessun testo prima o dopo):
{{
  "emotions": {{
    "felice": 0.0,
    "triste": 0.0,
    "arrabbiato": 0.0,
    "ansioso": 0.0,
    "sereno": 0.0,
    "stressato": 0.0,
    "grato": 0.0,
    "motivato": 0.0
  }},
  "daily_insights": {{
    "mood_summary": "una frase che descrive lo stato emotivo dominante",
    "energy_level": 0.5
  }},
  "profile_updates": {{}}
}}"""

    def _validate_emotions(self, emotions_dict: Dict) -> Dict[str, float]:
        """Valida e normalizza i punteggi emotivi"""
        validated = {}
        for emotion in self.emotions_list:
            score = emotions_dict.get(emotion, 0.0)
            if isinstance(score, (int, float)):
                validated[emotion] = max(0.0, min(1.0, float(score)))
            else:
                validated[emotion] = 0.0
        return validated

    def _update_psychological_profile(self, profile_updates: Dict):
        """Aggiorna il profilo psicologico con nuovi insights"""
        if not profile_updates:
            return

        # Incrementa contatore voci analizzate
        self.profile_data["total_entries_analyzed"] += 1

        # Aggiorna personality_traits con il nuovo sistema
        if "personality_traits" in profile_updates:
            self.update_personality_traits(profile_updates["personality_traits"])

        # Aggiorna stress factors con sistema Top 5
        if "stress_factors" in profile_updates:
            for factor_data in profile_updates["stress_factors"]:
                if isinstance(factor_data, dict) and "factor" in factor_data:
                    self.add_stress_factor(
                        factor_data["factor"], 
                        factor_data.get("intensity", 0.5)
                    )

        # Aggiorna effective strategies con sistema Top 5
        if "effective_strategies" in profile_updates:
            for strategy_data in profile_updates["effective_strategies"]:
                if isinstance(strategy_data, dict) and "strategy" in strategy_data:
                    self.add_effective_strategy(
                        strategy_data["strategy"], 
                        strategy_data.get("efficacy", 0.5)
                    )

        # Aggiorna key relationships con sistema Top 5
        if "key_relationships" in profile_updates:
            for rel_data in profile_updates["key_relationships"]:
                if isinstance(rel_data, dict) and "person" in rel_data:
                    self.add_key_relationship(
                        rel_data["person"], 
                        rel_data.get("quality", 0.5)
                    )

        # Aggiorna main insight
        if "main_insight" in profile_updates and profile_updates["main_insight"]:
            self.update_main_insight(profile_updates["main_insight"])

        # Backward compatibility - mantieni il vecchio sistema
        # Aggiorna behavioral_patterns
        if "behavioral_patterns" in profile_updates:
            for pattern, description in profile_updates["behavioral_patterns"].items():
                if pattern not in self.profile_data["behavioral_patterns"]:
                    self.profile_data["behavioral_patterns"][pattern] = []
                if description and description not in self.profile_data["behavioral_patterns"][pattern]:
                    self.profile_data["behavioral_patterns"][pattern].append({
                        "description": description,
                        "observed_date": datetime.datetime.now().isoformat()
                    })

        # Backward compatibility - relationship_dynamics
        if "relationship_insights" in profile_updates:
            rel_insights = profile_updates["relationship_insights"]
            if "relationship_quality_indicators" in rel_insights:
                for person, quality in rel_insights["relationship_quality_indicators"].items():
                    if person not in self.profile_data["relationship_dynamics"]:
                        self.profile_data["relationship_dynamics"][person] = {
                            "interactions": [],
                            "relationship_quality": "unknown"
                        }
                    
                    self.profile_data["relationship_dynamics"][person]["interactions"].append({
                        "date": datetime.datetime.now().isoformat(),
                        "quality_indicator": quality
                    })
                    
                    # Mantieni solo le ultime 10 interazioni per persona
                    interactions = self.profile_data["relationship_dynamics"][person]["interactions"]
                    if len(interactions) > 10:
                        self.profile_data["relationship_dynamics"][person]["interactions"] = interactions[-10:]

        # Backward compatibility - liste legacy
        for list_field in ["stress_triggers", "coping_mechanisms", "growth_indicators"]:
            if list_field in profile_updates and profile_updates[list_field]:
                if list_field not in self.profile_data:
                    self.profile_data[list_field] = []
                
                for item in profile_updates[list_field]:
                    if item not in self.profile_data[list_field]:
                        self.profile_data[list_field].append(item)

        # Salva il profilo aggiornato
        self.save_profile()

    def _get_empty_analysis(self) -> Dict:
        """Restituisce un'analisi vuota per casi di errore"""
        return {
            "emotions": {emotion: 0.0 for emotion in self.emotions_list},
            "daily_insights": {},
            "profile_updates": {}
        }

    def get_psychological_profile(self) -> Dict:
        """Restituisce il profilo psicologico completo"""
        return self.profile_data.copy()

    def get_personality_summary(self) -> str:
        """Genera un riassunto testuale del profilo psicologico"""
        if not self.profile_data or self.profile_data["total_entries_analyzed"] < 3:
            return "Profilo psicologico in costruzione. Scrivi qualche voce in più per insights più accurati."

        summary_parts = []
        
        # Personality traits
        traits = self.profile_data.get("personality_traits", {})
        if traits:
            summary_parts.append("=== TRATTI PERSONALITÀ ===")
            for trait, data in traits.items():
                if data["confidence"] > 0.3:  # Solo tratti con buona confidenza
                    summary_parts.append(f"• {trait.replace('_', ' ').title()}: {data['value']:.1f}/1.0 (confidenza: {data['confidence']:.1f})")

        # Stress triggers
        triggers = self.profile_data.get("stress_triggers", [])
        if triggers:
            summary_parts.append("\n=== FATTORI DI STRESS ===")
            for trigger in triggers[:5]:  # Top 5
                summary_parts.append(f"• {trigger}")

        # Coping mechanisms
        coping = self.profile_data.get("coping_mechanisms", [])
        if coping:
            summary_parts.append("\n=== STRATEGIE DI GESTIONE ===")
            for mechanism in coping[:5]:  # Top 5
                summary_parts.append(f"• {mechanism}")

        # Relationship dynamics
        relationships = self.profile_data.get("relationship_dynamics", {})
        if relationships:
            summary_parts.append("\n=== DINAMICHE RELAZIONALI ===")
            for person, data in list(relationships.items())[:3]:  # Top 3 relazioni
                recent_interaction = data["interactions"][-1] if data["interactions"] else None
                if recent_interaction:
                    summary_parts.append(f"• {person}: {recent_interaction['quality_indicator']}")

        summary_parts.append(f"\n📊 Basato su {self.profile_data['total_entries_analyzed']} voci analizzate")
        summary_parts.append(f"📅 Ultimo aggiornamento: {self.profile_data['last_updated'][:10]}")

        return "\n".join(summary_parts) if summary_parts else "Nessun dato sufficiente per generare un riassunto."
    
    def analyze_and_update_psychological_profile(self):
        """Analizza i file del diario esistenti per costruire il profilo psicologico"""
        print("🔍 Analizzando file del diario per costruire il profilo psicologico...")
        
        # Trova tutti i file di diario
        journal_files = sorted([
            f for f in self.journal_dir.glob("*.txt") 
            if f.is_file() and f.stem.count('-') == 2  # Pattern YYYY-MM-DD
        ], key=lambda x: x.stem)
        
        if not journal_files:
            print("[WARNING] Nessun file di diario trovato")
            return
        
        # Analizza gli ultimi 10 file per non sovraccaricare l'API
        files_to_analyze = journal_files[-10:]
        
        for file_path in files_to_analyze:
            try:
                content = file_path.read_text(encoding='utf-8')
                if len(content.strip()) > 50:  # Solo se ha contenuto significativo
                    print(f"Analizzando {file_path.name}...")
                    self.analyze_full_entry(content)
                    time.sleep(1)  # Piccola pausa per non sovraccaricare l'API
            except Exception as e:
                print(f"[ERROR] Errore analizzando {file_path.name}: {e}")
                continue

        print(f"[OK] Analisi completata. Profilo aggiornato con {len(files_to_analyze)} voci.")

    # Mantieni retrocompatibilità con il metodo esistente
    def analyze_emotions_from_journal_files(self, num_recent_files: int = 30) -> Dict[str, Dict[str, float]]:
        """Analizza le emozioni dai file di diario (metodo legacy per retrocompatibilità)"""
        emotions_by_date = defaultdict(lambda: {emotion: 0.0 for emotion in self.emotions_list})
        
        all_journal_files = [
            f for f in self.journal_dir.glob("*.txt") 
            if f.name != "settings.json" and f.is_file()
        ]
        
        try:
            sorted_files = sorted(all_journal_files, key=lambda x: x.stat().st_mtime, reverse=True)
        except OSError as e:
            print(f"Errore accesso file: {e}")
            sorted_files = all_journal_files

        files_to_analyze = sorted_files[:num_recent_files]

        for file_path in files_to_analyze:
            date_str = file_path.stem
            try:
                datetime.datetime.strptime(date_str, '%Y-%m-%d')
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if content.strip():
                    # Usa la nuova analisi completa ma restituisci solo le emozioni
                    analysis = self.analyze_full_entry(content)
                    emotions_by_date[date_str] = analysis["emotions"]
                else:
                    emotions_by_date[date_str] = {emotion: 0.0 for emotion in self.emotions_list}

            except ValueError: 
                continue
            except Exception as e:
                print(f"Errore analizzando {file_path.name}: {e}")
                emotions_by_date[date_str] = {emotion: 0.0 for emotion in self.emotions_list}
        
        return emotions_by_date

    # === SISTEMA TOP 5 ROTATING QUEUE ===
    
    def _update_top5_list(self, list_key: str, new_item: Dict, max_items: int = 5):
        """Aggiorna una lista Top 5 con sistema rotating queue"""
        if list_key not in self.profile_data:
            self.profile_data[list_key] = []
        
        current_list = self.profile_data[list_key]
        
        # Cerca se l'item esiste già (confronta per nome/fattore)
        item_key = None
        if list_key == "stress_factors":
            item_key = "factor"
        elif list_key == "effective_strategies":
            item_key = "strategy"  
        elif list_key == "key_relationships":
            item_key = "person"
            
        existing_index = -1
        for i, existing in enumerate(current_list):
            if existing.get(item_key) == new_item.get(item_key):
                existing_index = i
                break
        
        if existing_index >= 0:
            # Aggiorna l'item esistente
            current_list[existing_index] = new_item
        else:
            # Aggiungi nuovo item
            current_list.append(new_item)
            
            # Se supera il limite, rimuovi il più vecchio
            if len(current_list) > max_items:
                current_list.pop(0)
        
        # Ordina per valore (intensità/efficacia/qualità) decrescente
        if list_key == "stress_factors":
            current_list.sort(key=lambda x: x.get("intensity", 0), reverse=True)
        elif list_key == "effective_strategies":
            current_list.sort(key=lambda x: x.get("efficacy", 0), reverse=True)
        elif list_key == "key_relationships":
            current_list.sort(key=lambda x: x.get("quality", 0), reverse=True)
    
    def add_stress_factor(self, factor: str, intensity: float):
        """Aggiunge un fattore di stress al Top 5"""
        new_item = {
            "factor": factor,
            "intensity": intensity,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self._update_top5_list("stress_factors", new_item)
        self.save_profile()
    
    def add_effective_strategy(self, strategy: str, efficacy: float):
        """Aggiunge una strategia efficace al Top 5"""
        new_item = {
            "strategy": strategy,
            "efficacy": efficacy,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self._update_top5_list("effective_strategies", new_item)
        self.save_profile()
    
    def add_key_relationship(self, person: str, quality: float):
        """Aggiunge una relazione chiave al Top 5"""
        new_item = {
            "person": person,
            "quality": quality,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self._update_top5_list("key_relationships", new_item)
        self.save_profile()
    
    def update_emotional_profile(self, emotions_dict: Dict[str, float]):
        """Aggiorna il profilo emotivo cumulativo"""
        if "emotional_profile" not in self.profile_data:
            self.profile_data["emotional_profile"] = {emotion: 0.0 for emotion in self.emotions_list}
        
        # Calcolo rolling average pesato (più peso alle emozioni recenti)
        weight_new = 0.3  # 30% peso alla nuova analisi
        weight_old = 0.7  # 70% peso al profilo esistente
        
        for emotion, value in emotions_dict.items():
            emotion_key = emotion.lower()
            if emotion_key == "felice": emotion_key = "happiness"
            elif emotion_key == "triste": emotion_key = "sadness"
            elif emotion_key == "arrabbiato": emotion_key = "anger"
            elif emotion_key == "ansioso": emotion_key = "anxiety"
            elif emotion_key == "sereno": emotion_key = "serenity"
            elif emotion_key == "stressato": emotion_key = "stress"
            elif emotion_key == "grato": emotion_key = "gratitude"
            elif emotion_key == "motivato": emotion_key = "motivation"
            
            if emotion_key in self.profile_data["emotional_profile"]:
                current_value = self.profile_data["emotional_profile"][emotion_key]
                new_value = (current_value * weight_old) + (value * weight_new)
                self.profile_data["emotional_profile"][emotion_key] = new_value
        
        self.save_profile()
    
    def update_personality_traits(self, traits_dict: Dict[str, float]):
        """Aggiorna i tratti di personalità (6 dimensioni)"""
        if "personality_traits" not in self.profile_data:
            self.profile_data["personality_traits"] = {
                "openness": 0.0, "conscientiousness": 0.0, "extraversion": 0.0,
                "agreeableness": 0.0, "neuroticism": 0.0, "resilience": 0.0
            }
        
        # Rolling average pesato
        weight_new = 0.2  # 20% peso alla nuova analisi (tratti cambiano lentamente)
        weight_old = 0.8  # 80% peso ai tratti esistenti
        
        for trait, value in traits_dict.items():
            if trait in self.profile_data["personality_traits"]:
                current_value = self.profile_data["personality_traits"][trait]
                new_value = (current_value * weight_old) + (value * weight_new)
                self.profile_data["personality_traits"][trait] = new_value
        
        self.save_profile()
    
    def update_main_insight(self, insight_text: str, confidence: float = 0.8):
        """Aggiorna l'insight principale"""
        self.profile_data["main_insight"] = {
            "text": insight_text,
            "confidence": confidence,
            "last_updated": datetime.datetime.now().isoformat()
        }
        self.save_profile()
    
    def get_psychological_dashboard_data(self) -> Dict:
        """Restituisce tutti i dati strutturati per il dashboard psicologico"""
        # Mappa le emozioni dall'inglese all'italiano per compatibilità
        emotional_profile_eng = self.profile_data.get("emotional_profile", {})
        emotional_profile_ita = {}
        
        # Mappatura inglese -> italiano
        emotion_mapping = {
            'happiness': 'felice',
            'sadness': 'triste',
            'anger': 'arrabbiato',
            'anxiety': 'ansioso',
            'serenity': 'sereno',
            'stress': 'stressato',
            'gratitude': 'grato',
            'motivation': 'motivato'
        }
        
        # Converti le chiavi da inglese a italiano
        for eng_key, ita_key in emotion_mapping.items():
            if eng_key in emotional_profile_eng:
                emotional_profile_ita[ita_key] = emotional_profile_eng[eng_key]
            else:
                emotional_profile_ita[ita_key] = 0.0
        
        return {
            "emotional_profile": emotional_profile_ita,
            "personality_traits": self.profile_data.get("personality_traits", {}),
            "stress_factors": self.profile_data.get("stress_factors", []),
            "effective_strategies": self.profile_data.get("effective_strategies", []),
            "key_relationships": self.profile_data.get("key_relationships", []),
            "main_insight": self.profile_data.get("main_insight", {}),
            "total_entries": self.profile_data.get("total_entries_analyzed", 0),
            "last_updated": self.profile_data.get("last_updated", "")
        }
    
    def get_psychological_dashboard_data(self) -> Dict:
        """Get data for the psychological profile dashboard"""
        # Carica i dati più recenti
        self.profile_data = self.load_profile()
        
        # Se non ci sono dati analizzati, prova ad analizzare i file esistenti
        if self.profile_data.get("total_entries_analyzed", 0) == 0:
            # Analizza i file di diario esistenti
            self.analyze_and_update_psychological_profile()
            self.profile_data = self.load_profile()
        
        # Calcola il profilo emotivo cumulativo
        emotional_profile = defaultdict(float)
        cumulative_summary = self.profile_data.get("cumulative_emotional_summary", {})
        
        # Mappa le emozioni dall'inglese all'italiano
        emotion_mapping = {
            'happiness': 'felice',
            'sadness': 'triste', 
            'anger': 'arrabbiato',
            'anxiety': 'ansioso',
            'serenity': 'sereno',
            'stress': 'stressato',
            'gratitude': 'grato',
            'motivation': 'motivato'
        }
        
        for eng_key, ita_key in emotion_mapping.items():
            if eng_key in cumulative_summary:
                emotional_profile[ita_key] = cumulative_summary[eng_key]
        
        # Se il profilo emotivo è vuoto, usa il profilo base dai dati
        if not emotional_profile or all(v == 0 for v in emotional_profile.values()):
            base_profile = self.profile_data.get("emotional_profile", {})
            for eng_key, ita_key in emotion_mapping.items():
                if eng_key in base_profile:
                    emotional_profile[ita_key] = base_profile[eng_key]
        
        # Se ancora vuoto, usa valori di default
        if not emotional_profile or all(v == 0 for v in emotional_profile.values()):
            emotional_profile = {
                'felice': 0.15,
                'triste': 0.10,
                'arrabbiato': 0.05,
                'ansioso': 0.20,
                'sereno': 0.20,
                'stressato': 0.10,
                'grato': 0.10,
                'motivato': 0.10
            }
        
        # Prepara i dati per personality_traits come valori numerici, non dict
        personality_traits_raw = self.profile_data.get("personality_traits", {})
        personality_traits = {}
        
        # Converti i dati dei tratti in valori numerici 0-1
        if isinstance(personality_traits_raw, dict):
            for trait, value in personality_traits_raw.items():
                if isinstance(value, dict):
                    # Se è un dict, prendi il valore score o un default
                    personality_traits[trait] = value.get('score', 0.5)
                elif isinstance(value, (int, float)):
                    # Se è già un numero, usalo
                    personality_traits[trait] = float(value)
                else:
                    # Default a 0.5 se non riconosciuto
                    personality_traits[trait] = 0.5
        
        # Usa sempre i 5 tratti standard per la dashboard, mappando i dati esistenti
        standard_traits = {
            "Apertura": 0.5,
            "Coscienziosità": 0.5,
            "Estroversione": 0.5,
            "Gradevolezza": 0.5,
            "Stabilità Emotiva": 0.5
        }
        
        # Mappa i dati esistenti ai tratti standard se possibile
        trait_mapping = {
            "introversion_tendency": "Estroversione",
            "stress_response_style": "Stabilità Emotiva",
            "openness": "Apertura",
            "conscientiousness": "Coscienziosità",
            "agreeableness": "Gradevolezza",
            "extraversion": "Estroversione",
            "neuroticism": "Stabilità Emotiva",
            "resilience": "Stabilità Emotiva"
        }
        
        # Applica i valori esistenti ai tratti standard
        for old_trait, value in personality_traits.items():
            if old_trait in trait_mapping:
                standard_trait = trait_mapping[old_trait]
                standard_traits[standard_trait] = value
            elif old_trait in standard_traits:
                # Se il trait è già nel formato standard, usalo direttamente
                standard_traits[old_trait] = value
        
        # Se abbiamo dati reali del profilo, usa quelli invece dei default
        if self.profile_data.get("total_entries_analyzed", 0) > 0:
            # Prova a caricare i tratti dal profilo salvato
            saved_traits = self.profile_data.get("personality_traits", {})
            if saved_traits:
                print(f"[DEBUG] Caricando tratti salvati: {saved_traits}")
                for trait_key, trait_value in saved_traits.items():
                    if trait_key in trait_mapping:
                        mapped_trait = trait_mapping[trait_key]
                        if isinstance(trait_value, (int, float)):
                            standard_traits[mapped_trait] = float(trait_value)
                            print(f"[OK] Mappato {trait_key} -> {mapped_trait}: {trait_value}")
                        elif isinstance(trait_value, dict):
                            value = trait_value.get('value', trait_value.get('score', 0.5))
                            # Assicurati che il valore sia numerico
                            if isinstance(value, (int, float)):
                                standard_traits[mapped_trait] = float(value)
                                print(f"[OK] Mappato {trait_key} -> {mapped_trait}: {value}")
                            else:
                                # Se è una stringa o altro, usa il default
                                standard_traits[mapped_trait] = 0.5
                                print(f"[WARNING] Valore non numerico per {trait_key}, usando default 0.5")
                    elif trait_key in standard_traits:
                        if isinstance(trait_value, (int, float)):
                            standard_traits[trait_key] = float(trait_value)
                            print(f"[OK] Usato direttamente {trait_key}: {trait_value}")
                        elif isinstance(trait_value, dict):
                            value = trait_value.get('value', trait_value.get('score', 0.5))
                            # Assicurati che il valore sia numerico
                            if isinstance(value, (int, float)):
                                standard_traits[trait_key] = float(value)
                                print(f"[OK] Usato direttamente {trait_key}: {value}")
                            else:
                                # Se è una stringa o altro, usa il default
                                standard_traits[trait_key] = 0.5
                                print(f"[WARNING] Valore non numerico per {trait_key}, usando default 0.5")
                print(f"[INFO] Tratti finali: {standard_traits}")
            else:
                print(f"[WARNING] Nessun tratto salvato trovato nel profilo")
        else:
            print(f"[WARNING] Nessuna voce analizzata nel profilo (total_entries_analyzed: {self.profile_data.get('total_entries_analyzed', 0)})")
        
        personality_traits = standard_traits
        
        # Prepara i fattori di stress
        stress_factors = []
        stress_data = self.profile_data.get("stress_factors", [])
        
        # Se stress_factors è una lista di stringhe o dict
        for i, factor in enumerate(stress_data[:5]):
            if isinstance(factor, dict):
                # Prova diverse chiavi possibili
                name = factor.get("factor") or factor.get("name") or factor.get("description", f"Fattore {i+1}")
                value = factor.get("impact") or factor.get("value") or factor.get("score", 0.5)
                stress_factors.append({
                    "name": str(name),
                    "value": float(value) if isinstance(value, (int, float)) else 0.5
                })
            elif isinstance(factor, str):
                stress_factors.append({
                    "name": factor,
                    "value": 0.5
                })
            else:
                stress_factors.append({
                    "name": f"Fattore {i+1}",
                    "value": 0.5
                })
        
        # Se non ci sono fattori di stress, usa valori di default
        if not stress_factors:
            stress_factors = [
                {"name": "Lavoro", "value": 0.3},
                {"name": "Relazioni", "value": 0.2},
                {"name": "Salute", "value": 0.1},
                {"name": "Finanze", "value": 0.2},
                {"name": "Tempo", "value": 0.4}
            ]
        
        # Prepara le strategie efficaci
        effective_strategies = []
        strategies_data = self.profile_data.get("effective_strategies", [])
        
        for i, strategy in enumerate(strategies_data[:5]):
            if isinstance(strategy, dict):
                # Prova diverse chiavi possibili
                name = strategy.get("strategy") or strategy.get("name") or strategy.get("description", f"Strategia {i+1}")
                value = strategy.get("effectiveness") or strategy.get("value") or strategy.get("score", 0.7)
                effective_strategies.append({
                    "name": str(name),
                    "value": float(value) if isinstance(value, (int, float)) else 0.7
                })
            elif isinstance(strategy, str):
                effective_strategies.append({
                    "name": strategy,
                    "value": 0.7
                })
            else:
                effective_strategies.append({
                    "name": f"Strategia {i+1}",
                    "value": 0.7
                })
        
        # Se non ci sono strategie, usa valori di default
        if not effective_strategies:
            effective_strategies = [
                {"name": "Meditazione", "value": 0.8},
                {"name": "Esercizio fisico", "value": 0.7},
                {"name": "Scrittura", "value": 0.9},
                {"name": "Socializzare", "value": 0.6},
                {"name": "Riposo", "value": 0.7}
            ]
        
        # Prepara le relazioni chiave
        key_relationships = []
        relationships_data = self.profile_data.get("relationship_dynamics", {})
        
        for i, (person, data) in enumerate(list(relationships_data.items())[:5]):
            if isinstance(data, dict):
                # Calcola un punteggio di qualità basato sulle interazioni
                interactions = data.get("interactions", [])
                if interactions:
                    # Prendi l'ultima interazione per la qualità
                    last_interaction = interactions[-1]
                    quality = last_interaction.get("emotional_tone", 0.5)
                    if isinstance(quality, str):
                        # Converti parole in numeri
                        quality_map = {"positive": 0.8, "neutral": 0.5, "negative": 0.2}
                        quality = quality_map.get(quality.lower(), 0.5)
                else:
                    quality = 0.5
                
                key_relationships.append({
                    "name": person,
                    "value": float(quality) if isinstance(quality, (int, float)) else 0.5
                })
            else:
                key_relationships.append({
                    "name": str(person),
                    "value": 0.5
                })
        
        # Se non ci sono relazioni, usa valori di default
        if not key_relationships:
            key_relationships = [
                {"name": "Famiglia", "value": 0.8},
                {"name": "Amici", "value": 0.7},
                {"name": "Colleghi", "value": 0.6},
                {"name": "Partner", "value": 0.9},
                {"name": "Conoscenti", "value": 0.5}
            ]
        
        # Prepara l'insight principale
        main_insight = self.profile_data.get("main_insight", {})
        if not main_insight or not main_insight.get("text"):
            # Genera un insight di default basato sui dati disponibili
            total_entries = self.profile_data.get("total_entries_analyzed", 0)
            if total_entries > 0:
                # Trova l'emozione dominante
                dominant_emotion = max(emotional_profile.items(), key=lambda x: x[1]) if emotional_profile else ("sereno", 0.2)
                
                insight_text = f"Dopo aver analizzato {total_entries} voci del diario, emerge che la tua emozione predominante è '{dominant_emotion[0]}' ({dominant_emotion[1]*100:.0f}%). "
                
                # Aggiungi suggerimento basato sui fattori di stress
                if stress_factors:
                    top_stress = max(stress_factors, key=lambda x: x['value'])
                    insight_text += f"Il principale fattore di stress sembra essere '{top_stress['name']}'. "
                
                # Aggiungi strategia efficace
                if effective_strategies:
                    top_strategy = max(effective_strategies, key=lambda x: x['value'])
                    insight_text += f"La strategia più efficace per te è '{top_strategy['name']}'."
                
                main_insight = {"text": insight_text}
            else:
                main_insight = {"text": "Continua a scrivere nel diario per generare insights personalizzati basati sulle tue riflessioni."}
        
        return {
            "emotional_profile": dict(emotional_profile),
            "personality_traits": personality_traits,
            "stress_factors": stress_factors,
            "effective_strategies": effective_strategies,
            "key_relationships": key_relationships,
            "main_insight": main_insight,
            "total_entries": self.profile_data.get("total_entries_analyzed", 0),
            "last_updated": self.profile_data.get("last_updated", "")
        }