import json
import sys
import time
from pathlib import Path
from extract import extract_fnol_with_stats

def load_ground_truth(path: str = "ground_truth.json") -> dict:
    """Load the ground truth labels file."""
    p = Path(path)
    if not p.exists():
        print(f"Error: '{path}' not found. Please create {path} with labelled clips.")
        sys.exit(1)
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def get_cached_transcript(clip_id: str) -> tuple[str, float]:
    """Retrieve cached transcript and latency without making any API calls."""
    candidates = [
        Path("transcripts") / f"{clip_id}.prisma-v3.0.json",
        Path("transcripts") / f"{clip_id}.json",
    ]
    for c in candidates:
        if c.exists():
            data = json.loads(c.read_text(encoding="utf-8"))
            transcript = data.get("transcript", "")
            latency = float(data.get("end_to_end_latency", 0.0))
            return transcript, latency

    raise FileNotFoundError(f"No cached transcript found for clip '{clip_id}' in transcripts/. Skipping API call per rules.")

def evaluate():
    gt = load_ground_truth()
    total_clips = len(gt)
    if total_clips == 0:
        print("ground_truth.json is empty. No clips to evaluate.")
        return

    # Track metrics per condition and overall
    # condition -> dict of lists/counters
    conditions = ["clean", "noisy", "noise_cancelled"]
    stats = {
        cond: {
            "n": 0,
            "drivable_correct": 0,
            "towing_correct": 0,
            "third_party_correct": 0,
            "tp_zones": 0,
            "fp_zones": 0,
            "fn_zones": 0,
            "stt_latencies": [],
            "llm_latencies": [],
            "total_latencies": [],
            "dropped_evidence": 0,
        }
        for cond in conditions + ["overall"]
    }

    failures = []

    print(f"Starting evaluation across {total_clips} clip(s)...")

    for clip_id, item in gt.items():
        cond = item.get("condition", "unknown")
        expected = item.get("expected", {})

        # Load cached transcript
        try:
            transcript, stt_latency = get_cached_transcript(clip_id)
        except FileNotFoundError as e:
            print(f"Warning: {e}")
            continue

        # Run extraction and measure LLM latency
        t0 = time.perf_counter()
        pred_fnol, dropped_count = extract_fnol_with_stats(transcript)
        llm_latency = time.perf_counter() - t0
        total_latency = stt_latency + llm_latency

        # Check fields
        drivable_match = (pred_fnol.vehicle_drivable == expected.get("vehicle_drivable"))
        towing_match = (pred_fnol.towing_required == expected.get("towing_required"))
        third_party_match = (pred_fnol.third_party_or_injury == expected.get("third_party_or_injury"))

        pred_zones = {z.zone for z in pred_fnol.damage_zones}
        exp_zones = set(expected.get("damage_zones", []))

        tp = len(pred_zones & exp_zones)
        fp = len(pred_zones - exp_zones)
        fn = len(exp_zones - pred_zones)
        zones_match = (pred_zones == exp_zones)

        # Update stats for condition and overall
        targets = ["overall"]
        if cond in stats:
            targets.append(cond)

        for target in targets:
            stats[target]["n"] += 1
            if drivable_match:
                stats[target]["drivable_correct"] += 1
            if towing_match:
                stats[target]["towing_correct"] += 1
            if third_party_match:
                stats[target]["third_party_correct"] += 1
            stats[target]["tp_zones"] += tp
            stats[target]["fp_zones"] += fp
            stats[target]["fn_zones"] += fn
            stats[target]["stt_latencies"].append(stt_latency)
            stats[target]["llm_latencies"].append(llm_latency)
            stats[target]["total_latencies"].append(total_latency)
            stats[target]["dropped_evidence"] += dropped_count

        # Record failure details if any mismatch
        if not (drivable_match and towing_match and third_party_match and zones_match):
            mismatches = []
            if not drivable_match:
                mismatches.append(f"- **vehicle_drivable**: expected `{expected.get('vehicle_drivable')}`, got `{pred_fnol.vehicle_drivable}` (evidence: \"{pred_fnol.vehicle_drivable_evidence}\")")
            if not towing_match:
                mismatches.append(f"- **towing_required**: expected `{expected.get('towing_required')}`, got `{pred_fnol.towing_required}` (evidence: \"{pred_fnol.towing_evidence}\")")
            if not third_party_match:
                mismatches.append(f"- **third_party_or_injury**: expected `{expected.get('third_party_or_injury')}`, got `{pred_fnol.third_party_or_injury}` (evidence: \"{pred_fnol.third_party_evidence}\")")
            if not zones_match:
                mismatches.append(f"- **damage_zones**: expected `{sorted(list(exp_zones))}`, got `{sorted(list(pred_zones))}`")

            failures.append({
                "clip_id": clip_id,
                "condition": cond,
                "transcript": transcript,
                "mismatches": mismatches,
                "dropped_evidence": dropped_count,
            })

    # Generate Markdown Report
    lines = []
    lines.append(f"# Pipeline Evaluation Report (Total Clips N={stats['overall']['n']})\n")
    lines.append("| Condition | Sample Size (N) | Drivable Acc | Towing Acc | Third-Party Acc | Zone Precision | Zone Recall | Avg STT Latency | Avg LLM Latency | Avg Total Latency | Dropped Quotes |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for cond in conditions + ["overall"]:
        s = stats[cond]
        n = s["n"]
        if n == 0:
            lines.append(f"| {cond} | 0 | - | - | - | - | - | - | - | - | 0 |")
            continue

        d_acc = f"{(s['drivable_correct'] / n) * 100:.1f}%"
        t_acc = f"{(s['towing_correct'] / n) * 100:.1f}%"
        tp_acc = f"{(s['third_party_correct'] / n) * 100:.1f}%"

        # Precision & Recall
        prec_denom = s["tp_zones"] + s["fp_zones"]
        rec_denom = s["tp_zones"] + s["fn_zones"]
        prec = (s["tp_zones"] / prec_denom * 100) if prec_denom > 0 else (100.0 if rec_denom == 0 else 0.0)
        rec = (s["tp_zones"] / rec_denom * 100) if rec_denom > 0 else 100.0

        prec_str = f"{prec:.1f}%"
        rec_str = f"{rec:.1f}%"

        avg_stt = f"{sum(s['stt_latencies']) / n:.3f}s"
        avg_llm = f"{sum(s['llm_latencies']) / n:.3f}s"
        avg_tot = f"{sum(s['total_latencies']) / n:.3f}s"
        dropped = s["dropped_evidence"]

        lines.append(f"| **{cond}** | {n} | {d_acc} | {t_acc} | {tp_acc} | {prec_str} | {rec_str} | {avg_stt} | {avg_llm} | {avg_tot} | {dropped} |")

    lines.append("\n## Wrong Predictions Analysis\n")
    if not failures:
        lines.append("No prediction failures. 100% accuracy on evaluated clips!\n")
    else:
        lines.append(f"Total failed clips: {len(failures)} out of {stats['overall']['n']}\n")
        for f in failures:
            lines.append(f"### Clip `{f['clip_id']}` (Condition: `{f['condition']}`)")
            lines.append(f"- **Transcript**: \"{f['transcript']}\"")
            if f["dropped_evidence"] > 0:
                lines.append(f"- **Dropped Quotes (Not in transcript)**: {f['dropped_evidence']}")
            lines.append("- **Mismatches**:")
            for m in f["mismatches"]:
                lines.append(f"  {m}")
            lines.append("")

    report = "\n".join(lines)

    # Print to stdout
    print("\n" + report)

    # Save to results.md
    Path("results.md").write_text(report, encoding="utf-8")
    print("\nReport written to results.md")

if __name__ == "__main__":
    evaluate()

