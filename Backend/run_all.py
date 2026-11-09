import os
import sys
import json
import time
from pathlib import Path
import requests

from pipeline import run_pipeline

def is_http_429(err: Exception) -> bool:
    """Check if the error is an HTTP 429 (quota / rate limit)."""
    if hasattr(err, "response") and getattr(err, "response", None) is not None:
        if getattr(err.response, "status_code", None) == 429:
            return True
    err_str = str(err).lower()
    return "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str

def is_retryable_error(err: Exception) -> bool:
    """Check if error is transient server error (500, 503, 504) or network timeout."""
    if is_http_429(err):
        return False
    if isinstance(err, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    
    if hasattr(err, "response") and getattr(err, "response", None) is not None:
        if getattr(err.response, "status_code", None) in (500, 503, 504):
            return True
            
    err_str = str(err).lower()
    for code in ["500", "503", "504", "timeout"]:
        if code in err_str:
            return True
        
    return False

def read_saved_timings(key: str) -> dict | None:
    """Read timings from outputs/<key>.json if present."""
    out_file = Path("outputs") / f"{key}.json"
    if not out_file.is_file():
        return None
    try:
        data = json.loads(out_file.read_text(encoding="utf-8"))
        timings = data.get("timings")
        if isinstance(timings, dict):
            return timings
    except Exception:
        pass
    return None

def main():
    force = "--force" in sys.argv
    gt_path = Path("ground_truth.json")
    if not gt_path.is_file():
        print(f"Error: {gt_path} not found.")
        sys.exit(1)

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    clips_dir = Path("clips")
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    summary_rows = []
    total_clips = len(ground_truth)
    print(f"Starting batch run for {total_clips} clip(s) (force={force})...\n")

    clip_keys = list(ground_truth.keys())

    for idx, key in enumerate(clip_keys):
        # 1. Locate audio file
        matches = list(clips_dir.glob(f"{key}.*")) if clips_dir.exists() else []
        if not matches:
            print(f"[{idx+1}/{total_clips}] {key}: audio file not found in {clips_dir}")
            summary_rows.append({
                "clip": key,
                "status": "failed (missing audio)",
                "stt_seconds": "N/A",
                "llm_seconds": "N/A",
                "total_seconds": "N/A",
            })
            continue

        audio_path = matches[0]
        out_file = outputs_dir / f"{key}.json"

        # 2. Check if already cached in outputs/
        if out_file.is_file() and not force:
            print(f"[{idx+1}/{total_clips}] {key}: skipped (outputs/{key}.json already exists)")
            timings = read_saved_timings(key)
            stt_s = timings.get("stt_seconds", "N/A") if timings else "N/A"
            llm_s = timings.get("llm_seconds", "N/A") if timings else "N/A"
            tot_s = timings.get("total_seconds", "N/A") if timings else "N/A"

            summary_rows.append({
                "clip": key,
                "status": "skipped",
                "stt_seconds": stt_s,
                "llm_seconds": llm_s,
                "total_seconds": tot_s,
            })
            continue

        # 3. Execute pipeline with retry policy
        print(f"[{idx+1}/{total_clips}] {key}: processing {audio_path.name}...")
        max_retries = 2
        attempt = 0
        success = False
        quota_exhausted = False

        while attempt <= max_retries:
            try:
                run_pipeline(str(audio_path))
                success = True
                break
            except Exception as e:
                if is_http_429(e):
                    print(f"[{key}] Fatal: Daily quota exhausted, stop and retry later")
                    summary_rows.append({
                        "clip": key,
                        "status": "failed (quota exhausted)",
                        "stt_seconds": "N/A",
                        "llm_seconds": "N/A",
                        "total_seconds": "N/A",
                    })
                    quota_exhausted = True
                    break
                attempt += 1
                if is_retryable_error(e) and attempt <= max_retries:
                    print(f"[{key}] Retryable error encountered: {type(e).__name__}. Waiting 20s before retry {attempt}/{max_retries}...")
                    time.sleep(20)
                else:
                    # Print non-retryable error or final failure without leaking secrets
                    err_msg = str(e)[:200]
                    print(f"[{key}] Error processing pipeline: {err_msg}")
                    break

        if quota_exhausted:
            print("\nDaily quota exhausted, stop and retry later")
            break

        if success:
            timings = read_saved_timings(key)
            stt_s = timings.get("stt_seconds", "N/A") if timings else "N/A"
            llm_s = timings.get("llm_seconds", "N/A") if timings else "N/A"
            tot_s = timings.get("total_seconds", "N/A") if timings else "N/A"
            summary_rows.append({
                "clip": key,
                "status": "completed",
                "stt_seconds": stt_s,
                "llm_seconds": llm_s,
                "total_seconds": tot_s,
            })
        else:
            summary_rows.append({
                "clip": key,
                "status": "failed",
                "stt_seconds": "N/A",
                "llm_seconds": "N/A",
                "total_seconds": "N/A",
            })

        # Sequential 2-second pause between executed clips
        if idx < len(clip_keys) - 1:
            time.sleep(2)

    # 4. Generate Markdown Summary Table & Stats
    total_nums = [float(r["total_seconds"]) for r in summary_rows if isinstance(r["total_seconds"], (int, float))]
    avg_total = f"{sum(total_nums) / len(total_nums):.3f}s" if total_nums else "N/A"
    max_total = f"{max(total_nums):.3f}s" if total_nums else "N/A"

    lines = []
    lines.append("# Pipeline Execution Summary\n")
    lines.append("| Clip | Status | STT (s) | LLM (s) | Total (s) |")
    lines.append("| :--- | :--- | :--- | :--- | :--- |")

    for r in summary_rows:
        stt_str = f"{r['stt_seconds']}s" if isinstance(r["stt_seconds"], (int, float)) else str(r["stt_seconds"])
        llm_str = f"{r['llm_seconds']}s" if isinstance(r["llm_seconds"], (int, float)) else str(r["llm_seconds"])
        tot_str = f"{r['total_seconds']}s" if isinstance(r["total_seconds"], (int, float)) else str(r["total_seconds"])
        lines.append(f"| {r['clip']} | {r['status']} | {stt_str} | {llm_str} | {tot_str} |")

    lines.append(f"\n- **Average Total Latency**: {avg_total}")
    lines.append(f"- **Max Total Latency**: {max_total}\n")

    summary_content = "\n".join(lines)

    # Print to stdout
    print("\n" + summary_content)

    # Save to run_summary.md (UTF-8)
    Path("run_summary.md").write_text(summary_content, encoding="utf-8")
    print("Saved execution summary to run_summary.md")

if __name__ == "__main__":
    main()

