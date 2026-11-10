# Bima-Setu (FNOL Co-Pilot)

An AI-assisted First Notice of Loss (FNOL) co-pilot for motor insurance claims. Designed for callers reporting vehicular accidents in noisy Hindi-English (Hinglish), Bima-Setu extracts structured loss details where evidence quotes must appear in the transcript and, for towing and zones, must contain a supporting keyword to assist human adjusters. A human adjuster retains sole approval authority; the AI system never decides claims.

---

## Problem

Following a road accident, drivers call insurance claims helplines in high-stress states, speaking colloquial Hindi-English mixed with local mechanical slang (e.g., *kamani*, *dickey*, *tie-rod*).

Traditional automated interactive voice response (IVR) systems struggle because:
- Ambient road, traffic, and engine noise degrade standard speech recognition.
- Drivers mix languages, use non-standard part names, and omit formal terminology.
- Fully autonomous AI decision-making poses severe compliance and financial risks.

Bima-Setu addresses this by extracting structured, verifiable FNOL claims with exact-substring evidence quotes for human verification, followed by synthesized audio read-back to the caller.

---

## Pipeline Architecture

The end-to-end processing pipeline operates sequentially:

```
Caller Audio (.ogg / .wav / .mp3)
   │
   ▼
1. Gnani Prisma STT (prisma-v3.0, language_code: hi-IN)
   │  ↳ Cached in transcripts/<clip>.prisma-v3.0.json
   ▼
2. Taxonomy Pre-Pass & Prompt Framing
   │  ↳ Scans transcript for taxonomy aliases (hyphen/space/case-insensitive)
   ▼
3. LLM Extraction (gemini-3.5-flash-lite)
   │  ↳ Extracts tri-state values (TRUE / FALSE / UNKNOWN)
   │  ↳ Strictly enforces exact-substring evidence quotes & taxonomy zones
   ▼
4. Structured FNOL Record & Timings
   │  ↳ Saved to outputs/<clip>.json
   ▼
5. Gnani Timbre TTS Read-Back (timbre-v2.5, voice: Nalini)
   │  ↳ Hinglish summary cached in readback/<claim_id>.wav
   ▼
6. Human Adjuster Dashboard (React + Vite + Tailwind)
   │  ↳ Evidence highlighted in transcript; adjuster approves towing & workshop
```

### Core Extraction Invariants
- **Exact Substring Evidence**: Every asserted state (`vehicle_drivable`, `towing_required`, `third_party_or_injury`, `damage_zones`) must carry an evidence quote that is an exact substring of the transcript. If the quote does not match verbatim, the evidence is discarded and the field is reset to `UNKNOWN`.
- **Closed Damage Taxonomy**: Damage zones must strictly belong to `damage_taxonomy.json`. Hallucinated zones and unverified slang (e.g., *chimta*) are dropped.
- **Towing & Negation Rules**: `towing_required` is `TRUE` only if an explicit request for towing, crane, flatbed, or recovery vehicle is present; `FALSE` only if explicitly denied; otherwise `UNKNOWN`. Parts explicitly described as undamaged are excluded from damage zones.

---

## Models Used

| Component | Model Name | Configuration Details |
| :--- | :--- | :--- |
| **Speech-to-Text (STT)** | `prisma-v3.0` | Gnani Vachana STT v3 (`hi-IN`), multipart audio upload |
| **Text-to-Speech (TTS)** | `timbre-v2.5` | Gnani Timbre REST endpoint, voice `Nalini`, language `hi-IN`, speed `1.0`, audio config: 48 kHz linear PCM WAV |
| **LLM Extraction** | `gemini-3.5-flash-lite` | Native Google Gemini `generateContent` endpoint, `minimal` thinking level, temperature default |

---

## How to Run

### 1. Prerequisites and Environment
- OS: Windows / Linux / macOS
- Python 3.10+ (tested on Python 3.13)
- Node.js 18+ and npm

Activate your Python virtual environment:
```powershell
.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate  # Linux / macOS
```

