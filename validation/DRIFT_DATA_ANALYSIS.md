# Drift Detection Data Analysis - Decision Support

## Overview
**Dataset:** 754,409 CAD records (2019-2026)  
**Drift Detected:**
- **184 new call types** (shown: top 50)
- **219 new personnel** (shown: top 30)
- **262 unused call types** (90+ days without appearance)

---

## Call Types - Frequency Analysis

### Distribution Breakdown
| Frequency Range | Count | % of New Types | Risk Level |
|----------------|-------|----------------|------------|
| **>1000 calls** | 6 | 12% | ✅ Very Low - Clearly legitimate |
| **500-999** | 2 | 4% | ✅ Low - Likely legitimate |
| **100-499** | 18 | 36% | ⚠️ Medium - Review needed |
| **50-99** | 10 | 20% | ⚠️ High - Could be errors |
| **<50** | 14 | 28% | 🔴 Very High - Likely errors/variants |

### High-Confidence Items (>1000 calls)
These appear frequently enough to be clearly legitimate:
1. Motor Vehicle Violation – Private Property (4,447)
2. Medical Call –Oxygen (4,434)
3. Applicant Firearm (2,341)
4. Motor Vehicle Crash – Hit and Run (2,177)
5. Property – Lost (1,294)
6. Relief/Personal (1,147)

**Recommendation:** These 6 could be auto-approved with minimal risk.

---

## Personnel - Frequency Analysis

### Distribution Breakdown
| Call Count Range | Count | % of New Personnel | Risk Level |
|-----------------|-------|-------------------|------------|
| **>5000 calls** | 23 | 77% | ✅ Very Low - Active officers |
| **1000-4999** | 7 | 23% | ✅ Low - Active officers |
| **<1000** | 0 | 0% | N/A |

### Key Observation
**ALL 30 new personnel have 3,788+ calls** (minimum)

**Implication:** These are clearly active, legitimate officers. The high activity across all new personnel suggests your reference file is significantly out of date (new hires not added promptly).

**Recommendation:** Personnel could be auto-approved with very high confidence.

---

## Data Quality Issues Found

### 1. Spacing/Punctuation Variants
**Examples:**
- "Discovery-Motor Vehicle" vs "Discovery-MotorVehicle" (spacing in hyphen)
- "Relief/Personal" (likely variant of existing "Relief / Personal" with different spacing)
- "Fight -Unarmed" vs "Fight -Armed" (inconsistent spacing)

**Count:** 3+ obvious variants detected  
**Impact:** These should be **consolidated**, not added as new types

### 2. Statute Code Inconsistencies
**Found:** 19 types with statute codes (e.g., "- 2C:18-2")

**Issues:**
- "Burglary - Auto - 2C:18-2" vs "Burglary - Auto - 2C: 18-2" (extra space before "18")
- Some have statute codes, likely duplicating types without them
- Example: "Shoplifting - 2C:20-11" (new) probably exists as just "Shoplifting" in reference

**Impact:** Need consolidation logic to map statute variants to base types

### 3. Legitimate Duplicates with Subtypes
**Burglary variants (4 types):**
- Burglary - Auto (with/without statute)
- Burglary - Residence
- Burglary - Commercial

**Criminal Mischief variants (2 types):**
- Criminal Mischief (general)
- Criminal Mischief - Vehicle

**These are legitimate subtypes** - should be added as distinct entries.

---

## Risk Assessment by Automation Level

### Option A: Manual Review All (Current)
**Pros:**
- Zero risk of incorrect additions
- Full human oversight
- Catch all variants/errors

**Cons:**
- Time intensive (2-3 hours per sync)
- Human error in manual CSV editing
- Delayed reference data updates

**Best for:** First sync, when establishing confidence in the system

---

