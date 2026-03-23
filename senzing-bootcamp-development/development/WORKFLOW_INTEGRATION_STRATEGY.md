# Workflow Integration Strategy

## Current Situation

The comprehensive workflows for Modules 7-12 (~10,000+ lines) have been created in `docs/development/NEW_WORKFLOWS_PHASE5.md` but are not yet integrated into the main `steering/steering.md` file.

## Challenge

- **Current steering.md**: 1,945 lines
- **New workflows**: ~10,000 lines
- **Final size**: ~12,000 lines (estimated)
- **File size**: Too large for simple append operations
- **Complexity**: Multiple insertion points, not just appending

## Integration Options

### Option A: Manual Integration (RECOMMENDED) ✅

**Approach**: Manually copy workflows from NEW_WORKFLOWS_PHASE5.md into steering.md

**Steps**:
1. Open both files side-by-side in editor
2. Locate insertion points in steering.md:
   - After Module 6 workflow (line ~1023) → Insert Module 7
   - Replace old Module 7 (line ~1053) → Replace with Module 8
   - After Module 8 → Insert Module 9
   - After Module 9 → Insert Module 10
   - After Module 10 → Insert Module 11
   - Replace old Module 8 (line ~1296) → Replace with Module 12
3. Copy each workflow section
4. Verify formatting and references
5. Test that all links work

**Pros**:
- Most reliable
- Full control over formatting
- Can verify each section
- No risk of automation errors

**Cons**:
- Time-consuming (30-60 minutes)
- Manual process

**Status**: RECOMMENDED for next session

### Option B: Keep Workflows Separate (ALTERNATIVE) ✅

**Approach**: Keep workflows in NEW_WORKFLOWS_PHASE5.md and reference from steering.md

**Implementation**:
1. Add references in steering.md:
   ```markdown
   ## Module 7: Multi-Source Orchestration
   
   See detailed workflow in `docs/development/NEW_WORKFLOWS_PHASE5.md` (Module 7 section)
   
   **Quick Summary**:
   - Assess multi-source requirements
   - Define load order
   - Create orchestration script
   - [... brief overview ...]
   ```

2. Update agent-instructions.md to load NEW_WORKFLOWS_PHASE5.md when needed

**Pros**:
- No integration work needed
- Easier to maintain separate files
- Can update workflows independently
- Smaller steering.md file

**Cons**:
- Workflows not in main steering file
- Requires loading additional file
- Less discoverable

**Status**: VIABLE ALTERNATIVE

### Option C: Split into Module-Specific Files (FUTURE)

**Approach**: Create separate workflow files for each module

**Structure**:
```
steering/
├── steering.md                 # Main file with references
├── workflows/
│   ├── module-07-workflow.md
│   ├── module-08-workflow.md
│   ├── module-09-workflow.md
│   ├── module-10-workflow.md
│   ├── module-11-workflow.md
│   └── module-12-workflow.md
```

**Pros**:
- Modular and maintainable
- Easy to update individual modules
- Smaller file sizes
- Better organization

**Cons**:
- Requires restructuring
- More files to manage
- Need to update references

**Status**: FUTURE ENHANCEMENT

### Option D: Automated Integration (NOT RECOMMENDED)

**Approach**: Use strReplace operations to insert workflows

**Why Not Recommended**:
- File too large for reliable automation
- Multiple insertion points
- Risk of errors
- Difficult to verify
- Hard to recover from mistakes

**Status**: NOT RECOMMENDED

## Current Decision: Option B (Keep Separate)

For now, we're using **Option B** - keeping workflows in NEW_WORKFLOWS_PHASE5.md and referencing from steering.md.

### Implementation

1. **NEW_WORKFLOWS_PHASE5.md** contains all workflows (DONE ✅)
2. **steering.md** references the workflows (PENDING)
3. **Agent loads workflows on-demand** when user reaches those modules

### Benefits of This Approach

- ✅ Workflows are complete and ready to use
- ✅ No risk of breaking existing steering.md
- ✅ Easy to maintain and update
- ✅ Can switch to Option A later if desired
- ✅ Smaller main steering file

### How Agents Use This

When a user reaches Module 7-12:

```
User: "Let's start Module 7"

Agent:
1. Loads steering/steering.md (main workflows)
2. Loads docs/development/NEW_WORKFLOWS_PHASE5.md (detailed Module 7 workflow)
3. Follows the detailed workflow from NEW_WORKFLOWS_PHASE5.md
4. Guides user through each step
```

## Future Migration Path

If we decide to integrate later:

1. **Phase 1**: Add brief summaries to steering.md with references
2. **Phase 2**: Gradually copy workflows into steering.md
3. **Phase 3**: Deprecate NEW_WORKFLOWS_PHASE5.md
4. **Phase 4**: Archive NEW_WORKFLOWS_PHASE5.md to docs/development/archive/

## File Locations

### Current Files
- **Main workflows**: `steering/steering.md` (Modules 0-6, old 7-8)
- **New workflows**: `docs/development/NEW_WORKFLOWS_PHASE5.md` (Modules 7-12)
- **Agent instructions**: `steering/agent-instructions.md`

### After Integration (Option A)
- **All workflows**: `steering/steering.md` (Modules 0-12)
- **Archive**: `docs/development/NEW_WORKFLOWS_PHASE5.md` (archived)

### With Separate Files (Option B - Current)
- **Main workflows**: `steering/steering.md` (Modules 0-6)
- **Extended workflows**: `docs/development/NEW_WORKFLOWS_PHASE5.md` (Modules 7-12)
- **Agent instructions**: `steering/agent-instructions.md` (references both)

## Recommendations

### For Users
- No action needed - workflows are accessible through Kiro
- Agent will load appropriate workflows automatically

### For Developers
- Use Option B (current approach) for now
- Consider Option A (manual integration) in future release
- Consider Option C (split files) for v4.0.0

### For Agents
- Load steering.md for Modules 0-6
- Load NEW_WORKFLOWS_PHASE5.md for Modules 7-12
- Follow workflows step-by-step
- Reference both files as needed

## Status

- ✅ Workflows created in NEW_WORKFLOWS_PHASE5.md
- ✅ Decision made: Option B (keep separate)
- ✅ Documentation updated
- ⏳ Agent instructions updated (if needed)
- ⏳ Testing with users

## Next Steps

1. **Test with users** - Verify workflows are accessible
2. **Gather feedback** - See if separate files work well
3. **Decide on integration** - After user feedback
4. **Implement chosen option** - Based on feedback

## Version History

- **v1.0.0** (2026-03-17): Initial strategy document
- Decision: Option B (keep separate) for v3.0.0

## Related Documentation

- `docs/development/NEW_WORKFLOWS_PHASE5.md` - Complete workflows
- `docs/development/PHASE_5_COMPLETE.md` - Phase 5 completion summary
- `steering/steering.md` - Main steering file
- `steering/agent-instructions.md` - Agent behavior guide
