"""
FastAPI Main Application for Reminor Backend
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)
print(f"[ENV] Loaded from {env_path}, GROQ_API_KEY: {'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")
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
from models.schemas import (
    JournalEntry, JournalEntryCreate, JournalEntryPreview,
    EmotionAnalysis, EmotionScores,
    ChatRequest, ChatResponse,
    SearchQuery, SearchResponse, SearchResult,
    JournalStats, StatsResponse,
    ImportResponse, ImportedFile, BulkImportRequest
)

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
    version="1.0.0",
    lifespan=lifespan
)

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
        "version": "1.0.0"
    }


# ==================== JOURNAL ENDPOINTS ====================

@app.post("/journal/{user_id}/entries", response_model=JournalEntry)
async def create_entry(
    user_id: str,
    entry: JournalEntryCreate,
    mm: MemoryManager = Depends(get_memory_manager)
):
    """Create or update a journal entry"""
    success = mm.add_entry(user_id, entry.date, entry.content)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to save entry")

    return JournalEntry(
        date=entry.date,
        content=entry.content,
        word_count=len(entry.content.split()),
        has_emotions=False,
        created_at=datetime.now()
    )


@app.get("/journal/{user_id}/entries/{date}", response_model=JournalEntry)
async def get_entry(
    user_id: str,
    date: str,
    mm: MemoryManager = Depends(get_memory_manager)
):
    """Get a journal entry by date"""
    content = mm.get_entry(user_id, date)

    if content is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    emotions = mm.get_emotions(user_id, date)

    return JournalEntry(
        date=date,
        content=content,
        word_count=len(content.split()),
        has_emotions=emotions is not None
    )


@app.get("/journal/{user_id}/entries", response_model=List[JournalEntryPreview])
async def list_entries(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    mm: MemoryManager = Depends(get_memory_manager)
):
    """List journal entries with previews"""
    entries = mm.get_entries(user_id, start_date, end_date)

    result = []
    for date, content in sorted(entries.items(), reverse=True)[:limit]:
        preview = content[:100] + "..." if len(content) > 100 else content
        emotions = mm.get_emotions(user_id, date)

        result.append(JournalEntryPreview(
            date=date,
            preview=preview,
            word_count=len(content.split()),
            has_emotions=emotions is not None
        ))

    return result


# ==================== SEARCH ENDPOINTS ====================

@app.post("/journal/{user_id}/search", response_model=SearchResponse)
async def search_entries(
    user_id: str,
    query: SearchQuery,
    mm: MemoryManager = Depends(get_memory_manager)
):
    """Search journal entries"""
    results = mm.search(user_id, query.query, limit=query.limit)

    return SearchResponse(
        query=query.query,
        results=[
            SearchResult(
                date=r.get("date", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.0),
                title=r.get("title")
            )
            for r in results
        ],
        total=len(results)
    )


# ==================== EMOTIONS ENDPOINTS ====================

@app.post("/journal/{user_id}/entries/{date}/analyze", response_model=EmotionAnalysis)
async def analyze_entry(
    user_id: str,
    date: str,
    mm: MemoryManager = Depends(get_memory_manager),
    ea: EmotionsAnalyzer = Depends(get_emotions_analyzer)
):
    """Analyze emotions in a journal entry"""
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
            Motivato=emotions.get("motivato", 0.0)
        ),
        dominant_emotion=dominant,
        daily_insights=analysis.get("daily_insights")
    )


@app.get("/journal/{user_id}/entries/{date}/emotions", response_model=Optional[EmotionAnalysis])
async def get_emotions(
    user_id: str,
    date: str,
    mm: MemoryManager = Depends(get_memory_manager)
):
    """Get emotions for a specific date"""
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
            Motivato=emotions.get("motivato", 0.0)
        )
    )


@app.get("/journal/{user_id}/emotions/weekly")
async def get_weekly_emotions(
    user_id: str,
    mm: MemoryManager = Depends(get_memory_manager)
):
    """
    Get emotions for the last 7 days.
    Returns dict with date -> emotions mapping.
    """
    from datetime import timedelta

    today = datetime.now()
    dates = []
    for i in range(7):
        d = today - timedelta(days=i)
        dates.append(d.strftime("%Y-%m-%d"))

    # Get emotions for all dates
    result = {}
    for date in dates:
        emotions = mm.get_emotions(user_id, date)
        if emotions:
            result[date] = {
                "emotions": emotions,
                "dominant": max(emotions, key=emotions.get) if emotions else None,
                "intensity": sum(emotions.values()) / len(emotions) if emotions else 0
            }
        else:
            result[date] = None

    return {"weekly_emotions": result, "dates": dates}


# ==================== CHAT ENDPOINTS ====================

@app.post("/chat/{user_id}", response_model=ChatResponse)
async def chat(
    user_id: str,
    request: ChatRequest,
    cs: ChatService = Depends(get_chat_service)
):
    """Send a chat message"""
    try:
        result = await cs.chat(
            user_id=user_id,
            message=request.message,
            include_context=request.include_context
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
        response=result["response"],
        context_used=result.get("context_used", False)
    )


@app.delete("/chat/{user_id}/history")
async def clear_chat_history(
    user_id: str,
    cs: ChatService = Depends(get_chat_service)
):
    """Clear chat history for a user"""
    cs.clear_conversation(user_id)
    return {"message": "Chat history cleared"}


# ==================== STATS ENDPOINTS ====================

@app.get("/journal/{user_id}/stats", response_model=StatsResponse)
async def get_stats(
    user_id: str,
    mm: MemoryManager = Depends(get_memory_manager)
):
    """Get journal statistics"""
    from datetime import timedelta

    stats = mm.get_stats(user_id)

    # Calculate weekly activity (last 7 days)
    memory = mm.get_user_memory(user_id)
    today = datetime.now()
    weekly_activity = []

    for i in range(6, -1, -1):  # From 6 days ago to today
        d = today - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        has_entry = date_str in memory.entries
        weekly_activity.append(has_entry)

    return StatsResponse(
        stats=JournalStats(
            total_entries=stats.get("total_entries", 0),
            total_words=stats.get("total_words", 0),
            average_words=stats.get("average_words", 0),
            current_streak=stats.get("current_streak", 0),
            longest_streak=stats.get("longest_streak", 0),
            first_entry=stats.get("first_entry"),
            last_entry=stats.get("last_entry"),
            weekly_activity=weekly_activity
        ),
        top_topics=[]  # TODO: Implement
    )


# ==================== IMPORT/UPLOAD ENDPOINTS ====================

@app.post("/journal/{user_id}/import/files", response_model=ImportResponse)
async def upload_files(
    user_id: str,
    files: List[UploadFile] = File(...),
    rebuild_vectors: bool = Query(True),
    mm: MemoryManager = Depends(get_memory_manager)
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
                error_message=f["error_message"]
            )
            for f in result["files"]
        ],
        vectorization_status=result["vectorization_status"]
    )


@app.post("/journal/{user_id}/import/bulk", response_model=ImportResponse)
async def bulk_import(
    user_id: str,
    request: BulkImportRequest,
    mm: MemoryManager = Depends(get_memory_manager)
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
    entries = [
        {
            "date": e.date,
            "content": e.content,
            "filename": e.filename or f"{e.date}.txt"
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
                error_message=f["error_message"]
            )
            for f in result["files"]
        ],
        vectorization_status=result["vectorization_status"]
    )


@app.post("/journal/{user_id}/rebuild-vectors")
async def rebuild_vectors(
    user_id: str,
    mm: MemoryManager = Depends(get_memory_manager)
):
    """
    Manually trigger rebuild of Memvid index and vector embeddings.
    Useful after manual file changes or to fix corrupted index.
    """
    try:
        mm._rebuild_user_memory(user_id)
        memory = mm.get_user_memory(user_id)

        return {
            "status": "success",
            "message": "Memory rebuilt successfully",
            "entries_indexed": len(memory.entries),
            "embeddings_generated": len(memory.embeddings) if hasattr(memory, 'embeddings') else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")


# ==================== BACKUP/DOWNLOAD ENDPOINTS ====================

@app.get("/journal/{user_id}/backup/json")
async def download_backup_json(
    user_id: str,
    include_emotions: bool = Query(True),
    mm: MemoryManager = Depends(get_memory_manager)
):
    """
    Download complete backup as JSON.
    Includes all entries and optionally emotions data.
    """
    import json

    backup_data = mm.get_backup_data(user_id, include_emotions)

    # Convert to JSON bytes
    json_content = json.dumps(backup_data, indent=2, ensure_ascii=False)
    json_bytes = json_content.encode('utf-8')

    # Create streaming response
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=reminor_backup_{user_id}_{datetime.now().strftime('%Y%m%d')}.json"
        }
    )


@app.get("/journal/{user_id}/backup/mv2")
async def download_backup_mv2(
    user_id: str,
    mm: MemoryManager = Depends(get_memory_manager)
):
    """
    Download raw Memvid .mv2 file.
    This contains the complete memory with embeddings.
    Can be used to restore full memory state.
    """
    mv2_path = mm.get_mv2_path(user_id)

    if not mv2_path.exists():
        raise HTTPException(status_code=404, detail="Memory file not found. No entries saved yet.")

    return FileResponse(
        path=str(mv2_path),
        media_type="application/octet-stream",
        filename=f"reminor_memory_{user_id}_{datetime.now().strftime('%Y%m%d')}.mv2"
    )


@app.get("/journal/{user_id}/backup/zip")
async def download_backup_zip(
    user_id: str,
    include_mv2: bool = Query(True),
    mm: MemoryManager = Depends(get_memory_manager)
):
    """
    Download complete backup as ZIP archive.
    Includes:
    - All .txt journal files
    - emotions.json with emotion data
    - Optionally the .mv2 memory file
    """
    import json

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
        "mv2_included": False
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
                metadata["mv2_note"] = "File locked - can be regenerated from diary entries"

    # Read knowledge base
    knowledge_content = None
    knowledge_path = user_dir / "user_knowledge.json"
    if knowledge_path.exists():
        try:
            knowledge_content = knowledge_path.read_text(encoding='utf-8')
            metadata["knowledge_included"] = True
        except Exception as e:
            print(f"[WARNING] Could not read knowledge file: {e}")

    # Create ZIP in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add all .txt files from journal directory
        if journal_dir.exists():
            for txt_file in journal_dir.glob("*.txt"):
                zf.write(txt_file, f"journal/{txt_file.name}")

        # Add emotions data
        if emotions_data:
            zf.writestr("emotions.json", json.dumps(emotions_data, indent=2, ensure_ascii=False))

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
        }
    )


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
