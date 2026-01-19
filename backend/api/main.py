"""
FastAPI Main Application for Reminor Backend
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)
print(
    f"[ENV] Loaded from {env_path}, GROQ_API_KEY: {'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'}"
)
from datetime import datetime
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
import io
import zipfile

# Add parent paths for imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.memory import MemoryManager
from core.chat import ChatService
from core.emotions import EmotionsAnalyzer
from core.auth import get_current_user, CurrentUser
from models.schemas import (
    JournalEntry,
    JournalEntryCreate,
    JournalEntryPreview,
    EmotionAnalysis,
    EmotionScores,
    ChatRequest,
    ChatResponse,
    SearchQuery,
    SearchResponse,
    SearchResult,
    JournalStats,
    StatsResponse,
    DailyWordCount,
    ImportResponse,
    ImportedFile,
    BulkImportRequest,
)

# Import auth routes
from api.auth_routes import router as auth_router

# Global instances
DATA_DIR = Path(__file__).parent.parent.parent / "data"
memory_manager: Optional[MemoryManager] = None
chat_service: Optional[ChatService] = None
emotions_analyzer: Optional[EmotionsAnalyzer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global memory_manager, chat_service, emotions_analyzer

    # Startup
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    memory_manager = MemoryManager(DATA_DIR)
    chat_service = ChatService(memory_manager)
    emotions_analyzer = EmotionsAnalyzer(DATA_DIR)

    print(f"Reminor Backend started - Data dir: {DATA_DIR}")

    yield

    # Shutdown
    if memory_manager:
        memory_manager.close_all()
    print("Reminor Backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Reminor API",
    description="Backend API for Reminor - AI-Powered Personal Diary",
    version="2.0.0",
    lifespan=lifespan,
)

# Include auth router
app.include_router(auth_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency getters
def get_memory_manager() -> MemoryManager:
    if memory_manager is None:
        raise HTTPException(status_code=500, detail="Memory manager not initialized")
    return memory_manager


def get_chat_service() -> ChatService:
    if chat_service is None:
        raise HTTPException(status_code=500, detail="Chat service not initialized")
    return chat_service


def get_emotions_analyzer() -> EmotionsAnalyzer:
    if emotions_analyzer is None:
        raise HTTPException(status_code=500, detail="Emotions analyzer not initialized")
    return emotions_analyzer


# ==================== HEALTH CHECK ====================


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0-auth",
    }


# ==================== JOURNAL ENDPOINTS ====================


@app.post("/journal/entries", response_model=JournalEntry)
async def create_entry(
    entry: JournalEntryCreate,
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """Create or update a journal entry"""
    user_id = current_user.id
    success = mm.add_entry(user_id, entry.date, entry.content)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to save entry")

    return JournalEntry(
        date=entry.date,
        content=entry.content,
        word_count=len(entry.content.split()),
        has_emotions=False,
        created_at=datetime.now(),
    )


@app.get("/journal/entries/{date}", response_model=JournalEntry)
async def get_entry(
    date: str,
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """Get a journal entry by date"""
    user_id = current_user.id
    content = mm.get_entry(user_id, date)

    if content is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    emotions = mm.get_emotions(user_id, date)

    return JournalEntry(
        date=date,
        content=content,
        word_count=len(content.split()),
        has_emotions=emotions is not None,
    )


@app.get("/journal/entries", response_model=List[JournalEntryPreview])
async def list_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """List journal entries with previews"""
    user_id = current_user.id
    entries = mm.get_entries(user_id, start_date, end_date)

    result = []
    for date, content in sorted(entries.items(), reverse=True)[:limit]:
        preview = content[:100] + "..." if len(content) > 100 else content
        emotions = mm.get_emotions(user_id, date)

        result.append(
            JournalEntryPreview(
                date=date,
                preview=preview,
                word_count=len(content.split()),
                has_emotions=emotions is not None,
            )
        )

    return result


# ==================== SEARCH ENDPOINTS ====================


@app.post("/journal/search", response_model=SearchResponse)
async def search_entries(
    query: SearchQuery,
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """Search journal entries"""
    user_id = current_user.id
    results = mm.search(user_id, query.query, limit=query.limit)

    return SearchResponse(
        query=query.query,
        results=[
            SearchResult(
                date=r.get("date", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.0),
                title=r.get("title"),
            )
            for r in results
        ],
        total=len(results),
    )


# ==================== EMOTIONS ENDPOINTS ====================


@app.post("/journal/entries/{date}/analyze", response_model=EmotionAnalysis)
async def analyze_entry(
    date: str,
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
    ea: EmotionsAnalyzer = Depends(get_emotions_analyzer),
):
    """Analyze emotions in a journal entry"""
    user_id = current_user.id
    content = mm.get_entry(user_id, date)

    if content is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    # Analyze emotions
    analysis = ea.analyze_full(user_id, content)
    emotions = analysis.get("emotions", {})

    # Save to memory
    mm.save_emotions(user_id, date, emotions, analysis.get("daily_insights"))

    # Get dominant emotion
    dominant = ea.get_dominant_emotion(emotions)

    return EmotionAnalysis(
        date=date,
        emotions=EmotionScores(
            Felice=emotions.get("felice", 0.0),
            Triste=emotions.get("triste", 0.0),
            Arrabbiato=emotions.get("arrabbiato", 0.0),
            Ansioso=emotions.get("ansioso", 0.0),
            Sereno=emotions.get("sereno", 0.0),
            Stressato=emotions.get("stressato", 0.0),
            Grato=emotions.get("grato", 0.0),
            Motivato=emotions.get("motivato", 0.0),
        ),
        dominant_emotion=dominant,
        daily_insights=analysis.get("daily_insights"),
    )


@app.get(
    "/journal/entries/{date}/emotions",
    response_model=Optional[EmotionAnalysis],
)
async def get_emotions(
    date: str,
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """Get emotions for a specific date"""
    user_id = current_user.id
    emotions = mm.get_emotions(user_id, date)

    if emotions is None:
        return None

    return EmotionAnalysis(
        date=date,
        emotions=EmotionScores(
            Felice=emotions.get("felice", 0.0),
            Triste=emotions.get("triste", 0.0),
            Arrabbiato=emotions.get("arrabbiato", 0.0),
            Ansioso=emotions.get("ansioso", 0.0),
            Sereno=emotions.get("sereno", 0.0),
            Stressato=emotions.get("stressato", 0.0),
            Grato=emotions.get("grato", 0.0),
            Motivato=emotions.get("motivato", 0.0),
        ),
    )


@app.get("/journal/emotions/weekly")
async def get_weekly_emotions(
    start_date: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """
    Get emotions for a week (7 days starting from Monday of the given week).
    If start_date is provided, returns the week containing that date.
    Otherwise returns the current week.
    Returns dict with date -> emotions mapping including energy_level.
    """
    from datetime import timedelta

    user_id = current_user.id

    if start_date:
        try:
            base_date = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            base_date = datetime.now()
    else:
        base_date = datetime.now()

    # Find Monday of the week
    day_of_week = base_date.weekday()  # Monday = 0
    monday = base_date - timedelta(days=day_of_week)

    dates = []
    for i in range(7):
        d = monday + timedelta(days=i)
        dates.append(d.strftime("%Y-%m-%d"))

    # Get full analysis (emotions + insights) for all dates
    result = {}
    for date in dates:
        try:
            analysis = mm.get_full_analysis(user_id, date)
            if analysis and analysis.get("emotions"):
                emotions = analysis["emotions"]
                insights = analysis.get("daily_insights", {}) or {}
                energy_level = insights.get("energy_level", 0.5) if insights else 0.5

                result[date] = {
                    "emotions": emotions,
                    "dominant": max(emotions, key=emotions.get) if emotions else None,
                    "intensity": sum(emotions.values()) / len(emotions)
                    if emotions
                    else 0,
                    "energy_level": energy_level,
                }
            else:
                result[date] = None
        except Exception as e:
            print(f"Errore recupero emozioni per {date}: {e}")
            result[date] = None

    return {"weekly_emotions": result, "dates": dates}


# ==================== CHAT ENDPOINTS ====================


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    cs: ChatService = Depends(get_chat_service),
):
    """Send a chat message with multi-provider LLM support"""
    user_id = current_user.id
    try:
        result = await cs.chat(
            user_id=user_id,
            message=request.message,
            include_context=request.include_context,
            provider=request.provider or "groq",
            model=request.model,
            user_api_key=request.api_key,
        )

        if result.get("error"):
            print(f"[CHAT ERROR] {result['response']}")
            raise HTTPException(status_code=500, detail=result["response"])
    except Exception as e:
        print(f"[CHAT EXCEPTION] {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        response=result["response"], context_used=result.get("context_used", False)
    )


@app.delete("/chat/history")
async def clear_chat_history(
    current_user: CurrentUser = Depends(get_current_user),
    cs: ChatService = Depends(get_chat_service),
):
    """Clear chat history for current user"""
    user_id = current_user.id
    cs.clear_conversation(user_id)
    return {"message": "Chat history cleared"}


# ==================== STATS ENDPOINTS ====================


@app.get("/journal/stats", response_model=StatsResponse)
async def get_stats(
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """Get journal statistics with extended data for dashboard"""
    from datetime import timedelta

    user_id = current_user.id
    stats = mm.get_stats(user_id)
    memory = mm.get_user_memory(user_id)
    today = datetime.now()

    # Calculate weekly activity (last 7 days)
    weekly_activity = []
    for i in range(6, -1, -1):  # From 6 days ago to today
        d = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        has_entry = date_str in memory.entries
        weekly_activity.append(has_entry)

    # Calculate daily words for last 90 days (heatmap)
    daily_words = {}
    for i in range(89, -1, -1):
        d = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        if date_str in memory.entries:
            daily_words[date_str] = len(memory.entries[date_str].split())
        else:
            daily_words[date_str] = 0

    # Calculate recent daily words for last 14 days (bar chart)
    recent_daily_words = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        words = (
            len(memory.entries[date_str].split()) if date_str in memory.entries else 0
        )
        recent_daily_words.append(DailyWordCount(date=date_str, words=words))

    # Calculate emotion averages from all analyzed entries
    emotion_totals = {}
    emotion_counts = 0
    for date_str in memory.entries.keys():
        emotions = memory.get_emotions(date_str)
        if emotions:
            emotion_counts += 1
            for emotion, score in emotions.items():
                emotion_totals[emotion] = emotion_totals.get(emotion, 0) + score

    emotion_averages = {}
    if emotion_counts > 0:
        for emotion, total in emotion_totals.items():
            emotion_averages[emotion] = round(total / emotion_counts, 3)

    # Calculate longest streak properly
    dates = sorted(memory.entries.keys())
    longest_streak = 0
    current_run = 0
    prev_date = None

    for date_str in dates:
        try:
            current_date = datetime.strptime(date_str, "%Y-%m-%d")
            if prev_date is None:
                current_run = 1
            elif (current_date - prev_date).days == 1:
                current_run += 1
            else:
                current_run = 1
            longest_streak = max(longest_streak, current_run)
            prev_date = current_date
        except ValueError:
            continue

    # Calculate writing trend (last 7 days vs previous 7 days)
    last_7_days_words = 0
    prev_7_days_words = 0

    for i in range(7):
        d = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        if date_str in memory.entries:
            last_7_days_words += len(memory.entries[date_str].split())

    for i in range(7, 14):
        d = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        if date_str in memory.entries:
            prev_7_days_words += len(memory.entries[date_str].split())

    writing_trend = 0.0
    if prev_7_days_words > 0:
        writing_trend = (
            (last_7_days_words - prev_7_days_words) / prev_7_days_words
        ) * 100
    elif last_7_days_words > 0:
        writing_trend = 100.0  # 100% increase from zero

    # Get AI Summary from Knowledge Base for "System Profile"
    ai_summary_text = "ANALISI SISTEMA IN CORSO..."
    try:
        # Knowledge is loaded via KnowledgeExtractor usually
        # We'll check the file directly
        knowledge_file = mm.get_user_dir(user_id) / "user_knowledge.json"
        if knowledge_file.exists():
            import json

            with open(knowledge_file, "r", encoding="utf-8") as f:
                kb_data = json.load(f)
                summary = kb_data.get("summary", "")
                if summary:
                    ai_summary_text = summary
                else:
                    ai_summary_text = "NESSUN DATO PROFILO DISPONIBILE."
        else:
            # Try to trigger extraction in background if file missing?
            # For now just inform user.
            ai_summary_text = (
                "ANALISI SISTEMA NON DISPONIBILE. ATTENDERE ELABORAZIONE DATI."
            )

            # Optional: Trigger extraction if we have enough entries?
            # This might be slow for a GET request, so better leave it to a specific trigger
            # or background task.
    except Exception as e:
        print(f"Error loading summary for stats: {e}")
        ai_summary_text = "ERRORE LETTURA SISTEMA."

    return StatsResponse(
        stats=JournalStats(
            total_entries=stats.get("total_entries", 0),
            total_words=stats.get("total_words", 0),
            average_words=stats.get("average_words", 0),
            current_streak=stats.get("current_streak", 0),
            longest_streak=longest_streak,
            first_entry=stats.get("first_entry"),
            last_entry=stats.get("last_entry"),
            weekly_activity=weekly_activity,
            daily_words=daily_words,
            recent_daily_words=recent_daily_words,
            emotion_averages=emotion_averages,
            writing_hours=None,  # TODO: Would need file timestamps
            writing_trend=round(writing_trend, 1),
        ),
        top_topics=[],
        ai_summary=ai_summary_text,
    )


@app.post("/journal/knowledge/analyze")
async def trigger_knowledge_extraction(
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """
    Manually trigger AI knowledge extraction for the user profile.
    This analyzes all diary entries to build user_knowledge.json.
    """
    user_id = current_user.id
    try:
        mm._extract_user_knowledge(user_id)
        return {"status": "success", "message": "Knowledge extraction completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


# ==================== IMPORT/UPLOAD ENDPOINTS ====================


@app.post("/journal/import/files", response_model=ImportResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    rebuild_vectors: bool = Query(True),
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """
    Upload multiple diary files (.txt) to import.
    Files should be named with dates (e.g., 2024-01-15.txt, 15-01-2024.txt)
    The system will:
    1. Parse dates from filenames
    2. Save files to user's journal
    3. Rebuild Memvid index
    4. Generate vector embeddings for semantic search
    """
    user_id = current_user.id

    # Read all uploaded files
    file_data = []
    for file in files:
        content = await file.read()
        file_data.append((file.filename, content))

    # Import files
    result = mm.import_uploaded_files(user_id, file_data, rebuild_vectors)

    return ImportResponse(
        total_files=result["total_files"],
        imported=result["imported"],
        skipped=result["skipped"],
        errors=result["errors"],
        files=[
            ImportedFile(
                filename=f["filename"],
                date=f["date"],
                word_count=f["word_count"],
                status=f["status"],
                error_message=f["error_message"],
            )
            for f in result["files"]
        ],
        vectorization_status=result["vectorization_status"],
    )


@app.post("/journal/import/bulk", response_model=ImportResponse)
async def bulk_import(
    request: BulkImportRequest,
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """
    Bulk import journal entries via JSON.
    Useful for importing from other apps or formats.

    Request body:
    {
        "entries": [
            {"date": "2024-01-15", "content": "Today was..."},
            {"date": "2024-01-16", "content": "Another day..."}
        ],
        "rebuild_vectors": true
    }
    """
    user_id = current_user.id
    entries = [
        {
            "date": e.date,
            "content": e.content,
            "filename": e.filename or f"{e.date}.txt",
        }
        for e in request.entries
    ]

    result = mm.import_entries(user_id, entries, request.rebuild_vectors)

    return ImportResponse(
        total_files=result["total_files"],
        imported=result["imported"],
        skipped=result["skipped"],
        errors=result["errors"],
        files=[
            ImportedFile(
                filename=f["filename"],
                date=f["date"],
                word_count=f["word_count"],
                status=f["status"],
                error_message=f["error_message"],
            )
            for f in result["files"]
        ],
        vectorization_status=result["vectorization_status"],
    )


@app.post("/journal/rebuild-vectors")
async def rebuild_vectors(
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """
    Manually trigger rebuild of Memvid index and vector embeddings.
    Useful after manual file changes or to fix corrupted index.
    """
    user_id = current_user.id
    try:
        mm._rebuild_user_memory(user_id)
        memory = mm.get_user_memory(user_id)

        return {
            "status": "success",
            "message": "Memory rebuilt successfully",
            "entries_indexed": len(memory.entries),
            "embeddings_generated": len(memory.embeddings)
            if hasattr(memory, "embeddings")
            else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")


# ==================== BACKUP/DOWNLOAD ENDPOINTS ====================


@app.get("/journal/backup/json")
async def download_backup_json(
    include_emotions: bool = Query(True),
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """
    Download complete backup as JSON.
    Includes all entries and optionally emotions data.
    """
    import json

    user_id = current_user.id
    backup_data = mm.get_backup_data(user_id, include_emotions)

    # Convert to JSON bytes
    json_content = json.dumps(backup_data, indent=2, ensure_ascii=False)
    json_bytes = json_content.encode("utf-8")

    # Create streaming response
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=reminor_backup_{user_id}_{datetime.now().strftime('%Y%m%d')}.json"
        },
    )


@app.get("/journal/backup/mv2")
async def download_backup_mv2(
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """
    Download raw Memvid .mv2 file.
    This contains the complete memory with embeddings.
    Can be used to restore full memory state.
    """
    user_id = current_user.id
    mv2_path = mm.get_mv2_path(user_id)

    if not mv2_path.exists():
        raise HTTPException(
            status_code=404, detail="Memory file not found. No entries saved yet."
        )

    return FileResponse(
        path=str(mv2_path),
        media_type="application/octet-stream",
        filename=f"reminor_memory_{user_id}_{datetime.now().strftime('%Y%m%d')}.mv2",
    )


@app.get("/journal/backup/zip")
async def download_backup_zip(
    include_mv2: bool = Query(True),
    current_user: CurrentUser = Depends(get_current_user),
    mm: MemoryManager = Depends(get_memory_manager),
):
    """
    Download complete backup as ZIP archive.
    Includes:
    - All .txt journal files
    - emotions.json with emotion data
    - Optionally the .mv2 memory file
    """
    import json

    user_id = current_user.id
    user_dir = mm.get_user_dir(user_id)
    journal_dir = user_dir / "journal"

    # Collect data before closing memory
    memory = mm.get_user_memory(user_id)
    entries_count = len(memory.entries)
    emotions_data = {}
    for date in memory.entries.keys():
        emotions = memory.get_emotions(date)
        if emotions:
            emotions_data[date] = emotions

    # Prepare metadata
    metadata = {
        "exported_at": datetime.now().isoformat(),
        "version": "1.0",
        "total_entries": entries_count,
        "user_id": user_id,
        "mv2_included": False,
    }

    # Try to read mv2 file (close memory first to release lock on Windows)
    mv2_content = None
    if include_mv2:
        mv2_path = mm.get_mv2_path(user_id)
        if mv2_path.exists():
            try:
                mm.close_user_memory(user_id)
                mv2_content = mv2_path.read_bytes()
                metadata["mv2_included"] = True
            except Exception as e:
                print(f"[WARNING] Could not read mv2 file: {e}")
                metadata["mv2_note"] = (
                    "File locked - can be regenerated from diary entries"
                )

    # Read knowledge base
    knowledge_content = None
    knowledge_path = user_dir / "user_knowledge.json"
    if knowledge_path.exists():
        try:
            knowledge_content = knowledge_path.read_text(encoding="utf-8")
            metadata["knowledge_included"] = True
        except Exception as e:
            print(f"[WARNING] Could not read knowledge file: {e}")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add all .txt files from journal directory
        if journal_dir.exists():
            for txt_file in journal_dir.glob("*.txt"):
                zf.write(txt_file, f"journal/{txt_file.name}")

        # Add emotions data
        if emotions_data:
            zf.writestr(
                "emotions.json", json.dumps(emotions_data, indent=2, ensure_ascii=False)
            )

        # Add mv2 if available
        if mv2_content:
            zf.writestr("memory.mv2", mv2_content)

        # Add knowledge base if available
        if knowledge_content:
            zf.writestr("user_knowledge.json", knowledge_content)

        # Add metadata last (so it includes all status info)
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=reminor_backup_{user_id}_{datetime.now().strftime('%Y%m%d')}.zip"
        },
    )


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