### 2. Environment Variables (.env)
Create a `.env` file in the project root containing the following key names:
```ini
GNANI_API_KEY=your_gnani_api_key_here
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta
LLM_MODEL=gemini-3.5-flash-lite
LLM_API_KEY=your_gemini_api_key_here
```
*(Never hardcode, commit, or log these secrets).*

### 3. Verification & Offline Checks
Run the read-only integrity checker to verify clips, ground truth, and taxonomy:
```powershell
python check_setup.py
```

Run the offline API test suite (all network calls monkeypatched):
```powershell
python test_api_offline.py
```

### 4. Running Batch Pipeline & Evaluation
Execute pipeline over all clips in `ground_truth.json`:
```powershell
python run_all.py
```

Generate the failure diagnosis and evaluation report:
```powershell
python report.py
```

### 5. Running the Full Stack (API & Dashboard)
**Terminal 1 — FastAPI Backend:**
```powershell
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — React Adjuster Frontend:**
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Evaluation Results

Numbers pending re-evaluation after label and validator fixes.

The evaluation covers 12 audio clips across 3 sets: clean audio (`quite1`–`quite4`), noisy audio (`noisy1`–`noisy4`), and held-out clips (`held1`–`held4`).

### Execution Latencies (from `run_summary.md`)

| Clip | Status | STT (s) | LLM (s) | Total (s) |
| :--- | :--- | :--- | :--- | :--- |
| `quite1` | completed | 0.533s | 2.151s | 2.684s |
| `quite2` | completed | 0.599s | 1.861s | 2.46s |
| `quite3` | completed | 0.526s | 1.789s | 2.315s |
| `quite4` | completed | 0.479s | 1.573s | 2.052s |
| `noisy1` | completed | 0.553s | 1.502s | 2.055s |
| `noisy2` | completed | 0.535s | 1.577s | 2.112s |
| `noisy3` | completed | 0.542s | 1.473s | 2.015s |
| `noisy4` | completed | 0.561s | 1.558s | 2.119s |
| `held1` | completed | 0.409s | 1.307s | 1.716s |
| `held2` | completed | 0.379s | 1.26s | 1.639s |
| `held3` | completed | 0.421s | 1.579s | 2.0s |
| `held4` | completed | 0.369s | 1.381s | 1.75s |

- **Average Total Latency**: `2.076s`
- **Max Total Latency**: `2.684s`

### Per-Condition Field Accuracy (from `report.md`)

| Condition | Evaluated Clips | Drivable Acc | Towing Acc | Third-Party Acc | Exact Zones Acc |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **clean** | 6 | 66.7% (4/6) | 66.7% (4/6) | 66.7% (4/6) | 50.0% (3/6) |
| **noisy** | 6 | 66.7% (4/6) | 66.7% (4/6) | 100.0% (6/6) | 50.0% (3/6) |

### Failure Root-Cause Attribution
- **STT_MISSED**: `11` *(keyword or acoustic token dropped or mistranscribed by speech recognition before reaching the LLM)*
- **LLM_MISSED**: `1` *(target concept present in transcript text, but model omitted extraction)*

---

## Limitations

- **Small Sample Size**: The evaluation dataset comprises only 12 audio clips voiced by a single speaker.
- **Synthetic Test Scripts Only**: All clips are staged synthetic enactments (Scripts A–H). No live, panic-situation, or production insurance policyholder calls were tested.
- **Acoustic STT Degradation**: In several clips, the speech recognition engine mistranscribed or dropped key domain terms under background acoustic conditions (e.g., "tow" transcribed as Hindi "तो", "tie-rod" transcribed as "tyre road"), triggering downstream `STT_MISSED` failures.
- **Held-Out Clips First-Run Outcome**: Ground truth labels for `held1`–`held4` were established blindly prior to executing the pipeline, showing lower accuracy due to acoustic vocabulary variance (such as heavy commercial vehicle parts).
- **LLM Latency Variance**: Latency depends on external network conditions and API response times (ranging from 1.26s to 2.15s per extraction).
- **Cloud Model Deployment**: Evon is open-weight and needs a dedicated GPU, so extraction used hosted Gemini Flash-Lite.
- **Zero Automated Claims Authorization**: The software is strictly an assistive co-pilot; it is not equipped or certified to make unassisted claim settlements or denials.

