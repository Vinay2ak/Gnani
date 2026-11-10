import { Claim } from './types';

export const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (import.meta.env.PROD ? 'https://gnani-vrwd.onrender.com' : 'http://127.0.0.1:8000');

export async function fetchClaims(signal?: AbortSignal): Promise<Claim[]> {
  const res = await fetch(`${API_BASE}/claims`, { signal });
  if (!res.ok) {
    throw new Error(`Failed to fetch claims: HTTP ${res.status}`);
  }
  return res.json();
}

export async function uploadClaim(audioFile: File, phone?: string): Promise<Claim> {
  const formData = new FormData();
  formData.append('audio_file', audioFile);
  if (phone && phone.trim()) {
    formData.append('phone', phone.trim());
  }

  const res = await fetch(`${API_BASE}/claims`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.detail) {
        errorDetail = data.detail;
      }
    } catch {
      // Use HTTP status fallback
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export async function approveClaim(claimId: string): Promise<Claim> {
  const res = await fetch(`${API_BASE}/claims/${encodeURIComponent(claimId)}/approve`, {
    method: 'POST',
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.detail) {
        errorDetail = data.detail;
      }
    } catch {
      // Use fallback
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export async function fetchReadbackAudio(claimId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/claims/${encodeURIComponent(claimId)}/readback`, {
    method: 'POST',
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.detail) {
        errorDetail = data.detail;
      }
    } catch {
      // Use fallback
    }
    throw new Error(errorDetail);
  }

  return res.blob();
}

