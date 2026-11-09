from typing import Literal
from pydantic import BaseModel

Tri = Literal["TRUE", "FALSE", "UNKNOWN"]

class DamageZone(BaseModel):
    zone: str        # damage_taxonomy.json se ek naam
    evidence: str    # transcript ka exact quote

class FNOL(BaseModel):
    vehicle_drivable: Tri
    vehicle_drivable_evidence: str = ""
    towing_required: Tri
    towing_evidence: str = ""
    damage_zones: list[DamageZone] = []
    third_party_or_injury: Tri
    third_party_evidence: str = ""
