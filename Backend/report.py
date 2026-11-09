import json
from pathlib import Path

def normalize_text(text: str) -> str:
    """Normalize string: lowercase and remove spaces and hyphens."""
    if not text:
        return ""
    return text.lower().replace("-", "").replace(" ", "")

def load_taxonomy_zones() -> dict[str, list[str]]:
    """Load taxonomy zones and their aliases from damage_taxonomy.json."""
    tax_path = Path("damage_taxonomy.json")
    if not tax_path.is_file():
        return {}
    data = json.loads(tax_path.read_text(encoding="utf-8"))
    return data.get("zones", {})

def diagnose_missing_zone(zone: str, transcript: str, taxonomy_zones: dict[str, list[str]]) -> str:
    """Check if any alias appears in transcript (treating space/hyphen/no-space as equal)."""
    norm_transcript = normalize_text(transcript)
    aliases = taxonomy_zones.get(zone, [])
    # Also include the zone name itself
    candidates = aliases + [zone]
    
    for alias in candidates:
        norm_alias = normalize_text(alias)
        if norm_alias and norm_alias in norm_transcript:
            return "LLM_MISSED"
    return "STT_MISSED"

def diagnose_towing(transcript: str) -> str:
    """Check if transcript contains towing keywords: tow, crane, टो, क्रेन."""
    norm_transcript = normalize_text(transcript)
    keywords = ["tow", "crane", "टो", "क्रेन"]
    for kw in keywords:
        norm_kw = normalize_text(kw)
        if norm_kw and norm_kw in norm_transcript:
            return "LLM_MISSED"
    return "STT_MISSED"

