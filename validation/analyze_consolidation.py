import json

# Load validation data
with open('validation/reports/validation_summary_20260204_003131.json', 'r') as f:
    data = json.load(f)

ct = next(d for d in data['drift_results'] if d['detector']=='CallTypeDriftDetector')
types = [item['value'] for item in ct['new_call_types']]

print('=== CONSOLIDATION CANDIDATES ===\n')

# Spacing/punctuation variants
print('Spacing/Punctuation Variants:')
print('  - "Discovery-Motor Vehicle" vs "Discovery-MotorVehicle"')
print('  - "Relief/Personal" (spacing variant)')
print('  - "Fight -Unarmed" vs "Fight -Armed" (spacing)')
print()

# Statute code variants
statute_types = [t for t in types if ' - 2C:' in t or ' 2C:' in t or '- 2C:' in t]
print(f'Statute Code Variants: {len(statute_types)} types')
for t in statute_types:
    print(f'  {t}')
print()

# Duplicate detection (similar base names)
print('Potential Duplicates (similar names):')
burglary = [t for t in types if 'Burglary' in t]
print(f'  Burglary variants: {len(burglary)}')
for t in burglary:
    print(f'    {t}')
print()

criminal_mischief = [t for t in types if 'Criminal Mischief' in t]
print(f'  Criminal Mischief variants: {len(criminal_mischief)}')
for t in criminal_mischief:
    print(f'    {t}')
