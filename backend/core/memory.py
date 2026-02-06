"""
Memory Manager for Reminor Backend
Wraps MemvidMemory for multi-user support with encryption
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Import the existing memvid memory system
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from memvid_memory import MemvidMemory

# Import knowledge extractor
from .knowledge import KnowledgeExtractor


class MemoryManager:
    """
    Multi-user memory manager.
    Each user gets their own encrypted .mv2 file.
    """

    def __init__(self, data_dir: Path):
        """
        Initialize the memory manager.

        Args:
            data_dir: Base directory for user data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Cache of active user memories
        self._user_memories: Dict[str, MemvidMemory] = {}

    def get_user_dir(self, user_id: str) -> Path:
        """Get the data directory for a specific user"""
        user_dir = self.data_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def get_user_memory(self, user_id: str) -> MemvidMemory:
        """
        Get or create memory instance for a user.

        Args:
            user_id: Unique user identifier

        Returns:
            MemvidMemory instance for the user
        """
        if user_id not in self._user_memories:
            user_dir = self.get_user_dir(user_id)
            journal_dir = user_dir / "journal"
            journal_dir.mkdir(exist_ok=True)

            memvid_file = user_dir / "memory.mv2"

            self._user_memories[user_id] = MemvidMemory(
                journal_dir=journal_dir,
                memvid_file=memvid_file
            )

        return self._user_memories[user_id]

    def close_user_memory(self, user_id: str):
        """Close and remove a user's memory from cache"""
        if user_id in self._user_memories:
            self._user_memories[user_id].close()
            del self._user_memories[user_id]

    def close_all(self):
        """Close all active memory instances"""
        for user_id in list(self._user_memories.keys()):
            self.close_user_memory(user_id)

    # ==================== JOURNAL OPERATIONS ====================

    def add_entry(self, user_id: str, date: str, content: str) -> bool:
        """Add a journal entry for a user"""
        memory = self.get_user_memory(user_id)

        # Also save to .txt file for compatibility
        user_dir = self.get_user_dir(user_id)
        journal_dir = user_dir / "journal"
        file_path = journal_dir / f"{date}.txt"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"Error saving journal file: {e}")

        return memory.add_entry(date, content)

    def get_entry(self, user_id: str, date: str) -> Optional[str]:
        """Get a journal entry for a specific date"""
        memory = self.get_user_memory(user_id)
        return memory.entries.get(date)

    def get_entries(self, user_id: str, start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> Dict[str, str]:
        """Get journal entries within a date range"""
        memory = self.get_user_memory(user_id)
        entries = memory.entries

        if start_date:
            entries = {k: v for k, v in entries.items() if k >= start_date}
        if end_date:
            entries = {k: v for k, v in entries.items() if k <= end_date}

        return entries

    def search(self, user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search user's journal entries"""
        memory = self.get_user_memory(user_id)
        return memory.search(query, limit=limit)

    def get_context(self, user_id: str, query: Optional[str] = None,
                    num_entries: int = 10) -> str:
        """Get rich context for chatbot"""
        memory = self.get_user_memory(user_id)
        return memory.get_rich_context(query=query, num_entries=num_entries)

    # ==================== EMOTIONS OPERATIONS ====================

    def save_emotions(self, user_id: str, date: str, emotions: Dict[str, float],
                      daily_insights: Optional[Dict] = None) -> bool:
        """Save emotions for a date"""
        memory = self.get_user_memory(user_id)
        return memory.save_emotions(date, emotions, daily_insights)

    def get_emotions(self, user_id: str, date: str) -> Optional[Dict[str, float]]:
        """Get emotions for a specific date"""
        memory = self.get_user_memory(user_id)
        return memory.get_emotions(date)

    def get_weekly_emotions(self, user_id: str, dates: List[str]) -> Dict[str, Dict[str, float]]:
        """Get emotions for a week"""
        memory = self.get_user_memory(user_id)
        return memory.get_emotions_for_week(dates)

    def get_full_analysis(self, user_id: str, date: str) -> Optional[Dict[str, Any]]:
        """Get full analysis (emotions + insights) for a date"""
        memory = self.get_user_memory(user_id)
        return memory.get_full_analysis(date)

    # ==================== STATS ====================

    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get journal statistics for a user"""
        memory = self.get_user_memory(user_id)
        entries = memory.entries

        if not entries:
            return {
                "total_entries": 0,
                "total_words": 0,
                "average_words": 0,
                "current_streak": 0,
                "longest_streak": 0,
                "first_entry": None,
                "last_entry": None
            }

        # Calculate stats
        total_entries = len(entries)
        total_words = sum(len(content.split()) for content in entries.values())
        average_words = total_words // max(total_entries, 1)

        # Calculate streak
        dates = sorted(entries.keys(), reverse=True)
        current_streak = 0
        today = datetime.now().strftime("%Y-%m-%d")

        from datetime import timedelta
        check_date = datetime.now()

        for i in range(len(dates)):
            expected = (check_date - timedelta(days=i)).strftime("%Y-%m-%d")
            if expected in entries:
                current_streak += 1
            else:
                break

        return {
            "total_entries": total_entries,
            "total_words": total_words,
            "average_words": average_words,
            "current_streak": current_streak,
            "longest_streak": current_streak,  # TODO: Calculate properly
            "first_entry": min(dates) if dates else None,
            "last_entry": max(dates) if dates else None
        }

    # ==================== BACKUP ====================

    def get_backup_data(self, user_id: str, include_emotions: bool = True) -> Dict[str, Any]:
        """Get all user data for backup"""
        memory = self.get_user_memory(user_id)

        data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "entries": memory.entries
        }

        if include_emotions:
            emotions = {}
            for date in memory.entries.keys():
                emotion = memory.get_emotions(date)
                if emotion:
                    emotions[date] = emotion
            data["emotions"] = emotions

        return data

    def get_mv2_path(self, user_id: str) -> Path:
        """Get path to user's .mv2 file for direct download"""
        user_dir = self.get_user_dir(user_id)
        return user_dir / "memory.mv2"

    # ==================== IMPORT / UPLOAD ====================

    def import_entries(self, user_id: str, entries: List[Dict[str, str]],
                       rebuild_vectors: bool = True, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Bulk import journal entries for a user.

        Args:
            user_id: User ID
            entries: List of dicts with 'date', 'content', optional 'filename'
            rebuild_vectors: Whether to rebuild vector embeddings after import
            api_key: Optional user API key for knowledge extraction

        Returns:
            Dict with import results
        """
        import re

        user_dir = self.get_user_dir(user_id)
        journal_dir = user_dir / "journal"
        journal_dir.mkdir(exist_ok=True)

        results = {
            "total_files": len(entries),
            "imported": 0,
            "skipped": 0,
            "errors": 0,
            "files": [],
            "vectorization_status": "pending"
        }

        imported_dates = []

        for entry in entries:
            date_str = entry.get('date', '')
            content = entry.get('content', '')
            filename = entry.get('filename', f"{date_str}.txt")

            file_result = {
                "filename": filename,
                "date": date_str,
                "word_count": 0,
                "status": "pending",
                "error_message": None
            }

            # Validate date format
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                file_result["status"] = "error"
                file_result["error_message"] = f"Invalid date format: {date_str}"
                results["errors"] += 1
                results["files"].append(file_result)
                continue

            # Skip empty content
            if not content or len(content.strip()) < 10:
                file_result["status"] = "skipped"
                file_result["error_message"] = "Content too short (min 10 chars)"
                results["skipped"] += 1
                results["files"].append(file_result)
                continue

            try:
                # Save to .txt file
                file_path = journal_dir / f"{date_str}.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                file_result["word_count"] = len(content.split())
                file_result["status"] = "success"
                results["imported"] += 1
                imported_dates.append(date_str)

            except Exception as e:
                file_result["status"] = "error"
                file_result["error_message"] = str(e)
                results["errors"] += 1

            results["files"].append(file_result)

        # Rebuild Memvid index and vectors if requested
        if rebuild_vectors and imported_dates:
            try:
                self._rebuild_user_memory(user_id, api_key=api_key)
                results["vectorization_status"] = "completed"
            except Exception as e:
                results["vectorization_status"] = f"error: {str(e)}"

        return results

    def _rebuild_user_memory(self, user_id: str, extract_knowledge: bool = True, api_key: Optional[str] = None):
        """
        Rebuild Memvid index and embeddings for a user.
        Called after bulk import.

        Args:
            user_id: User ID
            extract_knowledge: Whether to also extract/update knowledge base
            api_key: Optional user API key for knowledge extraction
        """
        # Close existing memory instance
        self.close_user_memory(user_id)

        user_dir = self.get_user_dir(user_id)
        journal_dir = user_dir / "journal"
        memvid_file = user_dir / "memory.mv2"
        embeddings_file = user_dir / "memory.npz"

        # Delete existing files to force rebuild
        if memvid_file.exists():
            memvid_file.unlink()
        if embeddings_file.exists():
            embeddings_file.unlink()

        # Create new memory instance (will auto-index all .txt files)
        self._user_memories[user_id] = MemvidMemory(
            journal_dir=journal_dir,
            memvid_file=memvid_file
        )

        print(f"Memory rebuilt for user {user_id}")

        # Extract knowledge base from diary entries
        if extract_knowledge:
            self._extract_user_knowledge(user_id, api_key=api_key)

    def _extract_user_knowledge(self, user_id: str, api_key: Optional[str] = None):
        """
        Extract structured knowledge from user's diary entries.
        Creates/updates the user_knowledge.json file.

        Args:
            user_id: User ID
            api_key: Optional user API key. Falls back to env var.
        """
        user_dir = self.get_user_dir(user_id)
        try:
            print(f"[INFO] Extracting knowledge base for user {user_id}...")
            extractor = KnowledgeExtractor(user_dir, api_key=api_key)
            extractor.extract_knowledge()
            print(f"[OK] Knowledge base updated for user {user_id}")
        except Exception as e:
            print(f"[WARNING] Knowledge extraction failed: {e}")

    def get_user_knowledge(self, user_id: str) -> str:
        """
        Get formatted knowledge base for a user (for chat prompt).

        Returns:
            Formatted knowledge string for inclusion in prompt
        """
        user_dir = self.get_user_dir(user_id)
        try:
            extractor = KnowledgeExtractor(user_dir)
            return extractor.get_knowledge_for_prompt()
        except Exception as e:
            print(f"[WARNING] Error loading knowledge: {e}")
            return ""

    def get_user_name_from_knowledge(self, user_id: str) -> str:
        """
        Get user's name from knowledge base (if extracted).

        Returns:
            User's name or empty string if not found
        """
        user_dir = self.get_user_dir(user_id)
        try:
            extractor = KnowledgeExtractor(user_dir)
            # Look for the author in the people list
            people = extractor.knowledge.get("people", [])
            for person in people:
                if person.get("relationship") == "autore":
                    return person.get("name", "")
            return ""
        except Exception as e:
            return ""

    def parse_filename_date(self, filename: str) -> Optional[str]:
        """
        Extract date from filename.
        Supports formats:
        - 2024-01-15.txt
        - 2024_01_15.txt
        - 15-01-2024.txt
        - diario_2024-01-15.txt

        Returns:
            Date in YYYY-MM-DD format or None
        """
        import re

        # Try YYYY-MM-DD or YYYY_MM_DD
        match = re.search(r'(\d{4})[-_](\d{2})[-_](\d{2})', filename)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

        # Try DD-MM-YYYY or DD_MM_YYYY
        match = re.search(r'(\d{2})[-_](\d{2})[-_](\d{4})', filename)
        if match:
            return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"

        return None

    def import_uploaded_files(self, user_id: str, files: List[tuple],
                               rebuild_vectors: bool = True, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Import uploaded files (from FastAPI UploadFile).

        Args:
            user_id: User ID
            files: List of (filename, content_bytes) tuples
            rebuild_vectors: Whether to rebuild vectors after import
            api_key: Optional user API key for knowledge extraction

        Returns:
            Import results dict
        """
        entries = []

        for filename, content_bytes in files:
            # Try to decode content
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = content_bytes.decode('latin-1')
                except:
                    content = content_bytes.decode('utf-8', errors='ignore')

            # Extract date from filename
            date_str = self.parse_filename_date(filename)

            if not date_str:
                # Use today's date if can't parse
                date_str = datetime.now().strftime("%Y-%m-%d")

            entries.append({
                "date": date_str,
                "content": content,
                "filename": filename
            })

        return self.import_entries(user_id, entries, rebuild_vectors, api_key=api_key)