def load_failed_clips_from_run_summary() -> set[str]:
    """Identify any clips marked failed in run_summary.md."""
    summary_path = Path("run_summary.md")
    if not summary_path.is_file():
        return set()
    failed = set()
    for line in summary_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and not line.startswith("| Clip") and not line.startswith("| :---"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2 and "failed" in parts[1].lower():
                failed.add(parts[0])
    return failed

def generate_report():
    gt_path = Path("ground_truth.json")
    if not gt_path.is_file():
        print("Error: ground_truth.json not found.")
        return

    ground_truth = json.loads(gt_path.read_text(encoding="utf-8"))
    taxonomy_zones = load_taxonomy_zones()
    failed_clips = load_failed_clips_from_run_summary()

    # Track metrics per condition (clean vs noisy)
    conditions = ["clean", "noisy"]
    stats = {
        c: {
            "total": 0,
            "drivable_correct": 0,
            "towing_correct": 0,
            "third_party_correct": 0,
            "zones_correct": 0,
        }
        for c in conditions
    }

    stt_missed_total = 0
    llm_missed_total = 0

    lines = []
    lines.append("# Bima-Setu Pipeline Evaluation Report\n")

    for key, gt_entry in ground_truth.items():
        cond = gt_entry.get("condition", "unknown")
        expected = gt_entry.get("expected", {})

        # Load transcript
        transcript_path = Path("transcripts") / f"{key}.prisma-v3.0.json"
        transcript = ""
        if transcript_path.is_file():
            try:
                t_data = json.loads(transcript_path.read_text(encoding="utf-8"))
                transcript = t_data.get("transcript", "")
            except Exception:
                pass

        # Load extracted FNOL
        out_path = Path("outputs") / f"{key}.json"
        extracted = None
        if out_path.is_file():
            try:
                extracted = json.loads(out_path.read_text(encoding="utf-8"))
                if not transcript:
                    transcript = extracted.get("transcript", "")
            except Exception:
                pass

        lines.append(f"## Clip: `{key}` (Condition: `{cond}`)\n")
        lines.append(f"**Transcript:** \"{transcript}\"\n")

        if key in failed_clips:
            lines.append("> ⚠️ **NOT EVALUATED** (Pipeline execution failed per run_summary.md)\n\n---\n")
            continue

        if extracted is None:
            lines.append(f"> ⚠️ *Output file outputs/{key}.json not found. Run pipeline first.*\n")
            continue

        # Extract values
        ext_drivable = extracted.get("vehicle_drivable", "UNKNOWN")
        exp_drivable = expected.get("vehicle_drivable", "UNKNOWN")
        drivable_ok = (ext_drivable == exp_drivable)

        ext_towing = extracted.get("towing_required", "UNKNOWN")
        exp_towing = expected.get("towing_required", "UNKNOWN")
        towing_ok = (ext_towing == exp_towing)

        ext_tp = extracted.get("third_party_or_injury", "UNKNOWN")
        exp_tp = expected.get("third_party_or_injury", "UNKNOWN")
        tp_ok = (ext_tp == exp_tp)

        # Damage zones extraction
        raw_zones = extracted.get("damage_zones", [])
        ext_zones = set()
        for item in raw_zones:
            if isinstance(item, dict) and "zone" in item:
                ext_zones.add(item["zone"])
            elif isinstance(item, str):
                ext_zones.add(item)

        exp_zones = set(expected.get("damage_zones", []))
        zones_match = (ext_zones == exp_zones)

        # Update per-condition stats
        if cond in stats:
            stats[cond]["total"] += 1
            if drivable_ok:
                stats[cond]["drivable_correct"] += 1
            if towing_ok:
                stats[cond]["towing_correct"] += 1
            if tp_ok:
                stats[cond]["third_party_correct"] += 1
            if zones_match:
                stats[cond]["zones_correct"] += 1

        # Build Side-by-Side Table for Tri-State Fields
        lines.append("| Field | Extracted | Expected | Status | Diagnosis |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")

        # Drivable
        drivable_icon = "✅" if drivable_ok else "❌"
        drivable_diag = ""
        if not drivable_ok:
            drivable_diag = "Mismatch"
        lines.append(f"| vehicle_drivable | `{ext_drivable}` | `{exp_drivable}` | {drivable_icon} | {drivable_diag} |")

        # Towing
        towing_icon = "✅" if towing_ok else "❌"
        towing_diag = ""
        if not towing_ok:
            diag = diagnose_towing(transcript)
            towing_diag = f"`{diag}`"
            if diag == "STT_MISSED":
                stt_missed_total += 1
            else:
                llm_missed_total += 1
        lines.append(f"| towing_required | `{ext_towing}` | `{exp_towing}` | {towing_icon} | {towing_diag} |")

        # Third-Party / Injury
        tp_icon = "✅" if tp_ok else "❌"
        tp_diag = ""
        if not tp_ok:
            tp_diag = "Mismatch"
        lines.append(f"| third_party_or_injury | `{ext_tp}` | `{exp_tp}` | {tp_icon} | {tp_diag} |")

        lines.append("\n**Damage Zones Comparison:**\n")

        # Check matched zones
        matched_zones = exp_zones & ext_zones
        missing_zones = exp_zones - ext_zones
        extra_zones = ext_zones - exp_zones

        for z in sorted(matched_zones):
            lines.append(f"- ✅ **{z}**: Correctly extracted")

        for z in sorted(missing_zones):
            diag = diagnose_missing_zone(z, transcript, taxonomy_zones)
            if diag == "STT_MISSED":
                stt_missed_total += 1
            else:
                llm_missed_total += 1
            lines.append(f"- ❌ **{z}**: Missing (Diagnosis: `{diag}`)")

        for z in sorted(extra_zones):
            lines.append(f"- ❌ **{z}**: Extra / Unverified in Expected")

        if not matched_zones and not missing_zones and not extra_zones:
            lines.append("- *No damage zones expected or extracted.*")

        lines.append("\n---\n")

    # Aggregate Summary
    lines.append("## Summary Statistics\n")
    lines.append("### Per-Condition Field Accuracy\n")
    lines.append("| Condition | Evaluated Clips | Drivable Acc | Towing Acc | Third-Party Acc | Exact Zones Acc |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

    for c in conditions:
        st = stats[c]
        n = st["total"]
        if n == 0:
            lines.append(f"| **{c}** | 0 | - | - | - | - |")
            continue
        d_acc = f"{(st['drivable_correct'] / n) * 100:.1f}% ({st['drivable_correct']}/{n})"
        t_acc = f"{(st['towing_correct'] / n) * 100:.1f}% ({st['towing_correct']}/{n})"
        tp_acc = f"{(st['third_party_correct'] / n) * 100:.1f}% ({st['third_party_correct']}/{n})"
        z_acc = f"{(st['zones_correct'] / n) * 100:.1f}% ({st['zones_correct']}/{n})"
        lines.append(f"| **{c}** | {n} | {d_acc} | {t_acc} | {tp_acc} | {z_acc} |")

    lines.append("\n### Root-Cause Attribution Count\n")
    lines.append(f"- **STT_MISSED**: {stt_missed_total} *(keyword or alias was not present in audio transcript)*")
    lines.append(f"- **LLM_MISSED**: {llm_missed_total} *(keyword or alias was present in audio transcript but LLM failed to extract it)*\n")

    report_text = "\n".join(lines)
    Path("report.md").write_text(report_text, encoding="utf-8")
    print(report_text)
    print("\nSaved report to report.md (UTF-8)")

if __name__ == "__main__":
    generate_report()
