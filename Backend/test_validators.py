import sys
from Schema import FNOL, DamageZone
from extract import validate_fnol, load_taxonomy

def run_tests():
    taxonomy = load_taxonomy()
    all_passed = True

    # Test 1: towing TRUE with weak evidence -> UNKNOWN and evidence cleared
    try:
        t1_transcript = "meri car achanak se band pad gayi hai"
        f1 = FNOL(
            vehicle_drivable="UNKNOWN",
            towing_required="TRUE",
            towing_evidence="band pad gayi hai",  # Weak evidence, lacks tow/crane/etc.
            damage_zones=[],
            third_party_or_injury="UNKNOWN",
        )
        res1 = validate_fnol(f1, t1_transcript, taxonomy)
        assert res1.towing_required == "UNKNOWN", f"Expected UNKNOWN, got {res1.towing_required}"
        assert res1.towing_evidence == "", f"Expected empty evidence, got '{res1.towing_evidence}'"
        print("PASS: towing TRUE with weak evidence -> UNKNOWN and evidence cleared")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Test 1 failed: {e}")

    # Test 2: towing TRUE with 'crane' -> kept
    try:
        t2_transcript = "yahan turant ek crane bhej dijiye"
        f2 = FNOL(
            vehicle_drivable="UNKNOWN",
            towing_required="TRUE",
            towing_evidence="crane bhej dijiye",  # Contains 'crane'
            damage_zones=[],
            third_party_or_injury="UNKNOWN",
        )
        res2 = validate_fnol(f2, t2_transcript, taxonomy)
        assert res2.towing_required == "TRUE", f"Expected TRUE, got {res2.towing_required}"
        assert res2.towing_evidence == "crane bhej dijiye", f"Expected 'crane bhej dijiye', got '{res2.towing_evidence}'"
        print("PASS: towing TRUE with 'crane' -> kept")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Test 2 failed: {e}")

    # Test 3: a zone whose evidence has no alias -> dropped
    try:
        t3_transcript = "gaadi ke aage ka hissa dab gaya hai"
        f3 = FNOL(
            vehicle_drivable="UNKNOWN",
            towing_required="UNKNOWN",
            damage_zones=[
                DamageZone(
                    zone="Front Cooling System (Radiator)",
                    evidence="aage ka hissa dab gaya hai",  # Does not contain radiator/rediator alias
                )
            ],
            third_party_or_injury="UNKNOWN",
        )
        res3 = validate_fnol(f3, t3_transcript, taxonomy)
        assert len(res3.damage_zones) == 0, f"Expected 0 damage zones, got {len(res3.damage_zones)}"
        print("PASS: a zone whose evidence has no alias -> dropped")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Test 3 failed: {e}")

    # Test 4: evidence not in the transcript -> cleared / dropped
    try:
        t4_transcript = "sir bumper pe dent aaya hai"
        f4 = FNOL(
            vehicle_drivable="FALSE",
            vehicle_drivable_evidence="gaadi nahi chalegi",  # Not in transcript!
            towing_required="UNKNOWN",
            damage_zones=[
                DamageZone(
                    zone="Front Bumper / Bonnet",
                    evidence="bumper poora toot gaya",  # Not in transcript!
                )
            ],
            third_party_or_injury="UNKNOWN",
        )
        res4 = validate_fnol(f4, t4_transcript, taxonomy)
        assert res4.vehicle_drivable == "UNKNOWN", f"Expected drivable UNKNOWN, got {res4.vehicle_drivable}"
        assert res4.vehicle_drivable_evidence == "", f"Expected empty drivable evidence, got '{res4.vehicle_drivable_evidence}'"
        assert len(res4.damage_zones) == 0, f"Expected 0 damage zones, got {len(res4.damage_zones)}"
        print("PASS: evidence not in the transcript -> cleared / dropped")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Test 4 failed: {e}")

    # Test 5: drivable FALSE with empty evidence -> UNKNOWN
    try:
        t5_transcript = "gaadi road kinare khadi hai"
        f5 = FNOL(
            vehicle_drivable="FALSE",
            vehicle_drivable_evidence="",  # Empty evidence for FALSE
            towing_required="UNKNOWN",
            damage_zones=[],
            third_party_or_injury="UNKNOWN",
        )
        res5 = validate_fnol(f5, t5_transcript, taxonomy)
        assert res5.vehicle_drivable == "UNKNOWN", f"Expected UNKNOWN, got {res5.vehicle_drivable}"
        print("PASS: drivable FALSE with empty evidence -> UNKNOWN")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Test 5 failed: {e}")

    # Test 6 (Bonus): verified zone with alias in evidence -> kept
    try:
        t6_transcript = "gaadi ka radiator phat gaya hai"
        f6 = FNOL(
            vehicle_drivable="UNKNOWN",
            towing_required="UNKNOWN",
            damage_zones=[
                DamageZone(
                    zone="Front Cooling System (Radiator)",
                    evidence="radiator phat gaya hai",  # Contains alias 'radiator' and is substring
                )
            ],
            third_party_or_injury="UNKNOWN",
        )
        res6 = validate_fnol(f6, t6_transcript, taxonomy)
        assert len(res6.damage_zones) == 1, f"Expected 1 damage zone, got {len(res6.damage_zones)}"
        assert res6.damage_zones[0].zone == "Front Cooling System (Radiator)"
        print("PASS: verified zone with alias in evidence -> kept")
    except Exception as e:
        all_passed = False
        print(f"FAIL: Test 6 failed: {e}")

    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()

