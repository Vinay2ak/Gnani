import os
import json
import base64
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

def generate_readback_sentence(fnol: dict) -> str:
    """Generate a short Hindi-English confirmation sentence based on FNOL data with numbers as words."""
    num_words = {
        "0": "zero", "1": "ek", "2": "do", "3": "teen", "4": "char",
        "5": "paanch", "6": "chhah", "7": "saat", "8": "aath", "9": "nau", "10": "das"
    }
    parts = ["Aapka accident claim darj ho gaya hai."]

    # Drivability
    drivable = fnol.get("vehicle_drivable")
    if drivable == "FALSE":
        parts.append("Gaadi chalne layak nahi hai.")
    elif drivable == "TRUE":
        parts.append("Gaadi chalne ki sthiti mein hai.")

    # Towing
    towing = fnol.get("towing_required")
    if towing == "TRUE":
        parts.append("Towing aur recovery ki zaroorat hai.")
    elif towing == "FALSE":
        parts.append("Towing ki zaroorat nahi hai.")

    # Damage zones with count as words
    zones = [z.get("zone") for z in fnol.get("damage_zones", []) if z.get("zone")]
    if zones:
        count_word = num_words.get(str(len(zones)), str(len(zones)))
        parts.append(f"Nuksan ke {count_word} zones hain: {', '.join(zones)}.")

    # Injury / Third Party
    injury = fnol.get("third_party_or_injury")
    if injury == "TRUE":
        parts.append("Chot ya third-party damage report hua hai.")
    elif injury == "FALSE":
        parts.append("Kisi ko chot nahi aayi hai.")

    parts.append("Surveyor aapse jald hi sampark karenge.")
    return " ".join(parts)

def synthesize_readback(text: str, output_path: str | Path, voice: str = "Nalini") -> Path:
    """Synthesize text into WAV audio using Gnani Timbre TTS (timbre-v2.5) with disk cache."""
    out = Path(output_path)
    # Check cache first: never call API twice for the same clip
    if out.exists() and out.stat().st_size > 0:
        return out

    api_key = os.environ.get("GNANI_API_KEY")
    if not api_key:
        raise ValueError("GNANI_API_KEY environment variable is not set in .env")

    url = "https://api.vachana.ai/api/v1/tts/inference"
    headers = {
        "X-API-Key-ID": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model": "timbre-v2.5",
        "voice": voice,
        "language": "hi-IN",
        "speed": 1.0,
        "audio_config": {
            "encoding": "linear_pcm",
            "container": "wav",
            "num_channels": 1,
            "sample_rate": 48000,
            "sample_width": 2,
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
    except Exception as e:
        raise RuntimeError(f"Network error while connecting to Gnani Timbre TTS: {str(e)}")

    if not resp.ok:
        # Sanitize error message to ensure no secrets or full details are leaked
        err_msg = resp.text[:200]
        raise RuntimeError(f"Gnani Timbre TTS error [{resp.status_code}]: {err_msg}")

    content = resp.content
    # If Gnani response is JSON with base64 audio payload
    if content.strip().startswith(b"{"):
        try:
            j = resp.json()
            b64_audio = j.get("audio") or j.get("audio_content") or j.get("data")
            if b64_audio:
                content = base64.b64decode(b64_audio)
            else:
                raise RuntimeError(f"Gnani Timbre TTS returned JSON without audio payload: {j}")
        except json.JSONDecodeError:
            pass

    if not content or len(content) < 44:
        raise RuntimeError("Gnani Timbre TTS returned empty or invalid audio data")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(content)
    return out
