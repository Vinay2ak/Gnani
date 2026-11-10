import { FNOL } from '../types';

export function getVerdictSentence(fnol: FNOL): string {
  const parts: string[] = [];

  // Drivability
  if (fnol.vehicle_drivable === 'FALSE') {
    parts.push('Vehicle cannot move.');
  } else if (fnol.vehicle_drivable === 'TRUE') {
    parts.push('Vehicle can be driven.');
  }

  // Towing & Injury combined phrasing for conciseness
  const towingUnknown = fnol.towing_required === 'UNKNOWN';
  const injuryUnknown = fnol.third_party_or_injury === 'UNKNOWN';

  if (fnol.vehicle_drivable === 'UNKNOWN' && towingUnknown && injuryUnknown) {
    return 'Drivability, towing, and injury not stated.';
  }

  if (towingUnknown && injuryUnknown) {
    parts.push('Towing and injury not stated.');
  } else {
    // Towing
    if (fnol.towing_required === 'TRUE') {
      parts.push('Towing required.');
    } else if (fnol.towing_required === 'FALSE') {
      parts.push('No tow needed.');
    } else {
      parts.push('Towing not stated.');
    }

    // Injury / Third Party
    if (fnol.third_party_or_injury === 'TRUE') {
      parts.push('Injury or third party involved.');
    } else if (fnol.third_party_or_injury === 'FALSE') {
      parts.push('No injury or third party.');
    } else {
      parts.push('Injury not stated.');
    }
  }

  return parts.join(' ');
}

export function getQueueVerdictLine(fnol: FNOL): string {
  const tokens: string[] = [];

  if (fnol.vehicle_drivable === 'FALSE') {
    tokens.push('Cannot move');
  } else if (fnol.vehicle_drivable === 'TRUE') {
    tokens.push('Drivable');
  } else {
    tokens.push('Drivable?');
  }

  if (fnol.towing_required === 'TRUE') {
    tokens.push('Tow needed');
  } else if (fnol.towing_required === 'FALSE') {
    tokens.push('No tow');
  }

  if (fnol.third_party_or_injury === 'TRUE') {
    tokens.push('Injury');
  }

  return tokens.join(' · ');
}

export function getConfirmationQuestions(fnol: FNOL): string[] {
  const questions: string[] = [];

  if (fnol.vehicle_drivable === 'UNKNOWN') {
    questions.push('Ask: can the vehicle be driven?');
  }
  if (fnol.towing_required === 'UNKNOWN') {
    questions.push('Ask: does the vehicle need towing?');
  }
  if (fnol.third_party_or_injury === 'UNKNOWN') {
    questions.push('Ask: was anyone hurt, or was another vehicle involved?');
  }
  if (!fnol.damage_zones || fnol.damage_zones.length === 0) {
    questions.push('Ask: which parts are damaged?');
  }

  return questions;
}

