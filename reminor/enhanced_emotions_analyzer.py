#!/usr/bin/env python3
"""
Enhanced EmotionsAnalyzer per MySoul Extreme Journal
Combina analisi emozioni + profilo psicologico cumulativo
"""

import os
import datetime
import requests
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
import hashlib

class EnhancedEmotionsAnalyzer:
    def __init__(self, journal_dir: Path):
        self.journal_dir = journal_dir
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            print("[AVVISO] GROQ_API_KEY non trovata per EnhancedEmotionsAnalyzer")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "deepseek-r1-distill-llama-70b"
        
        # Lista emozioni standard (per retrocompatibilità)
        self.emotions_list = [
            "felice", "triste", "arrabbiato", "ansioso", 
            "sereno", "stressato", "grato", "motivato"
        ]
        
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
                    self._analysis_cache = json.load(f)
            except Exception as e:
                print(f"Errore caricamento cache: {e}")
                self._analysis_cache = {}
        else:
            self._analysis_cache = {}

    def save_cache(self):
        cache_path = self._get_cache_path()
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(self._analysis_cache, f)
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
            
            # Tratti Personalita' - 6 dimensioni psicologiche (radar)
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

        # Costruisci il prompt per l'analisi completa
        prompt = self._build_analysis_prompt(text_content)
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": "Sei un esperto psicologo che analizza diari personali. Rispondi ESCLUSIVAMENTE con JSON valido seguendo esattamente la struttura richiesta."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            api_response = response.json()
            response_content = api_response['choices'][0]['message']['content']
            
            analysis_result = json.loads(response_content)
            
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
        """Costruisce il prompt per l'analisi completa"""
        emotions_list_str = ", ".join(self.emotions_list)
        
        # Carica contesto del profilo esistente per analisi più accurata
        profile_context = ""
        if self.profile_data.get("personality_traits"):
            recent_traits = list(self.profile_data["personality_traits"].keys())[:3]
            profile_context = f"\nContesto profilo esistente: {recent_traits}"

        return f"""
Analizza questa voce di diario e restituisci SOLO un JSON valido con questa struttura:

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
    "mood_summary": "breve descrizione umore",
    "energy_level": 0.5,
    "key_people": [],
    "main_topics": [],
    "concerns": []
  }},
  "profile_updates": {{
    "stress_triggers": [],
    "coping_mechanisms": [],
    "personality_traits": {{
      "openness": 0.5,
      "conscientiousness": 0.5,
      "extraversion": 0.5,
      "agreeableness": 0.5,
      "neuroticism": 0.5,
      "resilience": 0.5
    }},
    "stress_factors": [],
    "effective_strategies": [],
    "key_relationships": [],
    "main_insight": ""
  }}
}}

ISTRUZIONI SPECIFICHE:
- emotions: valori da 0.0 a 1.0 che indicano l'intensità di ogni emozione nel testo
- personality_traits: valori da 0.0 a 1.0 per i 6 tratti principali basati sul contenuto
- stress_factors: array di oggetti con {{"factor": "descrizione", "intensity": 0.0-1.0}}
- effective_strategies: array di oggetti con {{"strategy": "descrizione", "efficacy": 0.0-1.0}}
- key_relationships: array di oggetti con {{"person": "nome", "quality": 0.0-1.0}}
- main_insight: stringa con insight psicologico principale (max 100 parole)

{profile_context}

Testo da analizzare:
{text_content[:2000]}

Rispondi SOLO con JSON valido, nessun altro testo.
"""

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

        summary_parts.append(f"\n[STATISTICHE] Basato su {self.profile_data['total_entries_analyzed']} voci analizzate")
        summary_parts.append(f"📅 Ultimo aggiornamento: {self.profile_data['last_updated'][:10]}")

        return "\n".join(summary_parts) if summary_parts else "Nessun dato sufficiente per generare un riassunto."

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