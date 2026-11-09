import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

RETRY_STATUS = {500, 503, 504}   # temporary errors: dobara try karo

def call_llm(system: str, user: str) -> str:
    """Gemini native generateContent. Retries temporary errors, joins all text parts."""
    base_url = os.environ.get("LLM_BASE_URL")
    model = os.environ.get("LLM_MODEL")
    api_key = os.environ.get("LLM_API_KEY")

    missing = [n for n, v in [("LLM_BASE_URL", base_url), ("LLM_MODEL", model),
                              ("LLM_API_KEY", api_key)] if not v]
    if missing:
        raise ValueError(f"Missing required environment variable(s) in .env: {', '.join(missing)}")

    url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "thinkingConfig": {"thinkingLevel": "minimal"},
            "responseMimeType": "application/json",
        },
    }

    last_error = None
    for attempt in range(4):                      # 1 try + 3 retries
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.RequestException as e:
            last_error = f"network error: {e}"
        else:
            if resp.ok:
                data = resp.json()
                cand = (data.get("candidates") or [{}])[0]
                parts = cand.get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)   # saare parts jodo
                finish = cand.get("finishReason")
                if text.strip() and finish in (None, "STOP"):
                    return text
                last_error = f"bad response (finishReason={finish}): {str(data)[:200]}"
            elif resp.status_code in RETRY_STATUS:
                last_error = f"[{resp.status_code}] {resp.text[:200]}"
            else:
                raise RuntimeError(f"LLM API request failed [{resp.status_code}]: {resp.text}")
        if attempt < 3:
            time.sleep(5 * (attempt + 1))         # 5s, 10s, 15s ruko
    raise RuntimeError(f"LLM failed after retries: {last_error}")