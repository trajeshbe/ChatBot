# Agent Artifact Detection - Final Fix

> **Date**: 2025-12-11
> **Status**: 🔧 In Progress
> **Issue**: Artifacts not being detected after agent completes task

---

## 🔍 Problem Summary

**What Works**:
- ✅ Agent completes in 3-5 iterations
- ✅ File is created successfully (3.5MB HTML file exists)
- ✅ Task marked as "completed" not "failed"

**What's Broken**:
- ❌ Artifacts array is empty in result.json
- ❌ Only shows input file `/workspace/sales2.txt` instead of output file
- ❌ No MinIO upload (because artifacts array is empty)
- ❌ No download button in UI

---

## 🕰️ Timeline

**3 hours ago (MVP .93)**: Everything working perfectly
- Artifacts detected correctly
- Files downloadable from UI
- No MinIO organizational hierarchy

**Current (MVP .94)**: Broken after adding MinIO changes
- Added MinIO upload functionality
- Added organizational path hierarchy
- **BROKE** artifact detection in the process

---

## 🔬 Root Cause

### Old Working Code (MVP .93):
```python
# Line 436: Loop starts
while self.iteration < self.max_iterations and not task_complete:
    # ... tool execution ...

    if "FINAL_ANSWER" in response:
        task_complete = True
        break

# Line 535-536: After loop ends, scan happens HERE
# Scan artifacts directory for files
artifacts_dir = self.orchestrator.artifacts_dir
if artifacts_dir.exists():
    for artifact_file in artifacts_dir.iterdir():
        # Add to session_state["artifacts"]

# Line 538: Build result with artifacts
result = {
    "artifacts": self.orchestrator.session_state["artifacts"]
}
```

### Current Broken Code (MVP .94):
```python
# Line 556: Scan INSIDE loop (after tool execution)
while self.iteration < self.max_iterations and not task_complete:
    # ... tool execution ...

    # Scan workspace for files (line 556-594)
    for scan_dir in [artifacts_dir, workspace]:
        for artifact_file in files:
            # Add to session_state["artifacts"]

    if "FINAL_ANSWER" in response:
        task_complete = True
        break  # ❌ LOOP EXITS HERE, scan already ran BEFORE file was created!

# Line 612-620: Build result
result = {
    "artifacts": self.orchestrator.session_state["artifacts"]  # Empty!
}
```

**The Issue**: When FINAL_ANSWER is called in iteration 4:
1. Tool executes → file created
2. FINAL_ANSWER detected → loop breaks immediately
3. Scan at line 556 **never runs for that iteration**
4. Result built with empty artifacts array

---

## ✅ Solution

Move the artifact scan to run **AFTER** the loop completes, just like the old code:

```python
# After loop completes
while self.iteration < self.max_iterations and not task_complete:
    # ... loop code ...

# 🆕 FINAL SCAN - After loop, before building result
# This catches files created in the final iteration
for scan_dir in [orchestrator.artifacts_dir, orchestrator.workspace]:
    if not scan_dir.exists():
        continue

    files_to_check = [f for f in scan_dir.iterdir() if f.is_file()]

    for artifact_file in files_to_check:
        artifact_path = str(artifact_file.relative_to(orchestrator.workspace))

        # Skip input files
        if artifact_file.name in ['sales2.txt', 'sales.txt', 'sales.csv']:
            continue

        # Check if already tracked
        already_tracked = any(
            a.get("path") == artifact_path
            for a in orchestrator.session_state["artifacts"]
        )

        if not already_tracked:
            logger.info(f"📎 Final scan found: {artifact_path}")
            orchestrator.session_state["artifacts"].append({
                "path": artifact_path,
                "size": artifact_file.stat().st_size,
                "created_at": datetime.utcnow().isoformat()
            })

# NOW build result with complete artifacts
result = {
    "artifacts": orchestrator.session_state["artifacts"]  # Now has files!
}
```

---

## 📝 Implementation Steps

1. **Remove** the scan from inside the loop (lines 556-594)
2. **Add** the scan AFTER the loop completes (after line 610, before line 612)
3. **Add to `session_state["artifacts"]`** not `result["artifacts"]`
4. **Rebuild** agent-runtime container
5. **Test** with new task

---

## 🎯 Expected Result

After fix:
- ✅ Agent completes in 3-5 iterations
- ✅ File created in `/workspace/artifacts/sales_report_123.html`
- ✅ **Final scan detects file and adds to `session_state["artifacts"]`**
- ✅ Result.json has correct artifacts array
- ✅ Backend extracts artifacts from result.json
- ✅ MinIO upload happens with organizational path
- ✅ Download button shows in UI

---

**Next**: Implement this fix properly
