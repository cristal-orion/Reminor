"""
Knowledge Extractor for Reminor
Extracts structured knowledge from diary entries to build a persistent knowledge base
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class KnowledgeExtractor:
    """
    Extracts and manages structured knowledge from diary entries.
    Creates a persistent knowledge base that's always available to the chatbot.
    """

    def __init__(self, user_dir: Path):
        """
        Initialize the knowledge extractor.

        Args:
            user_dir: User's data directory
        """
        self.user_dir = Path(user_dir)
        self.knowledge_file = self.user_dir / "user_knowledge.json"
        self.journal_dir = self.user_dir / "journal"

        self.api_key = os.getenv('GROQ_API_KEY')
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"

        # Default empty knowledge structure
        self.knowledge = self._empty_knowledge()

        # Load existing knowledge if available
        self.load_knowledge()

    def _empty_knowledge(self) -> Dict[str, Any]:
        """Return empty knowledge structure"""
        return {
            "version": "1.0",
            "last_updated": None,
            "entries_analyzed": 0,
            "people": [],
            "places": [],
            "events": [],
            "emotional_patterns": [],
            "themes": [],
            "summary": ""
        }

    def load_knowledge(self) -> Dict[str, Any]:
        """Load existing knowledge from file"""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    self.knowledge = json.load(f)
            except Exception as e:
                print(f"[WARNING] Error loading knowledge: {e}")
                self.knowledge = self._empty_knowledge()
        return self.knowledge

    def save_knowledge(self):
        """Save knowledge to file"""
        self.knowledge["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge, f, ensure_ascii=False, indent=2)
            print(f"[OK] Knowledge base saved: {self.knowledge_file}")
        except Exception as e:
            print(f"[ERROR] Error saving knowledge: {e}")

    def get_all_entries(self) -> Dict[str, str]:
        """Get all diary entries from journal directory"""
        entries = {}
        if not self.journal_dir.exists():
            return entries

        for file_path in sorted(self.journal_dir.glob("*.txt")):
            try:
                date_str = file_path.stem  # filename without extension
                content = file_path.read_text(encoding='utf-8')
                if content.strip():
                    entries[date_str] = content
            except Exception as e:
                print(f"[WARNING] Error reading {file_path}: {e}")

        return entries

    def extract_knowledge(self, entries: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Extract structured knowledge from diary entries using LLM.

        Args:
            entries: Dict of date -> content. If None, reads from journal_dir.

        Returns:
            Updated knowledge dictionary
        """
        if not self.api_key:
            print("[ERROR] GROQ_API_KEY not set, cannot extract knowledge")
            return self.knowledge

        if entries is None:
            entries = self.get_all_entries()

        if not entries:
            print("[WARNING] No diary entries found")
            return self.knowledge

        print(f"[INFO] Extracting knowledge from {len(entries)} diary entries...")

        # Prepare diary content for analysis
        # Combine all entries with dates
        diary_text = ""
        for date, content in sorted(entries.items()):
            diary_text += f"\n=== {date} ===\n{content}\n"

        # Truncate if too long (keep most recent entries)
        max_chars = 30000  # Leave room for prompt
        if len(diary_text) > max_chars:
            diary_text = diary_text[-max_chars:]
            print(f"[INFO] Diary truncated to last {max_chars} characters")

        # Build extraction prompt
        extraction_prompt = self._build_extraction_prompt(diary_text)

        try:
            response = self._call_llm(extraction_prompt)
            if response:
                self._parse_extraction_response(response, len(entries))
                self.save_knowledge()
                print(f"[OK] Knowledge extracted successfully")
        except Exception as e:
            print(f"[ERROR] Knowledge extraction failed: {e}")

        return self.knowledge

    def _build_extraction_prompt(self, diary_text: str) -> str:
        """Build the prompt for knowledge extraction"""
        return f"""Analizza questo diario personale e estrai le informazioni chiave in formato JSON.

DIARIO:
{diary_text}

Estrai e restituisci SOLO un JSON valido con questa struttura esatta:

{{
  "people": [
    {{"name": "Nome", "relationship": "relazione con l'autore", "context": "breve contesto di come appare nel diario", "sentiment": "positivo/negativo/neutro/complicato"}}
  ],
  "places": [
    {{"name": "Nome luogo", "type": "citta/locale/natura/altro", "context": "cosa e' successo li'", "frequency": "una volta/ricorrente"}}
  ],
  "events": [
    {{"date": "YYYY-MM-DD se nota", "description": "breve descrizione", "importance": "alta/media/bassa", "emotions": ["emozione1", "emozione2"]}}
  ],
  "emotional_patterns": [
    {{"pattern": "descrizione del pattern", "triggers": ["trigger1", "trigger2"], "frequency": "spesso/a volte/raro"}}
  ],
  "themes": ["tema1", "tema2", "tema3"],
  "summary": "Riassunto in 2-3 frasi della persona che scrive questo diario, il suo carattere, le sue preoccupazioni principali"
}}

REGOLE:
- Estrai SOLO informazioni ESPLICITAMENTE presenti nel diario
- NON inventare dettagli
- Mantieni i nomi esattamente come scritti
- Il summary deve essere in terza persona
- Rispondi SOLO con il JSON, nessun altro testo"""

    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call Groq LLM API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Sei un analista che estrae informazioni strutturate da testi. Rispondi SOLO con JSON valido."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.3  # Lower temperature for more consistent extraction
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[ERROR] LLM API call failed: {e}")
            return None

    def _parse_extraction_response(self, response: str, num_entries: int):
        """Parse LLM response and update knowledge"""
        try:
            # Try to extract JSON from response
            # Sometimes LLM wraps it in markdown code blocks
            json_str = response.strip()
            if json_str.startswith("```"):
                # Remove markdown code blocks
                lines = json_str.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith("```json"):
                        in_json = True
                        continue
                    elif line.startswith("```"):
                        in_json = False
                        continue
                    if in_json or (not line.startswith("```")):
                        json_lines.append(line)
                json_str = "\n".join(json_lines)

            extracted = json.loads(json_str)

            # Update knowledge with extracted data
            self.knowledge["people"] = extracted.get("people", [])
            self.knowledge["places"] = extracted.get("places", [])
            self.knowledge["events"] = extracted.get("events", [])
            self.knowledge["emotional_patterns"] = extracted.get("emotional_patterns", [])
            self.knowledge["themes"] = extracted.get("themes", [])
            self.knowledge["summary"] = extracted.get("summary", "")
            self.knowledge["entries_analyzed"] = num_entries

        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON response: {e}")
            print(f"[DEBUG] Response was: {response[:500]}...")

    def get_knowledge_for_prompt(self) -> str:
        """
        Format knowledge base for inclusion in chat prompt.

        Returns:
            Formatted string for system prompt
        """
        if not self.knowledge.get("entries_analyzed", 0):
            return "Nessuna knowledge base disponibile. Le informazioni verranno estratte dalla ricerca."

        parts = []

        # Summary
        if self.knowledge.get("summary"):
            parts.append(f"## Chi e' l'utente\n{self.knowledge['summary']}")

        # People
        people = self.knowledge.get("people", [])
        if people:
            people_lines = []
            for p in people[:10]:  # Max 10 people
                name = p.get("name", "?")
                rel = p.get("relationship", "")
                ctx = p.get("context", "")
                sentiment = p.get("sentiment", "")
                line = f"- **{name}**"
                if rel:
                    line += f" ({rel})"
                if ctx:
                    line += f": {ctx}"
                if sentiment and sentiment != "neutro":
                    line += f" [{sentiment}]"
                people_lines.append(line)
            parts.append("## Persone importanti\n" + "\n".join(people_lines))

        # Places
        places = self.knowledge.get("places", [])
        if places:
            places_lines = []
            for p in places[:8]:  # Max 8 places
                name = p.get("name", "?")
                ctx = p.get("context", "")
                line = f"- **{name}**"
                if ctx:
                    line += f": {ctx}"
                places_lines.append(line)
            parts.append("## Luoghi significativi\n" + "\n".join(places_lines))

        # Key events
        events = self.knowledge.get("events", [])
        important_events = [e for e in events if e.get("importance") == "alta"][:5]
        if important_events:
            events_lines = []
            for e in important_events:
                date = e.get("date", "")
                desc = e.get("description", "")
                line = f"- {desc}"
                if date:
                    line = f"- **{date}**: {desc}"
                events_lines.append(line)
            parts.append("## Eventi chiave\n" + "\n".join(events_lines))

        # Themes
        themes = self.knowledge.get("themes", [])
        if themes:
            parts.append(f"## Temi ricorrenti\n{', '.join(themes[:6])}")

        # Emotional patterns
        patterns = self.knowledge.get("emotional_patterns", [])
        if patterns:
            patterns_lines = []
            for p in patterns[:3]:
                pattern = p.get("pattern", "")
                if pattern:
                    patterns_lines.append(f"- {pattern}")
            if patterns_lines:
                parts.append("## Pattern emotivi\n" + "\n".join(patterns_lines))

        return "\n\n".join(parts) if parts else "Knowledge base vuota."

    def needs_update(self, current_entries_count: int) -> bool:
        """Check if knowledge base needs updating"""
        if not self.knowledge_file.exists():
            return True
        if self.knowledge.get("entries_analyzed", 0) < current_entries_count:
            return True
        return False
