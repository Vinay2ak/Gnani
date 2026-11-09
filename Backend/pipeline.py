import sys
import json
import time
from pathlib import Path
from test_stt import transcribe
from extract import extract_fnol

def run_pipeline(clip_path: str):
    p = Path(clip_path)
    if not p.exists():
        print(f"Error: audio file not found: {clip_path}")
        sys.exit(1)

    # Step 1: STT transcription (uses cached transcript if available)
    t_stt_start = time.perf_counter()
    stt_res = transcribe(str(p), model="prisma-v3.0", lang="hi-IN")
    stt_wall = time.perf_counter() - t_stt_start

    # Use reported API latency if present, else wall clock
    stt_seconds = round(float(stt_res.get("end_to_end_latency", stt_wall)), 3)
    transcript = stt_res.get("transcript", "")

    # Step 2: LLM extraction
    t_llm_start = time.perf_counter()
    fnol = extract_fnol(transcript)
    llm_seconds = round(time.perf_counter() - t_llm_start, 3)

    total_seconds = round(stt_seconds + llm_seconds, 3)

    # Prepare output dictionary
    fnol_dict = fnol.model_dump()
    timings = {
        "stt_seconds": stt_seconds,
        "llm_seconds": llm_seconds,
        "total_seconds": total_seconds,
    }

    # Print FNOL as pretty JSON plus timings
    print("=== FNOL Output ===")
    print(json.dumps(fnol_dict, indent=2, ensure_ascii=False))
    print("\n=== Timings ===")
    print(json.dumps(timings, indent=2))

    # Save output to outputs/<clip>.json
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    out_file = outputs_dir / f"{p.stem}.json"

    saved_data = {
        **fnol_dict,
        "timings": timings,
        "transcript": transcript,
    }
    out_file.write_text(json.dumps(saved_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved output to {out_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <path_to_audio_clip>")
        sys.exit(1)
    run_pipeline(sys.argv[1])

