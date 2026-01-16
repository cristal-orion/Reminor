"""
Emotions Analyzer Service for Reminor Backend
Wraps EnhancedEmotionsAnalyzer for multi-user support
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import the existing emotions analyzer
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from enhanced_emotions_analyzer import EnhancedEmotionsAnalyzer as BaseAnalyzer
    HAS_ANALYZER = True
except ImportError:
    HAS_ANALYZER = False
    print("Warning: enhanced_emotions_analyzer not available")


class EmotionsAnalyzer:
    """
    Multi-user emotions analyzer.
    Each user gets their own analyzer instance.
    """

    # Standard emotions list
    EMOTIONS = [
        "felice", "triste", "arrabbiato", "ansioso",
        "sereno", "stressato", "grato", "motivato"
    ]

    def __init__(self, data_dir: Path):
        """
        Initialize emotions analyzer.

        Args:
            data_dir: Base directory for user data
        """
        self.data_dir = Path(data_dir)
        self._user_analyzers: Dict[str, Any] = {}

    def get_user_analyzer(self, user_id: str) -> Optional[Any]:
        """
        Get or create analyzer for a user.

        Args:
            user_id: User ID

        Returns:
            Analyzer instance or None if not available
        """
        if not HAS_ANALYZER:
            return None

        if user_id not in self._user_analyzers:
            user_dir = self.data_dir / user_id / "journal"
            user_dir.mkdir(parents=True, exist_ok=True)
            self._user_analyzers[user_id] = BaseAnalyzer(user_dir)

        return self._user_analyzers[user_id]

    def analyze_text(self, user_id: str, text: str) -> Dict[str, float]:
        """
        Analyze emotions in text.

        Args:
            user_id: User ID
            text: Text to analyze

        Returns:
            Dict of emotion -> score (0-1)
        """
        analyzer = self.get_user_analyzer(user_id)

        if not analyzer:
            return self._simple_analysis(text)

        try:
            return analyzer.analyze_emotions_from_text(text)
        except Exception as e:
            print(f"Error analyzing emotions: {e}")
            return self._simple_analysis(text)

    def analyze_full(self, user_id: str, text: str) -> Dict[str, Any]:
        """
        Full analysis including emotions and profile updates.

        Args:
            user_id: User ID
            text: Text to analyze

        Returns:
            Dict with emotions, daily_insights, profile_updates
        """
        analyzer = self.get_user_analyzer(user_id)

        if not analyzer:
            return {
                "emotions": self._simple_analysis(text),
                "daily_insights": None,
                "profile_updates": None
            }

        try:
            return analyzer.analyze_full_entry(text)
        except Exception as e:
            print(f"Error in full analysis: {e}")
            return {
                "emotions": self._simple_analysis(text),
                "daily_insights": None,
                "profile_updates": None
            }

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get psychological profile for a user.

        Args:
            user_id: User ID

        Returns:
            Profile data dict
        """
        analyzer = self.get_user_analyzer(user_id)

        if not analyzer:
            return {}

        return analyzer.profile_data

    def _simple_analysis(self, text: str) -> Dict[str, float]:
        """
        Simple keyword-based emotion analysis as fallback.

        Args:
            text: Text to analyze

        Returns:
            Dict of emotion -> score
        """
        text_lower = text.lower()
        emotions = {emotion: 0.0 for emotion in self.EMOTIONS}

        # Simple keyword matching
        keywords = {
            "felice": ["felice", "contento", "gioia", "bene", "fantastico", "ottimo"],
            "triste": ["triste", "male", "depresso", "dolore", "piango", "sconforto"],
            "arrabbiato": ["arrabbiato", "furioso", "rabbia", "odio", "irritato"],
            "ansioso": ["ansioso", "ansia", "preoccupato", "nervoso", "agitato"],
            "sereno": ["sereno", "calmo", "tranquillo", "pace", "rilassato"],
            "stressato": ["stressato", "stress", "pressione", "sovraccarico"],
            "grato": ["grato", "grazie", "riconoscente", "apprezzo", "fortuna"],
            "motivato": ["motivato", "determinato", "energia", "voglia", "obiettivo"]
        }

        for emotion, words in keywords.items():
            for word in words:
                if word in text_lower:
                    emotions[emotion] = min(emotions[emotion] + 0.3, 1.0)

        return emotions

    def get_dominant_emotion(self, emotions: Dict[str, float]) -> Optional[str]:
        """
        Get the dominant emotion from scores.

        Args:
            emotions: Dict of emotion -> score

        Returns:
            Name of dominant emotion or None
        """
        if not emotions:
            return None

        max_emotion = max(emotions.items(), key=lambda x: x[1])

        if max_emotion[1] > 0.2:
            return max_emotion[0]

        return None
