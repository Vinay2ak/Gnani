import { FNOL } from '../types';

export interface IndexedQuote {
  index: number;
  text: string;
}

export function extractDistinctQuotes(fnol: FNOL): IndexedQuote[] {
  const rawList: string[] = [];

  if (fnol.vehicle_drivable_evidence?.trim()) {
    rawList.push(fnol.vehicle_drivable_evidence.trim());
  }
  if (fnol.towing_evidence?.trim()) {
    rawList.push(fnol.towing_evidence.trim());
  }
  if (fnol.third_party_evidence?.trim()) {
    rawList.push(fnol.third_party_evidence.trim());
  }
  if (Array.isArray(fnol.damage_zones)) {
    for (const dz of fnol.damage_zones) {
      if (dz.evidence?.trim()) {
        rawList.push(dz.evidence.trim());
      }
    }
  }

  // Deduplicate while maintaining first-seen order
  const seen = new Set<string>();
  const distinct: IndexedQuote[] = [];

  for (const quote of rawList) {
    if (!seen.has(quote)) {
      seen.add(quote);
      distinct.push({
        index: distinct.length + 1,
        text: quote,
      });
    }
  }

  return distinct;
}

export interface QuoteInterval {
  start: number;
  end: number;
  indices: number[];
}

export function buildTranscriptIntervals(
  transcript: string,
  quotes: IndexedQuote[]
): QuoteInterval[] {
  if (!transcript || quotes.length === 0) return [];

  const rawIntervals: QuoteInterval[] = [];

  for (const q of quotes) {
    let startIndex = 0;
    while (startIndex < transcript.length) {
      const pos = transcript.indexOf(q.text, startIndex);
      if (pos === -1) break;
      rawIntervals.push({
        start: pos,
        end: pos + q.text.length,
        indices: [q.index],
      });
      startIndex = pos + Math.max(1, q.text.length);
    }
  }

  if (rawIntervals.length === 0) return [];

  // Sort by start position ascending, then end descending
  rawIntervals.sort((a, b) => a.start - b.start || b.end - a.end);

  // Merge overlapping and contiguous intervals
  const merged: QuoteInterval[] = [{ ...rawIntervals[0], indices: [...rawIntervals[0].indices] }];

  for (let i = 1; i < rawIntervals.length; i++) {
    const cur = rawIntervals[i];
    const prev = merged[merged.length - 1];

    if (cur.start <= prev.end) {
      prev.end = Math.max(prev.end, cur.end);
      for (const idx of cur.indices) {
        if (!prev.indices.includes(idx)) {
          prev.indices.push(idx);
        }
      }
      prev.indices.sort((a, b) => a - b);
    } else {
      merged.push({ ...cur, indices: [...cur.indices] });
    }
  }

  return merged;
}

