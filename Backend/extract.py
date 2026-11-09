import json
import re
import string
from pathlib import Path
try:
    from Schema import FNOL, DamageZone
except ImportError:
    from schema import FNOL, DamageZone
from llm import call_llm

def load_taxonomy() -> dict:
    """Load damage taxonomy strictly from damage_taxonomy.json."""
    p = Path("damage_taxonomy.json")
    if not p.is_file():
        raise FileNotFoundError("damage_taxonomy.json not found. Please ensure damage_taxonomy.json exists.")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"damage_taxonomy.json contains invalid JSON: {e}") from e

def normalize_text(text: str) -> str:
    """Normalize string: lowercase and remove spaces and hyphens."""
    if not text:
        return ""
    return text.lower().replace("-", "").replace(" ", "")

def find_taxonomy_hints(transcript: str, zones: dict[str, list[str]]) -> list[str]:
    """Scan transcript for taxonomy aliases (case-insensitive, ignoring hyphens/spaces)."""
    norm_transcript = normalize_text(transcript)
    hits = []
    for zone, aliases in zones.items():
        candidates = aliases + [zone]
        for alias in candidates:
            norm_alias = normalize_text(alias)
            if norm_alias and norm_alias in norm_transcript:
                hits.append(zone)
                break
    return hits

def build_system_prompt() -> tuple[str, set[str]]:
    """Build the system prompt using taxonomy, rules, and few-shot example."""
    tax = load_taxonomy()
    zones = tax.get("zones", {})
    allowed_zones = set(zones.keys())

    # Build taxonomy guide string
    tax_lines = []
    for zone, aliases in zones.items():
        tax_lines.append(f"- \"{zone}\": aliases/keywords = {json.dumps(aliases, ensure_ascii=False)}")
    tax_str = "\n".join(tax_lines)

    system_prompt = f"""You are an expert First Notice of Loss (FNOL) extractor for vehicle accident calls in Hindi-English.
Extract the structured FNOL information from the caller's transcript.

### ALLOWED DAMAGE ZONES (Use ONLY these exact zone names):
{tax_str}

### HARD RULES:
1. Every damage zone must use the EXACT zone name from the allowed list above. Never invent a zone.
2. Unverified slang (such as 'chimta') must NOT be mapped to any damage zone.
3. Values for 'vehicle_drivable', 'towing_required', and 'third_party_or_injury' must be 'TRUE', 'FALSE', or 'UNKNOWN'.
4. Evidence quotes MUST be EXACT substrings of the transcript. Do not paraphrase.
5. If the transcript does not explicitly mention or confirm a field, set it to 'UNKNOWN' with empty evidence \"\". Do not guess.
6. Return JSON only, with no markdown fences, no formatting, and no commentary.
7. Towing rule: 'towing_required' is TRUE only if the evidence quote contains tow, crane, flatbed, recovery, टो or क्रेन, or an explicit request for a vehicle to pull the car; FALSE only if the caller explicitly says no tow is needed; otherwise UNKNOWN.
8. Negation rule: A part the caller says is undamaged must NOT be listed as damaged.
9. Taxonomy hints rule: Potential damage zone keyword hits may be provided with the transcript. A zone is kept ONLY if supported by an exact-substring evidence quote from the transcript.

### JSON SCHEMA:
{{
  "vehicle_drivable": "TRUE" | "FALSE" | "UNKNOWN",
  "vehicle_drivable_evidence": "<exact quote or empty>",
  "towing_required": "TRUE" | "FALSE" | "UNKNOWN",
  "towing_evidence": "<exact quote or empty>",
  "damage_zones": [
    {{
      "zone": "<exact zone name from allowed list>",
      "evidence": "<exact quote from transcript>"
    }}
  ],
  "third_party_or_injury": "TRUE" | "FALSE" | "UNKNOWN",
  "third_party_evidence": "<exact quote or empty>"
}}

### FEW-SHOT EXAMPLE:
User Transcript:
"Sir meri gaadi ek khambe se takra gayi, windshield toot gaya hai aur driver side ka door dab gaya hai. Gaadi dheere dheere chal sakti hai, tow ki zaroorat nahi, kisi ko chot nahi lagi."

Response:
{{
  "vehicle_drivable": "TRUE",
  "vehicle_drivable_evidence": "Gaadi dheere dheere chal sakti hai",
  "towing_required": "FALSE",
  "towing_evidence": "tow ki zaroorat nahi",
  "damage_zones": [
    {{
      "zone": "Windshield",
      "evidence": "windshield toot gaya hai"
    }},
    {{
      "zone": "Door",
      "evidence": "door dab gaya hai"
    }}
  ],
  "third_party_or_injury": "FALSE",
  "third_party_evidence": "kisi ko chot nahi lagi"
}}
"""
    return system_prompt, allowed_zones

