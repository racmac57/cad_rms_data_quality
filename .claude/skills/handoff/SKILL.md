---
name: handoff
description: Generate a structured AI handoff document for the next session. Use when wrapping up a work session, handing off to Cursor or another Claude Code instance, or documenting next steps for server work.
disable-model-invocation: true
argument-hint: [short-title]
allowed-tools: Bash(git log *) Read Grep Glob
---

# Generate AI Handoff Document

Create a handoff document at `docs/ai_handoff/HANDOFF_YYYYMMDD_$ARGUMENTS.md` using today's date.

## Template Structure

Follow this exact structure, which matches the established pattern in this repo:

```markdown
# Handoff: <Title>

**Date:** YYYY-MM-DD
**Status:** <Ready to implement | In progress | Blocked on X>
**Prerequisite:** <link to prior handoff if any, or "None">
**Server:** HPD2022LAWSOFT (10.0.0.157) -- RDP as `HPD\administrator`

---

## Opening Prompt -- Cursor

Paste this as your first message in a new Cursor chat:

\```
Read C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality\docs\ai_handoff\<this_file>.md before responding.

Context: <1-2 sentence summary of what needs to happen and current state>
\```

## Opening Prompt -- Claude Code

Run `claude` from the repo root, then paste:

\```
<Similar prompt but referencing relative path docs/ai_handoff/<this_file>.md>
\```

---

## Background

<What was done, what led to this point, key decisions made>

## Implementation Plan

### Step 1 -- <title>
<Commands and instructions>

### Step 2 -- <title>
<Commands and instructions>

...

---

## Architecture Reference

<Tables, paths, service URLs relevant to this task>

---

## If It Fails

<Diagnosis tree: common failure modes and how to check/fix each>

---

## Next Steps After Completion

1. <verification>
2. <next handoff or task>
```

## Instructions

1. **Read recent git history** to understand what was done this session:
   ```
   git log --oneline -20
   ```

2. **Read any existing handoffs** in `docs/ai_handoff/` for format reference.

3. **Ask the user** what the handoff is about if `$ARGUMENTS` is empty or unclear. Gather:
   - What was accomplished this session
   - What remains to be done
   - Which server/environment the next session targets
   - Any blockers or prerequisites

4. **Write the handoff** following the template above. Key rules:
   - Opening prompts must be self-contained -- the next AI has zero context
   - Include exact PowerShell/Python commands, not vague instructions
   - Server paths use Windows backslashes
   - Reference specific files by full path on the server
   - Include expected output for verification commands
   - The "If It Fails" section is mandatory -- list 2-3 likely failure modes

5. **Show the user** the generated document for review before finalizing.

## Path References

- Repo on server: `C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\cad_rms_data_quality`
- Scripts on server: `C:\HPD ESRI\04_Scripts\`
- ArcGIS Pro Python: `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`
- ArcGIS toolbox: `C:\ESRIExport\LawEnforcementDataManagement_New\LawEnforcementDataManagement.atbx`
- AGOL org: `https://hpd0223.maps.arcgis.com`
