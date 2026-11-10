# Bima-Setu Pipeline Evaluation Report

## Clip: `quite1` (Condition: `clean`)

**Transcript:** "Hello sir, मेरी गाड़ी का accident हो गया है। highway पे divider से टकरा गई, radiator फट गया है। और पानी बह रहा है, tyre road भी मुड़ गया है, गाड़ी बिल्कुल start नहीं हो रही। चलने लायक नहीं है, तो करनी पड़ेगी। जल्दी कोई भेजिए।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `FALSE` | `FALSE` | ✅ |  |
| towing_required | `UNKNOWN` | `TRUE` | ❌ | `STT_MISSED` |
| third_party_or_injury | `UNKNOWN` | `UNKNOWN` | ✅ |  |

**Damage Zones Comparison:**

- ✅ **Front Cooling System (Radiator)**: Correctly extracted
- ❌ **Front Suspension (Control Arm / Tie-Rod)**: Missing (Diagnosis: `STT_MISSED`)

---

## Clip: `quite2` (Condition: `clean`)

**Transcript:** "सर, छोटा सा accident हुआ है। bumper और head light टूट गया है, टूट गए हैं, लेकिन गाड़ी बिल्कुल ठीक है। चल रही है, radiator को कुछ नहीं हुआ। मैं खुद चला के workshop ले जाऊँगा तो। की जरूरत नहीं, कोई दूसरी गाड़ी involve involve involve नहीं थी और किसी को चोट नहीं लगी।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `TRUE` | `TRUE` | ✅ |  |
| towing_required | `FALSE` | `FALSE` | ✅ |  |
| third_party_or_injury | `FALSE` | `FALSE` | ✅ |  |

**Damage Zones Comparison:**

- ✅ **Front Bumper / Bonnet**: Correctly extracted
- ✅ **Headlight**: Correctly extracted

---

## Clip: `quite3` (Condition: `clean`)

**Transcript:** "सर, पीछे से एक गाड़ी ने जोर से टक्कर मारी, मेरी गाड़ी की डिक्की पीछे पिचक गई है। गाड़ी चल रही है, पर पीछे वाली गाड़ी के driver को चोट लगी है, खून आ रहा।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `TRUE` | `TRUE` | ✅ |  |
| towing_required | `UNKNOWN` | `UNKNOWN` | ✅ |  |
| third_party_or_injury | `TRUE` | `TRUE` | ✅ |  |

**Damage Zones Comparison:**

- ❌ **Rear (Boot / Dickey)**: Missing (Diagnosis: `STT_MISSED`)

---

## Clip: `quite4` (Condition: `clean`)

**Transcript:** "Sir, गाड़ी का engine अचानक से बंद हो गया है और आगे का tyre भी फट गया है। गाड़ी एक... inch pitch, 1 inch भी नहीं ले रही, सड़क के बीच में खड़ी है। crane बिछानी पड़ेगी।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `FALSE` | `FALSE` | ✅ |  |
| towing_required | `TRUE` | `TRUE` | ✅ |  |
| third_party_or_injury | `UNKNOWN` | `UNKNOWN` | ✅ |  |

**Damage Zones Comparison:**

- ✅ **Engine**: Correctly extracted
- ✅ **Wheel / Tyre**: Correctly extracted

---

## Clip: `noisy1` (Condition: `noisy`)

**Transcript:** "Hello sir, मेरी गाड़ी का accident हो गया है। highway पे divider से टकरा गई, radiator फट गया है और पानी बह रहा है। tyre road भी मुर गया है, गाड़ी बिल्कुल start नहीं हो रही, चलने लायक नहीं है। तो करनी पड़ेगी, जल्दी कोई भेजिए।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `FALSE` | `FALSE` | ✅ |  |
| towing_required | `UNKNOWN` | `TRUE` | ❌ | `STT_MISSED` |
| third_party_or_injury | `UNKNOWN` | `UNKNOWN` | ✅ |  |

**Damage Zones Comparison:**

- ✅ **Front Cooling System (Radiator)**: Correctly extracted
- ❌ **Front Suspension (Control Arm / Tie-Rod)**: Missing (Diagnosis: `STT_MISSED`)

---

## Clip: `noisy2` (Condition: `noisy`)

**Transcript:** "सर, छोटा सा accident हुआ है, bumper और headlight टूट गए, टूट गए हैं, लेकिन गाड़ी बिल्कुल ठीक है। चल रही है, radiator को कुछ नहीं हुआ। मैं खुद चला के workshop ले जाऊँगा। तो की जरूरत नहीं, कोई दूसरी गाड़ी involve नहीं थी और किसी को चोट नहीं लगी।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `TRUE` | `TRUE` | ✅ |  |
| towing_required | `FALSE` | `FALSE` | ✅ |  |
| third_party_or_injury | `FALSE` | `FALSE` | ✅ |  |

**Damage Zones Comparison:**

- ✅ **Front Bumper / Bonnet**: Correctly extracted
- ✅ **Headlight**: Correctly extracted

---

## Clip: `noisy3` (Condition: `noisy`)

