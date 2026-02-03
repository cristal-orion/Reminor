"""
Pydantic schemas for Reminor API
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, List, Any
from datetime import datetime, date


# ==================== USER MODELS ====================


class UserCreate(BaseModel):
    """Schema for user registration"""

    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    language: Optional[str] = Field("it", pattern=r"^(it|en)$")


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (no password)"""

    id: str
    email: EmailStr
    name: Optional[str] = None
    language: str = "it"
    created_at: datetime

    class Config:
        from_attributes = True


class LanguageUpdate(BaseModel):
    """Schema for updating user language preference"""

    language: str = Field(..., pattern=r"^(it|en)$")


class TokenResponse(BaseModel):
    """Schema for JWT token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ==================== JOURNAL MODELS ====================


class JournalEntryCreate(BaseModel):
    """Schema for creating a journal entry"""

    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    content: str = Field(..., min_length=1)


class JournalEntry(BaseModel):
    """Schema for journal entry response"""

    date: str
    content: str
    word_count: int
    has_emotions: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class JournalEntryPreview(BaseModel):
    """Schema for journal entry preview (list view)"""

    date: str
    preview: str
    word_count: int
    has_emotions: bool = False


# ==================== EMOTIONS MODELS ====================


class EmotionScores(BaseModel):
    """Schema for emotion scores - 8 emotions matching frontend"""

    Felice: float = Field(0.0, ge=0.0, le=1.0)
    Triste: float = Field(0.0, ge=0.0, le=1.0)
    Arrabbiato: float = Field(0.0, ge=0.0, le=1.0)
    Ansioso: float = Field(0.0, ge=0.0, le=1.0)
    Sereno: float = Field(0.0, ge=0.0, le=1.0)
    Stressato: float = Field(0.0, ge=0.0, le=1.0)
    Grato: float = Field(0.0, ge=0.0, le=1.0)
    Motivato: float = Field(0.0, ge=0.0, le=1.0)


class AnalyzeRequest(BaseModel):
    """Schema for emotion analysis request with LLM settings"""

    provider: Optional[str] = None  # groq, openai, anthropic, gemini, mistral, deepseek
    model: Optional[str] = None  # Model name (provider-specific)
    api_key: Optional[str] = None  # User's API key


class EmotionAnalysis(BaseModel):
    """Schema for emotion analysis result"""

    date: str
    emotions: EmotionScores
    dominant_emotion: Optional[str] = None
    daily_insights: Optional[Dict[str, Any]] = None
    error: Optional[bool] = None
    message: Optional[str] = None  # Error message if api_key missing


class WeeklyEmotions(BaseModel):
    """Schema for weekly emotion matrix"""

    start_date: str
    end_date: str
    days: Dict[str, Optional[EmotionScores]]


# ==================== LLM CONFIG MODELS ====================


class LLMConfigUpdate(BaseModel):
    """Schema for saving LLM configuration (input)"""

    provider: str = Field("groq", pattern=r"^(groq|openai|anthropic|gemini|mistral|deepseek)$")
    model: Optional[str] = None
    api_key: Optional[str] = None  # Plain text, will be encrypted server-side


class LLMConfigResponse(BaseModel):
    """Schema for LLM configuration response (key masked)"""

    provider: str = "groq"
    model: Optional[str] = None
    has_api_key: bool = False
    api_key_preview: Optional[str] = None  # e.g. "sk-...abc123"


# ==================== CHAT MODELS ====================


class ChatMessage(BaseModel):
    """Schema for a single chat message"""

    role: str = Field(..., pattern=r"^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    """Schema for chat request"""

    message: str = Field(..., min_length=1)
    include_context: bool = True
    context_days: int = Field(30, ge=1, le=365)
    provider: Optional[str] = None  # groq, openai, anthropic, gemini, mistral, deepseek
    model: Optional[str] = None  # Model name (provider-specific)
    api_key: Optional[str] = None  # User's API key (overrides env)


class ChatResponse(BaseModel):
    """Schema for chat response"""

    response: str
    context_used: bool = False
    emotions_detected: Optional[EmotionScores] = None


# ==================== SEARCH MODELS ====================


class SearchQuery(BaseModel):
    """Schema for search request"""

    query: str = Field(..., min_length=1)
    limit: int = Field(10, ge=1, le=50)
    semantic: bool = True


class SearchResult(BaseModel):
    """Schema for a single search result"""

    date: str
    content: str
    score: float
    title: Optional[str] = None


class SearchResponse(BaseModel):
    """Schema for search response"""

    query: str
    results: List[SearchResult]
    total: int


# ==================== STATS MODELS ====================


class DailyWordCount(BaseModel):
    """Schema for daily word count"""

    date: str
    words: int


class JournalStats(BaseModel):
    """Schema for journal statistics"""

    total_entries: int
    total_words: int
    average_words: int
    current_streak: int
    longest_streak: int
    first_entry: Optional[str] = None
    last_entry: Optional[str] = None
    weekly_activity: Optional[List[bool]] = None  # Last 7 days activity (Mon-Sun)
    # Extended stats for dashboard
    daily_words: Optional[Dict[str, int]] = None  # Last 90 days: date -> word_count
    recent_daily_words: Optional[List[DailyWordCount]] = (
        None  # Last 14 days for bar chart
    )
    emotion_averages: Optional[Dict[str, float]] = None  # Average emotion scores
    writing_hours: Optional[Dict[int, int]] = None  # Hour -> entry count (0-23)
    writing_trend: Optional[float] = None  # Percentage change vs previous period


class TopTopic(BaseModel):
    """Schema for top topic"""

    topic: str
    count: int


class StatsResponse(BaseModel):
    """Schema for stats dashboard"""

    stats: JournalStats
    top_topics: List[TopTopic]
    ai_summary: Optional[str] = None
    emotion_trends: Optional[Dict[str, List[float]]] = None


# ==================== BACKUP MODELS ====================


class BackupRequest(BaseModel):
    """Schema for backup request"""

    include_emotions: bool = True
    format: str = Field("json", pattern=r"^(json|zip|mv2)$")


class BackupResponse(BaseModel):
    """Schema for backup response"""

    download_url: str
    expires_at: datetime
    size_bytes: int
    format: str


# ==================== IMPORT/UPLOAD MODELS ====================


class ImportedFile(BaseModel):
    """Schema for a single imported file result"""

    filename: str
    date: str
    word_count: int
    status: str  # "success", "error", "skipped"
    error_message: Optional[str] = None


class ImportResponse(BaseModel):
    """Schema for bulk import response"""

    total_files: int
    imported: int
    skipped: int
    errors: int
    files: List[ImportedFile]
    vectorization_status: str  # "completed", "pending", "error"


class ImportTextRequest(BaseModel):
    """Schema for importing text content directly"""

    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    content: str = Field(..., min_length=1)
    filename: Optional[str] = None


class BulkImportRequest(BaseModel):
    """Schema for bulk text import"""

    entries: List[ImportTextRequest]
    rebuild_vectors: bool = True