def strip_code_fences(text: str) -> str:
    """Strip markdown code block fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first line (e.g. ```json)
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def strip_chars(text: str) -> str:
    """Remove spaces, hyphens, and punctuation, and convert to lowercase."""
    if not text:
        return ""
    return re.sub(r"[\s\-_" + re.escape(string.punctuation) + r"।॥]", "", text.lower())

def has_towing_evidence_support(evidence: str) -> bool:
    """Check if evidence quote contains a required towing keyword or pull phrase."""
    if not evidence:
        return False
    ev_lower = evidence.lower()
    towing_keywords = ["tow", "crane", "flatbed", "recovery", "टो", "क्रेन"]
    for kw in towing_keywords:
        if kw in ev_lower:
            return True
    pull_phrases = ["pull", "khinch", "kheench", "khench", "uthana", "uthane", "uthwa", "खींच", "उठाने", "उठवा"]
    for phrase in pull_phrases:
        if phrase in ev_lower:
            return True
    return False

def validate_fnol(fnol: FNOL, transcript: str, taxonomy: dict) -> FNOL:
    """Pure validation function for FNOL ensuring exact evidence substrings, keyword grounding, and taxonomy aliases."""
    taxonomy_zones = taxonomy.get("zones", {})
    allowed_zones = set(taxonomy_zones.keys())

    # a & c: vehicle_drivable
    if fnol.vehicle_drivable_evidence and fnol.vehicle_drivable_evidence not in transcript:
        fnol.vehicle_drivable_evidence = ""
        fnol.vehicle_drivable = "UNKNOWN"
    elif fnol.vehicle_drivable in ("TRUE", "FALSE") and not fnol.vehicle_drivable_evidence:
        fnol.vehicle_drivable = "UNKNOWN"

    # a & b: towing_required
    if fnol.towing_evidence and fnol.towing_evidence not in transcript:
        fnol.towing_evidence = ""
        fnol.towing_required = "UNKNOWN"
    elif fnol.towing_required == "TRUE":
        if not has_towing_evidence_support(fnol.towing_evidence):
            fnol.towing_required = "UNKNOWN"
            fnol.towing_evidence = ""
    elif fnol.towing_required == "FALSE" and not fnol.towing_evidence:
        fnol.towing_required = "UNKNOWN"

    # a & c: third_party_or_injury
    if fnol.third_party_evidence and fnol.third_party_evidence not in transcript:
        fnol.third_party_evidence = ""
        fnol.third_party_or_injury = "UNKNOWN"
    elif fnol.third_party_or_injury in ("TRUE", "FALSE") and not fnol.third_party_evidence:
        fnol.third_party_or_injury = "UNKNOWN"

    # a & d: damage_zones
    verified_zones: list[DamageZone] = []
    for item in fnol.damage_zones:
        # Zones not in taxonomy are dropped
        if item.zone not in allowed_zones:
            continue
        # Exact substring check
        if not item.evidence or item.evidence not in transcript:
            continue
        # Evidence must contain at least one alias of that zone (case-insensitive, no hyphens/spaces/punct)
        norm_ev = strip_chars(item.evidence)
        aliases = taxonomy_zones.get(item.zone, [])
        candidates = set(aliases) | {item.zone}
        has_alias = any(strip_chars(a) in norm_ev for a in candidates if strip_chars(a))
        if has_alias:
            verified_zones.append(item)

    fnol.damage_zones = verified_zones
    return fnol

def clean_and_verify_fnol_with_stats(fnol: FNOL, transcript: str, allowed_zones: set[str]) -> tuple[FNOL, int]:
    """Verify evidence quotes are exact substrings and zones belong to taxonomy. Returns (fnol, dropped_evidence_count)."""
    dropped_count = 0
    if fnol.vehicle_drivable_evidence and fnol.vehicle_drivable_evidence not in transcript:
        dropped_count += 1
    if fnol.towing_evidence and fnol.towing_evidence not in transcript:
        dropped_count += 1
    if fnol.third_party_evidence and fnol.third_party_evidence not in transcript:
        dropped_count += 1
    for item in fnol.damage_zones:
        if item.evidence and item.evidence not in transcript:
            dropped_count += 1

    tax = load_taxonomy()
    validated = validate_fnol(fnol, transcript, tax)
    return validated, dropped_count

def clean_and_verify_fnol(fnol: FNOL, transcript: str, allowed_zones: set[str]) -> FNOL:
    """Verify evidence quotes are exact substrings and zones belong to taxonomy."""
    verified, _ = clean_and_verify_fnol_with_stats(fnol, transcript, allowed_zones)
    return verified

def extract_fnol_with_stats(transcript: str) -> tuple[FNOL, int]:
    """Extract structured FNOL and return (FNOL, dropped_evidence_count)."""
    system_prompt, allowed_zones = build_system_prompt()
    tax = load_taxonomy()
    zones = tax.get("zones", {})
    hints = find_taxonomy_hints(transcript, zones)
    hints_text = ""
    if hints:
        hints_text = "\n\nDetected keyword hints (verify context and exact evidence quote):\n" + "\n".join(f"- {h}" for h in hints)

    prompt = f"Transcript:\n{transcript}{hints_text}"
    last_err = None
    for attempt in range(2):
        try:
            raw = call_llm(system_prompt, prompt)
            data = json.loads(strip_code_fences(raw))
            fnol = FNOL.model_validate(data)
            return clean_and_verify_fnol_with_stats(fnol, transcript, allowed_zones)
        except Exception as e:
            last_err = e
            prompt = f"Your previous response failed or was not valid JSON ({e}). Please extract the FNOL and output ONLY valid JSON matching the schema for this transcript:\n{transcript}{hints_text}"

    raise RuntimeError(f"FNOL extraction failed after retry: {last_err}") from last_err

def extract_fnol(transcript: str) -> FNOL:
    """Extract structured FNOL from transcript with strict taxonomy and substring validation."""
    fnol, _ = extract_fnol_with_stats(transcript)
    return fnol
