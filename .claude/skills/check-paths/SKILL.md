---
name: check-paths
description: Verify that OneDrive paths, junction references, and config files follow the project path conventions. Catches carucci_r/RobertCarucci mismatches and stale standards_root references.
user-invocable: true
allowed-tools: Bash(git *) Read Grep Glob
---

# Check Paths -- Config and Script Path Validation

Lint all configuration files and Python scripts for path consistency violations.

## Rules to Enforce

### Rule 1: No RobertCarucci in scripts or configs
The canonical username is `carucci_r`. The junction `C:\Users\carucci_r -> C:\Users\RobertCarucci` exists, but all code must reference `carucci_r`.

**Check:**
```bash
# Search for RobertCarucci in all Python and YAML files
grep -rn "RobertCarucci" --include="*.py" --include="*.yaml" --include="*.yml" --include="*.ps1" --include="*.json" .
```
Any match is a **violation**.

### Rule 2: PowerBI_Data is the canonical folder name
The old misspelled folder name must not appear.

**Check:**
```bash
# Search for old misspelled folder names
grep -rn "PowerBi_Data\|PowerBI_data\|Powerbi_Data\|powerbi_data" --include="*.py" --include="*.yaml" --include="*.yml" --include="*.ps1" . | grep -v "PowerBI_Data"
```

### Rule 3: OneDrive paths use the full suffix
All OneDrive paths must use `OneDrive - City of Hackensack`, not bare `OneDrive`.

**Check:**
```bash
# Find OneDrive refs that are NOT the full "OneDrive - City of Hackensack"
grep -rn "OneDrive" --include="*.py" --include="*.yaml" --include="*.yml" --include="*.ps1" . | grep -v "OneDrive - City of Hackensack" | grep -v ".git/" | grep -v "CLAUDE.md" | grep -v "SKILL.md"
```

### Rule 4: ${standards_root} variable used in schemas.yaml
The `config/schemas.yaml` file should use `${standards_root}` for all Standards paths, not hardcoded absolute paths.

**Check:**
```bash
# Look for hardcoded Standards paths that should use the variable
grep -n "09_Reference/Standards" config/schemas.yaml | grep -v "standards_root"
```

### Rule 5: Config paths are internally consistent
All paths in `config/consolidation_sources.yaml` should reference `carucci_r` and use consistent base directories.

**Check:**
```bash
# Extract all paths from YAML configs and check consistency
grep -n "path:" config/consolidation_sources.yaml config/rms_sources.yaml | head -30
```

### Rule 6: No hardcoded normalization dicts in scripts
Since v1.7.0, normalization mappings load from `Standards/CAD_RMS/mappings/*.json`. No Python file should contain hardcoded normalization dictionaries.

**Check:**
```bash
# Look for hardcoded mapping dicts (common pattern: large dict literals with normalization targets)
grep -rn "how_reported_map\|disposition_map\|normalization_map" --include="*.py" . | grep -v "load\|import\|json\|\.json\|SKILL.md"
```

## Execution

Run ALL checks above using Grep and report results in this format:

```
## Path Check Results

| Rule | Status | Details |
|------|--------|---------|
| No RobertCarucci | PASS/FAIL | X violations found |
| PowerBI_Data canonical | PASS/FAIL | X violations found |
| OneDrive full suffix | PASS/FAIL | X violations found |
| ${standards_root} usage | PASS/FAIL | X hardcoded paths |
| Config path consistency | PASS/FAIL | X inconsistencies |
| No hardcoded mappings | PASS/FAIL | X violations found |

### Violations (if any)
- file:line -- description
```

If any violations are found, offer to fix them automatically. For Rule 1 violations, **do NOT auto-fix** -- ask the user to verify junction status first (per CLAUDE.md instructions).
