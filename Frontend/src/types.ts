export type TriState = 'TRUE' | 'FALSE' | 'UNKNOWN';

export type ThemeMode = 'light' | 'dark' | 'system';

export interface DamageZone {
  zone: string;
  evidence: string;
}

export interface FNOL {
  vehicle_drivable: TriState;
  vehicle_drivable_evidence: string;
  towing_required: TriState;
  towing_evidence: string;
  damage_zones: DamageZone[];
  third_party_or_injury: TriState;
  third_party_evidence: string;
}

export interface Policy {
  policy_number: string;
  holder_name: string;
  vehicle_make_model: string;
  registration_number: string;
  coverage_type: string;
  towing_covered: boolean;
}

export interface ClaimTimings {
  stt_seconds: number;
  llm_seconds: number;
  total_seconds: number;
}

export interface Claim {
  id: string;
  phone?: string | null;
  policy?: Policy | null;
  transcript: string;
  fnol: FNOL;
  timings: ClaimTimings;
  status: 'pending' | 'approved';
  workshop?: string | null;
  audio_path?: string;
}
