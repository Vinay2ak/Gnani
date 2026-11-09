import io
import sys
from pathlib import Path
from unittest import mock

try:
    from fastapi.testclient import TestClient
except Exception as e:
    print(f"FAIL: Could not import TestClient ({e}). Please install httpx: pip install httpx")
    sys.exit(1)

from Schema import FNOL, DamageZone
from api import app, claims_db

client = TestClient(app)

def run_tests():
    all_passed = True
    claims_db.clear()

    # Shared mock data
    mock_stt_result = {
        "transcript": "Hello sir, gaadi ka accident ho gaya hai",
        "end_to_end_latency": 0.25,
    }
    mock_fnol_result = FNOL(
        vehicle_drivable="FALSE",
        vehicle_drivable_evidence="gaadi nahi chal rahi",
        towing_required="TRUE",
        towing_evidence="tow bhejo",
        damage_zones=[
            DamageZone(zone="Front Bumper / Bonnet", evidence="bumper toot gaya")
        ],
        third_party_or_injury="UNKNOWN",
        third_party_evidence="",
    )

    created_claim_id = None

    # Test 1: Upload dummy .ogg returns claim with status pending
    try:
        with mock.patch("api.transcribe", return_value=mock_stt_result), \
             mock.patch("api.extract_fnol", return_value=mock_fnol_result):
            fake_ogg = b"OggS" + b"\x00" * 100
            resp = client.post(
                "/claims",
                data={"phone": "9876543210"},
                files={"audio_file": ("test.ogg", fake_ogg, "audio/ogg")},
            )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert data.get("status") == "pending", f"Expected status 'pending', got {data.get('status')}"
            assert "id" in data, "Claim id missing from response"
            created_claim_id = data["id"]
            print("PASS: Upload dummy .ogg returns claim with status pending")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Upload dummy .ogg test failed: {e}")

    # Test 2: GET /claims lists it
    try:
        resp = client.get("/claims")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        claims_list = resp.json()
        ids = [c["id"] for c in claims_list]
        assert created_claim_id in ids, f"Created claim {created_claim_id} not found in /claims list"
        print("PASS: GET /claims lists created claim")
    except Exception as e:
        all_passed = False
        print(f"FAIL: GET /claims failed: {e}")

    # Test 3: Upload .txt is rejected
    try:
        fake_txt = b"This is a text file, not audio."
        resp = client.post(
            "/claims",
            files={"audio_file": ("test.txt", fake_txt, "text/plain")},
        )
        assert resp.status_code == 400, f"Expected 400 for .txt file, got {resp.status_code}"
        print("PASS: Upload .txt file is rejected with HTTP 400")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Upload .txt rejection test failed: {e}")

    # Test 4: Pipeline error returns 502 and creates no claim
    try:
        count_before = len(claims_db)
        with mock.patch("api.transcribe", side_effect=RuntimeError("Prisma STT connection failed")):
            fake_ogg = b"OggS" + b"\x00" * 100
            resp = client.post(
                "/claims",
                files={"audio_file": ("error_test.ogg", fake_ogg, "audio/ogg")},
            )
            assert resp.status_code == 502, f"Expected 502, got {resp.status_code}: {resp.text}"
            assert len(claims_db) == count_before, "Failed claim was incorrectly stored in claims_db"
            print("PASS: Pipeline error returns HTTP 502 and creates no claim")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Pipeline error handling test failed: {e}")

    # Test 5: Readback twice calls TTS only once and returns the same file
    try:
        dummy_wav_content = b"RIFF" + b"\x00" * 40
        tts_call_count = 0

        def fake_synthesize(text, out_path):
            nonlocal tts_call_count
            tts_call_count += 1
            p = Path(out_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(dummy_wav_content)
            return p

        with mock.patch("api.synthesize_readback", side_effect=fake_synthesize):
            # First readback call (synthesizes and caches)
            resp1 = client.post(f"/claims/{created_claim_id}/readback")
            assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}"
            assert resp1.content == dummy_wav_content

            # Second readback call (must serve from cache)
            resp2 = client.post(f"/claims/{created_claim_id}/readback")
            assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}"
            assert resp2.content == dummy_wav_content

            assert tts_call_count == 1, f"TTS was called {tts_call_count} times, expected exactly 1"
            print("PASS: Readback called twice invokes TTS only once and returns cached audio")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Readback caching test failed: {e}")

    # Test 6: Approve once works, second approve is rejected
    try:
        # First approve: pending -> approved
        resp_app1 = client.post(f"/claims/{created_claim_id}/approve")
        assert resp_app1.status_code == 200, f"Expected 200, got {resp_app1.status_code}"
        data1 = resp_app1.json()
        assert data1.get("status") == "approved", f"Expected status 'approved', got {data1.get('status')}"
        assert data1.get("workshop"), "Assigned workshop missing"

        # Second approve: already approved -> 400 rejection
        resp_app2 = client.post(f"/claims/{created_claim_id}/approve")
        assert resp_app2.status_code == 400, f"Expected 400 for already approved claim, got {resp_app2.status_code}"
        print("PASS: First approve succeeds and second approve is rejected with HTTP 400")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Approve idempotency guard test failed: {e}")

    # Cleanup any mock uploaded / readback test files
    for p in Path("uploads").glob(f"{created_claim_id}*"):
        p.unlink(missing_ok=True)
    for p in Path("readback").glob(f"{created_claim_id}*"):
        p.unlink(missing_ok=True)

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()