**Transcript:** "सर, पीछे से एक गाड़ी ने जोर से टक्कर मारी, मेरी गाड़ी की डगी। पिचक गई है, गाड़ी चल रही है, पर पीछे वाली गाड़ी के driver को चोट लगी है। खून आ रहा है।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `TRUE` | `TRUE` | ✅ |  |
| towing_required | `UNKNOWN` | `UNKNOWN` | ✅ |  |
| third_party_or_injury | `TRUE` | `TRUE` | ✅ |  |

**Damage Zones Comparison:**

- ❌ **Rear (Boot / Dickey)**: Missing (Diagnosis: `STT_MISSED`)

---

## Clip: `noisy4` (Condition: `noisy`)

**Transcript:** "Sir, गाड़ी का engine अचानक बंद हो गया है और आगे का tyre भी फट गया है। गाड़ी बीच गाड़ी 1 inch भी नहीं हिल रही, सड़क के बीच में खड़ी है। crane भिजवानी पड़ेगी।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `FALSE` | `FALSE` | ✅ |  |
| towing_required | `TRUE` | `TRUE` | ✅ |  |
| third_party_or_injury | `UNKNOWN` | `UNKNOWN` | ✅ |  |

**Damage Zones Comparison:**

- ✅ **Engine**: Correctly extracted
- ✅ **Wheel / Tyre**: Correctly extracted

---

## Clip: `held1` (Condition: `clean`)

**Transcript:** "Hello, मेरा accident हो गया है, headlight टूट गया है, मुझे जल्दी मदद चाहिए। बाकी मैं अभी देख नहीं पाया।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `UNKNOWN` | `FALSE` | ❌ | Mismatch |
| towing_required | `UNKNOWN` | `TRUE` | ❌ | `STT_MISSED` |
| third_party_or_injury | `UNKNOWN` | `FALSE` | ❌ | Mismatch |

**Damage Zones Comparison:**

- ❌ **Suspension (Leaf Spring)**: Missing (Diagnosis: `STT_MISSED`)
- ❌ **Wheel / Tyre**: Missing (Diagnosis: `STT_MISSED`)
- ❌ **Headlight**: Extra / Unverified in Expected

---

## Clip: `held2` (Condition: `noisy`)

**Transcript:** "सर, highway पे truck ने side shift कर दिया। अ driver side का door damage हुआ है और tyre burst हो गया, गाड़ी हिल नहीं रही। belt bed भेज दीजिए।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `FALSE` | `UNKNOWN` | ❌ | Mismatch |
| towing_required | `UNKNOWN` | `UNKNOWN` | ✅ |  |
| third_party_or_injury | `UNKNOWN` | `UNKNOWN` | ✅ |  |

**Damage Zones Comparison:**

- ❌ **Headlight**: Missing (Diagnosis: `STT_MISSED`)
- ❌ **Door**: Extra / Unverified in Expected
- ❌ **Wheel / Tyre**: Extra / Unverified in Expected

---

## Clip: `held3` (Condition: `clean`)

**Transcript:** "सर, मेरा truck की कमानी टूट गई है और आगे का पहिया टेढ़ा हो गया है। truck बिल्कुल नहीं चल रहा, crane भिजवा दीजिए। कोई दूसरी गाड़ी नहीं थी और किसी। को चोट नहीं लगे।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `FALSE` | `TRUE` | ❌ | Mismatch |
| towing_required | `TRUE` | `UNKNOWN` | ❌ | `LLM_MISSED` |
| third_party_or_injury | `FALSE` | `TRUE` | ❌ | Mismatch |

**Damage Zones Comparison:**

- ❌ **Front Bumper / Bonnet**: Missing (Diagnosis: `STT_MISSED`)
- ❌ **Suspension (Leaf Spring)**: Extra / Unverified in Expected
- ❌ **Wheel / Tyre**: Extra / Unverified in Expected

---

## Clip: `held4` (Condition: `noisy`)

**Transcript:** "Sir, गाड़ी का engine ठीक है, चल रही है, सिर्फ bonnet दब गया है दूसरी गाड़ी वाली। को चोट लगी है, ambulance बुलवा दीजिए।"

| Field | Extracted | Expected | Status | Diagnosis |
| :--- | :--- | :--- | :--- | :--- |
| vehicle_drivable | `TRUE` | `FALSE` | ❌ | Mismatch |
| towing_required | `UNKNOWN` | `TRUE` | ❌ | `STT_MISSED` |
| third_party_or_injury | `TRUE` | `TRUE` | ✅ |  |

**Damage Zones Comparison:**

- ❌ **Door**: Missing (Diagnosis: `STT_MISSED`)
- ❌ **Wheel / Tyre**: Missing (Diagnosis: `STT_MISSED`)
- ❌ **Front Bumper / Bonnet**: Extra / Unverified in Expected

---

## Summary Statistics

### Per-Condition Field Accuracy

| Condition | Evaluated Clips | Drivable Acc | Towing Acc | Third-Party Acc | Exact Zones Acc |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **clean** | 6 | 66.7% (4/6) | 50.0% (3/6) | 66.7% (4/6) | 33.3% (2/6) |
| **noisy** | 6 | 66.7% (4/6) | 66.7% (4/6) | 100.0% (6/6) | 33.3% (2/6) |

### Root-Cause Attribution Count

- **STT_MISSED**: 14 *(keyword or alias was not present in audio transcript)*
- **LLM_MISSED**: 1 *(keyword or alias was present in audio transcript but LLM failed to extract it)*