### Option B: Auto-Approve High-Confidence, Flag Low-Confidence
**Auto-approve criteria:**
- Call types: >1000 frequency (6 items = 12% of work saved)
- Personnel: >3000 calls (ALL 30 items = 100% of personnel work saved)

**Flag for review:**
- Call types: <1000 frequency (44 items need review)
- Items with statute codes (19 items = potential consolidation)
- Items with spacing/punctuation irregularities

**Pros:**
- Saves time on obvious items (personnel entirely automated)
- Human review focuses on risky items
- Balance of speed and safety

**Cons:**
- Could auto-approve a variant (low risk with 1000+ threshold)
- Still requires manual review of 44 call types

**Best for:** Ongoing maintenance after initial cleanup

---

### Option C: Full Automation with Post-Sync Review Report
**Auto-approve everything**, then generate report of what was added

**Pros:**
- Fastest (no manual review time)
- Reference data always current
- Review can happen asynchronously

**Cons:**
- Will add variants/errors automatically
- Creates cleanup work later
- Could pollute reference data

**Best for:** Organizations with high trust in data entry, low variant issues

---

### Option D: Tiered Approach (Different Rules by Field Type)

**Call Types:**
- Auto-approve: >1000 frequency
- Flag for review: 100-999 frequency
- Auto-reject: <100 frequency + flag for investigation

**Personnel:**
- Auto-approve: >1000 calls (clearly active officers)
- Add immediately with "Needs Verification" status

**Pros:**
- Field-appropriate rules
- Personnel is low-risk, call types need more care
- Balances speed vs accuracy by data type

**Cons:**
- More complex logic
- Different workflows for different fields

**Best for:** Your situation - personnel drift is clear, call type drift has quality issues

---

## Recommendations Based on YOUR Data

### For Call Types: **Option B (Semi-Automated)**
**Reasoning:**
- 6 items (12%) are clearly safe to auto-approve (>1000 calls)
- 28% of items are <50 frequency (very suspicious)
- 19 items have statute code issues needing human review
- Consolidation opportunities exist (variants need mapping)

**Suggested Rules:**
- **Auto-approve:** Frequency >1000 AND no statute code
- **Flag for review:** Everything else
- **Flag specially:** Items with spacing/punct irregularities, statute codes

### For Personnel: **Option B trending to C (High Automation)**
**Reasoning:**
- ALL 30 personnel have 3,788+ calls (clearly legitimate)
- No low-frequency suspicious entries
- Names are standardized (P.O., SPO., Det., etc.)
- Risk of bad auto-approval is extremely low

**Suggested Rules:**
- **Auto-approve:** Any personnel with >1000 calls
- **Add verification task:** HR verification list generated monthly

---

## Answer to Question 1

**Recommended Choice: Option D (Tiered Approach)**

**Why:**
- **Personnel can be highly automated** (all entries are legitimate officers)
- **Call types need more scrutiny** (variants, statute codes, low-frequency items)
- Your data shows different risk profiles for different fields
- Saves maximum time while maintaining quality

**Specific Implementation:**
- Personnel: Auto-approve >1000 calls (saves 100% of personnel review time)
- Call types: Auto-approve >1000 frequency without statute codes (saves 12% of call type review time)
- Call types: Flag all items with statute codes, spacing issues, or <100 frequency for review

**Expected Time Savings:**
- Personnel: ~1 hour (100% automated)
- Call types: ~15 minutes (12% automated, 88% still reviewed)
- **Total: 1.25 hours saved per sync**

---

## Follow-Up Questions for Plan Mode

1. **Consolidation Logic:** How should we detect and flag variants automatically?
2. **Thresholds:** Are 1000 calls (call types) and 1000 calls (personnel) the right thresholds?
3. **Statute Code Handling:** Should types with statute codes always be flagged for consolidation review?
4. **Unused Types:** How should we handle the 262 types not seen in 90+ days?
5. **Drift Alerts:** Should we alert when drift exceeds certain thresholds (e.g., >50 new types)?
