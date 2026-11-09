# Synthetic Policy Database (Strictly fictional demo data)
POLICIES = {
    "9876543210": {
        "policy_number": "POL-SYNTH-1001",
        "holder_name": "Aarav Sharma",
        "vehicle_make_model": "Maruti Suzuki Swift VXi (2022)",
        "registration_number": "DL-01-AB-1234",
        "coverage_type": "Comprehensive",
        "towing_covered": True,
    },
    "9876543211": {
        "policy_number": "POL-SYNTH-1002",
        "holder_name": "Priya Verma",
        "vehicle_make_model": "Hyundai Creta SX (2023)",
        "registration_number": "MH-02-CD-5678",
        "coverage_type": "Zero Depreciation",
        "towing_covered": True,
    },
    "9876543212": {
        "policy_number": "POL-SYNTH-1003",
        "holder_name": "Rajesh Patel",
        "vehicle_make_model": "Tata Nexon XZ+ (2021)",
        "registration_number": "GJ-01-EF-9012",
        "coverage_type": "Comprehensive",
        "towing_covered": False,
    },
    "9876543213": {
        "policy_number": "POL-SYNTH-1004",
        "holder_name": "Sunita Rao",
        "vehicle_make_model": "Mahindra XUV700 AX7 (2024)",
        "registration_number": "KA-05-GH-3456",
        "coverage_type": "Bumper-to-Bumper",
        "towing_covered": True,
    },
    "9876543214": {
        "policy_number": "POL-SYNTH-1005",
        "holder_name": "Vikram Singh",
        "vehicle_make_model": "Honda City ZX (2020)",
        "registration_number": "UP-16-IJ-7890",
        "coverage_type": "Third Party Only",
        "towing_covered": False,
    },
}

def lookup_policy(phone: str | None) -> dict | None:
    """Lookup synthetic policy by phone string, or return None if not found."""
    if not phone:
        return None
    # Normalize phone: remove spaces, dashes, +91 prefix if any
    cleaned = phone.replace(" ", "").replace("-", "")
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    return POLICIES.get(cleaned)

