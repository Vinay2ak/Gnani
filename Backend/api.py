import os
import uuid
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from test_stt import transcribe
from extract import extract_fnol
from policies import lookup_policy
from tts import generate_readback_sentence, synthesize_readback

app = FastAPI(
    title="Bima-Setu (FNOL Co-Pilot) API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Enable CORS: allows deployed frontend in production or specific origins if configured
is_render = os.environ.get("RENDER") == "true" or "PORT" in os.environ
env_origins = os.environ.get("ALLOWED_ORIGINS")

if env_origins:
    origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    if "*" in origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins + ["http://localhost:5173", "http://127.0.0.1:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
elif is_render:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Bima-Setu (FNOL Co-Pilot) API"}

@app.get("/health")
def health():
    return {"status": "ok"}

# In-memory claims storage (no database)
claims_db: dict[str, dict] = {}

# Allowed audio formats and size limits
ALLOWED_EXTENSIONS = {".ogg", ".m4a", ".mp3", ".wav"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Mock workshops list for adjuster assignment
MOCK_WORKSHOPS = [
    "Apex Auto Body Works (Authorized Center, Andheri)",
    "Speedy Motors Garage (Okhla Phase 2)",
    "National Car Care & Recovery (Whitefield)",
    "Universal Precision Bodyshop (Sector 62, Noida)",
]

# Ensure directories exist
Path("uploads").mkdir(exist_ok=True)
Path("readback").mkdir(exist_ok=True)

@app.post("/claims")
async def create_claim(
    audio_file: UploadFile = File(...),
    phone: Optional[str] = Form(None),
):
    """Multipart upload: validates audio format and size, transcribes, extracts FNOL, matches policy."""
    claim_id = f"CLM-{uuid.uuid4().hex[:6].upper()}"

    # Validate file extension
    raw_filename = audio_file.filename or "audio.ogg"
    ext = Path(raw_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio format '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Read and validate size (max 5 MB)
    file_bytes = await audio_file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file size exceeds the 5 MB limit ({len(file_bytes)} bytes uploaded)",
        )

    # Save audio file strictly with claim_id (never user's filename)
    safe_filename = f"{claim_id}{ext}"
    upload_path = Path("uploads") / safe_filename

    try:
        upload_path.write_bytes(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded audio: {str(e)}")

    # 1. STT Transcription
    t_stt_0 = time.perf_counter()
    try:
        stt_res = transcribe(str(upload_path), model="prisma-v3.0", lang="hi-IN")
        stt_wall = time.perf_counter() - t_stt_0
        stt_seconds = round(float(stt_res.get("end_to_end_latency", stt_wall)), 3)
        transcript = stt_res.get("transcript", "")
    except Exception as e:
        upload_path.unlink(missing_ok=True)
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
            raise HTTPException(status_code=503, detail="LLM quota exhausted")
        raise HTTPException(status_code=502, detail=f"STT transcription failed: {str(e)[:200]}")

    # 2. FNOL Extraction
    t_llm_0 = time.perf_counter()
    try:
        fnol_obj = extract_fnol(transcript)
        llm_seconds = round(time.perf_counter() - t_llm_0, 3)
    except Exception as e:
        upload_path.unlink(missing_ok=True)
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
            raise HTTPException(status_code=503, detail="LLM quota exhausted")
        raise HTTPException(status_code=502, detail=f"FNOL extraction failed: {str(e)[:200]}")

    total_seconds = round(stt_seconds + llm_seconds, 3)

    # 3. Policy Lookup
    phone_str = phone if isinstance(phone, str) else None
    policy_info = lookup_policy(phone_str)

    # Store in memory only after pipeline succeeds
    claim_record = {
        "id": claim_id,
        "phone": phone_str,
        "policy": policy_info,
        "transcript": transcript,
        "fnol": fnol_obj.model_dump(),
        "timings": {
            "stt_seconds": stt_seconds,
            "llm_seconds": llm_seconds,
            "total_seconds": total_seconds,
        },
        "status": "pending",
        "workshop": None,
        "audio_path": str(upload_path),
    }
    claims_db[claim_id] = claim_record
    return claim_record

@app.get("/claims")
def list_claims():
    """Retrieve all claims in memory."""
    return list(claims_db.values())

@app.get("/claims/{claim_id}")
def get_claim(claim_id: str):
    """Retrieve a single claim by its ID."""
    if claim_id not in claims_db:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found")
    return claims_db[claim_id]

@app.post("/claims/{claim_id}/approve")
def approve_claim(claim_id: str):
    """Adjuster approves claim and assigns an authorized workshop. Works only if pending."""
    if claim_id not in claims_db:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found")

    claim = claims_db[claim_id]
    if claim.get("status") != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Claim is already '{claim.get('status')}'; can only approve claims with 'pending' status",
        )

    claim["status"] = "approved"

    # Assign workshop from mock list in round-robin fashion
    idx = len(claims_db) % len(MOCK_WORKSHOPS)
    claim["workshop"] = MOCK_WORKSHOPS[idx]

    return claim

@app.post("/claims/{claim_id}/readback")
def readback_claim(claim_id: str, voice: Optional[str] = "Nalini"):
    """Generate or serve cached Hindi-English audio confirmation for the claim."""
    if claim_id not in claims_db:
        raise HTTPException(status_code=404, detail=f"Claim '{claim_id}' not found")

    selected_voice = "Deepak" if voice and voice.strip().lower() in ["deepak", "male", "man", "purush"] else "Nalini"
    voice_slug = selected_voice.lower()
    cache_file = Path("readback") / f"{claim_id}_{voice_slug}.wav"

    # Return cached audio if available
    if cache_file.exists() and cache_file.stat().st_size > 0:
        return FileResponse(cache_file, media_type="audio/wav", filename=f"{claim_id}_readback_{voice_slug}.wav")

    # Generate read-back text
    claim = claims_db[claim_id]
    readback_text = generate_readback_sentence(claim.get("fnol", {}))

    # Call Gnani Timbre TTS
    try:
        synthesize_readback(readback_text, cache_file, voice=selected_voice)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"TTS synthesis error: {str(e)[:200]}")

    return FileResponse(cache_file, media_type="audio/wav", filename=f"{claim_id}_readback_{voice_slug}.wav")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
