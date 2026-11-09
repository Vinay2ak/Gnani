import os
import sys
import json
import difflib
from pathlib import Path

def main():
    has_problems = False
    clips_dir = Path("clips")
    transcripts_dir = Path("transcripts")
    outputs_dir = Path("outputs")

    # 1. Load ground_truth.json (utf-8) with line and column reporting on JSON errors
    gt_path = Path("ground_truth.json")
    if not gt_path.is_file():
        print(f"ERROR: {gt_path} not found.")
        sys.exit(1)

    try:
        with open(gt_path, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {gt_path} at line {e.lineno}, column {e.colno}: {e.msg}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Could not read {gt_path}: {e}")
        sys.exit(1)

    # Load damage_taxonomy.json for zone verification
    tax_path = Path("damage_taxonomy.json")
    if not tax_path.is_file():
        print(f"ERROR: {tax_path} not found.")
        sys.exit(1)

    try:
        with open(tax_path, "r", encoding="utf-8") as f:
            taxonomy = json.load(f)
            allowed_zones = set(taxonomy.get("zones", {}).keys())
    except Exception as e:
        print(f"ERROR: Could not read {tax_path}: {e}")
        sys.exit(1)

    # 2. Check clips/ directory for spaces and orphan quite*/noisy* files
    clip_files = list(clips_dir.glob("*")) if clips_dir.exists() else []
    
    # Flag any filename containing a space
    spaced_files = [f.name for f in clip_files if " " in f.name]
    if spaced_files:
        has_problems = True
        print(f"FLAG: Filename(s) containing spaces in {clips_dir}: {', '.join(spaced_files)}")

    # Files named quite* or noisy* that have no ground_truth key
    orphan_clips = []
    for f in clip_files:
        if f.is_file():
            lower_name = f.stem.lower()
            if lower_name.startswith("quite") or lower_name.startswith("noisy"):
                if f.stem not in ground_truth:
                    orphan_clips.append(f.name)

    if orphan_clips:
        has_problems = True
        print(f"WARNING: Clips named quite*/noisy* with no ground_truth entry: {', '.join(orphan_clips)}")

    # 3. Validate each ground_truth entry and check cached files
    TRI_STATES = {"TRUE", "FALSE", "UNKNOWN"}
    CONDITIONS = {"clean", "noisy", "noise_cancelled"}

    table_rows = []
    missing_audio_keys = []

    for key, entry in ground_truth.items():
        clip_problems = []

        # Find clips/<key>.* (any extension)
        matching_audio = list(clips_dir.glob(f"{key}.*")) if clips_dir.exists() else []
        audio_found = len(matching_audio) > 0
        if not audio_found:
            clip_problems.append("no audio file in clips/")
            missing_audio_keys.append(key)

        # Check cached transcript: transcripts/<key>.prisma-v3.0.json
        cached_transcript = (transcripts_dir / f"{key}.prisma-v3.0.json").is_file()

        # Check cached output: outputs/<key>.json
        cached_output = (outputs_dir / f"{key}.json").is_file()

        # Validate entry structure & condition
        if not isinstance(entry, dict):
            clip_problems.append("entry is not a JSON object")
        else:
            cond = entry.get("condition")
            if cond not in CONDITIONS:
                clip_problems.append(f"invalid condition '{cond}' (expected: clean|noisy|noise_cancelled)")

            expected = entry.get("expected")
            if not isinstance(expected, dict):
                clip_problems.append("expected field is missing or not a JSON object")
            else:
                for field in ["vehicle_drivable", "towing_required", "third_party_or_injury"]:
                    val = expected.get(field)
                    if val not in TRI_STATES:
                        clip_problems.append(f"invalid {field} '{val}' (expected: TRUE|FALSE|UNKNOWN)")

                # Validate damage_zones
                damage_zones = expected.get("damage_zones")
                if not isinstance(damage_zones, list):
                    clip_problems.append("damage_zones is not a list")
                else:
                    for zone in damage_zones:
                        if zone not in allowed_zones:
                            closest = difflib.get_close_matches(zone, allowed_zones, n=1, cutoff=0.2)
                            suggestion = f" (closest valid: '{closest[0]}')" if closest else ""
                            clip_problems.append(f"unrecognized damage zone '{zone}'{suggestion}")

        if clip_problems:
            has_problems = True

        table_rows.append({
            "clip": key,
            "audio": "YES" if audio_found else "NO",
            "transcript": "YES" if cached_transcript else "NO",
            "output": "YES" if cached_output else "NO",
            "problems": "; ".join(clip_problems) if clip_problems else "None",
        })

    # List keys with no audio file if any
    if missing_audio_keys:
        print(f"ERROR: Ground truth key(s) with no audio file in {clips_dir}: {', '.join(missing_audio_keys)}")

    # 4. Print table: clip | audio found | cached transcript found | cached output found | problems
    headers = ["clip", "audio found", "cached transcript found", "cached output found", "problems"]
    col_clip_w = max(len(headers[0]), max((len(r["clip"]) for r in table_rows), default=10))
    col_audio_w = max(len(headers[1]), 11)
    col_stt_w = max(len(headers[2]), 23)
    col_out_w = max(len(headers[3]), 19)
    col_prob_w = max(len(headers[4]), max((len(r["problems"]) for r in table_rows), default=10))

    header_line = f"{headers[0]:<{col_clip_w}} | {headers[1]:<{col_audio_w}} | {headers[2]:<{col_stt_w}} | {headers[3]:<{col_out_w}} | {headers[4]:<{col_prob_w}}"
    sep_line = f"{'-'*col_clip_w}-+-{'-'*col_audio_w}-+-{'-'*col_stt_w}-+-{'-'*col_out_w}-+-{'-'*col_prob_w}"

    print("\n" + header_line)
    print(sep_line)
    for r in table_rows:
        print(f"{r['clip']:<{col_clip_w}} | {r['audio']:<{col_audio_w}} | {r['transcript']:<{col_stt_w}} | {r['output']:<{col_out_w}} | {r['problems']:<{col_prob_w}}")

    if has_problems:
        print("\nSetup check FAILED: Problems detected above.")
        sys.exit(1)
    else:
        print("\nSetup check PASSED: All ground truth entries and files are valid.")
        sys.exit(0)

if __name__ == "__main__":
    main()

