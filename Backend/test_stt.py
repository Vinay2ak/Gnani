import os, sys, json, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
KEY = os.environ.get("GNANI_API_KEY", "").strip()

def transcribe(path, model, lang="hi-IN"):
    out = Path("transcripts") / f"{Path(path).stem}.{model}.json"
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    
    key = os.environ.get("GNANI_API_KEY", KEY).strip()
    if not key:
        raise ValueError("GNANI_API_KEY environment variable is not set")
    
    data = {"language_code": lang}
    if model == "prisma-v3.0":
        data["model"] = model
    with open(path, "rb") as f:
        r = requests.post(
            "https://api.vachana.ai/stt/v3",
            headers={"X-API-Key-ID": key},
            files={"audio_file": (Path(path).name, f)},
            data=data, timeout=60,
        )
    if not r.ok:
        print(r.status_code, r.text[:300])
    r.raise_for_status()
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(r.json(), ensure_ascii=False, indent=2), encoding="utf-8")
    return r.json()

if __name__ == "__main__":
    for p in sys.argv[1:]:
        for m in ["prisma-v3.0"]:
            res = transcribe(p, m)
            print(f"\n{p} [{m}] latency={res.get('end_to_end_latency')}")
            print(res["transcript"])