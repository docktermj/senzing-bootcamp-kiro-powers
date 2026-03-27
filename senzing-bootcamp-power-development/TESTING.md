# Testing Guide for Senzing Boot Camp Power

This guide documents how to test the Senzing Boot Camp power locally before distribution.

## Overview

Testing the power involves:

1. Local installation and activation
2. Steering file validation
3. MCP server connectivity testing
4. Hook functionality verification
5. Documentation completeness check

## Prerequisites

- Kiro IDE installed
- Access to test workspace
- Internet connection (for MCP server testing)

## Local Testing Workflow

### 1. Install Power Locally

#### Option A: Install from local directory

```bash
# From Kiro, use the configure action to open powers panel
# Then add local power path: /path/to/senzing-kiro-power/senzing-bootcamp
```

#### Option B: Test without installation

```bash
# Copy power files to test workspace
cp -r senzing-bootcamp /path/to/test-workspace/.kiro/powers/senzing-bootcamp
```

### 2. Activate Power

In Kiro, test power activation:

```text
kiroPowers action="activate" powerName="senzing-bootcamp"
```

**Verify**:

- ✅ POWER.md loads successfully
- ✅ Frontmatter is parsed correctly
- ✅ Steering files list is returned
- ✅ MCP server configuration is recognized

### 3. Test Steering Files

Load each steering file to verify syntax and content:

```text
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="steering.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="agent-instructions.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="quick-reference.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="project-structure.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="design-patterns.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="module-prerequisites.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="environment-setup.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="security-privacy.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="cost-estimation.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="lessons-learned.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="common-pitfalls.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="troubleshooting-decision-tree.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="complexity-estimator.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="modules-7-12-workflows.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="data-lineage.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="incremental-loading.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="uat-framework.md"
kiroPowers action="readSteering" powerName="senzing-bootcamp" steeringFile="docker-deployment.md"
```

**Verify**:

- ✅ All steering files load without errors
- ✅ Markdown formatting is correct
- ✅ No broken internal links
- ✅ Content is complete and coherent

### 4. Test MCP Server Connectivity

Test connection to Senzing MCP server:

```text
kiroPowers action="use" powerName="senzing-bootcamp" serverName="senzing" toolName="get_capabilities" arguments={}
```

**Verify**:

- ✅ Server responds successfully
- ✅ Capabilities list is returned
- ✅ No authentication errors
- ✅ Response time is reasonable (< 5 seconds)

### 5. Test MCP Tools

Test key MCP tools used in the boot camp:

**Test get_sample_data:**

```text
kiroPowers action="use" powerName="senzing-bootcamp" serverName="senzing" toolName="get_sample_data" arguments={"dataset": "las_vegas", "format": "json"}
```

**Test search_docs:**

```text
kiroPowers action="use" powerName="senzing-bootcamp" serverName="senzing" toolName="search_docs" arguments={"query": "entity resolution", "limit": 5}
```

**Test explain_error_code:**

```text
kiroPowers action="use" powerName="senzing-bootcamp" serverName="senzing" toolName="explain_error_code" arguments={"error_code": "SENZ0005"}
```

**Verify**:

- ✅ All tools respond successfully
- ✅ Responses are well-formatted
- ✅ No server errors
- ✅ Response content is relevant

### 6. Verify Hook Files

Check hook file syntax:

```bash
# Validate JSON syntax
for hook in senzing-bootcamp/hooks/*.hook; do
    echo "Validating $hook"
    jq empty "$hook" && echo "✅ Valid" || echo "❌ Invalid"
done
```

**Verify**:

- ✅ All hook files have valid JSON syntax
- ✅ Required fields are present (name, version, when, then)
- ✅ Event types are valid
- ✅ File patterns are correct

### 7. Test Hook Installation

Test hook installation process:

```bash
# Create test workspace
mkdir -p /tmp/test-bootcamp-workspace
cd /tmp/test-bootcamp-workspace

# Copy hooks
mkdir -p .kiro/hooks
cp /path/to/senzing-bootcamp/hooks/*.hook .kiro/hooks/

# Verify hooks are installed
ls -la .kiro/hooks/
```

**Verify**:

- ✅ Hooks copy successfully
- ✅ File permissions are correct
- ✅ Hooks appear in Kiro hooks panel

### 8. Documentation Completeness Check

Verify all referenced files exist:

**User-facing documentation:**

```bash
# Check guides
ls senzing-bootcamp/docs/guides/QUICK_START.md
ls senzing-bootcamp/docs/guides/FAQ.md
ls senzing-bootcamp/docs/guides/GLOSSARY.md
ls senzing-bootcamp/docs/guides/ONBOARDING_CHECKLIST.md
ls senzing-bootcamp/docs/guides/PROGRESS_TRACKER.md
ls senzing-bootcamp/docs/guides/TROUBLESHOOTING_INDEX.md
ls senzing-bootcamp/docs/guides/COLLABORATION_GUIDE.md
ls senzing-bootcamp/docs/guides/HOOKS_INSTALLATION_GUIDE.md

# Check policies
ls senzing-bootcamp/docs/policies/PEP8_COMPLIANCE.md
ls senzing-bootcamp/docs/policies/SQLITE_DATABASE_LOCATION.md

# Check feedback template
ls senzing-bootcamp/docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md

# Check diagrams
ls senzing-bootcamp/docs/diagrams/module-flow.md
ls senzing-bootcamp/docs/diagrams/data-flow.md
```

**Verify**:

- ✅ All referenced files exist
- ✅ No broken links in documentation
- ✅ File paths are correct

### 9. Test Example Projects

Verify example projects are complete:

```bash
# Check example directories
ls -la senzing-bootcamp/examples/simple-single-source/
ls -la senzing-bootcamp/examples/multi-source-project/
ls -la senzing-bootcamp/examples/production-deployment/

# Verify README files
ls senzing-bootcamp/examples/simple-single-source/README.md
ls senzing-bootcamp/examples/multi-source-project/README.md
ls senzing-bootcamp/examples/production-deployment/README.md
```

**Verify**:

- ✅ All example directories exist
- ✅ README files are present
- ✅ Example code is complete

### 10. Test Templates

Verify templates are accessible:

```bash
# Check templates directory
ls -la senzing-bootcamp/templates/

# Verify key templates
ls senzing-bootcamp/templates/demo_quick_start.py
ls senzing-bootcamp/templates/README.md
```

**Verify**:

- ✅ Templates directory exists
- ✅ Key templates are present
- ✅ Template README is complete

## Testing Checklist

Use this checklist for comprehensive testing:

### Power Installation

- [ ] Power installs from local directory
- [ ] Power appears in powers list
- [ ] Power can be activated
- [ ] Frontmatter is parsed correctly

### POWER.md

- [ ] Loads successfully
- [ ] Frontmatter is valid
- [ ] All sections are present
- [ ] No broken internal links
- [ ] Markdown formatting is correct

### Steering Files

- [ ] All steering files load successfully
- [ ] No syntax errors
- [ ] Content is complete
- [ ] No broken links

### MCP Server

- [ ] Server is accessible
- [ ] get_capabilities works
- [ ] Key tools respond correctly
- [ ] No authentication errors

### Hooks

- [ ] All hook files have valid JSON
- [ ] Hooks install correctly
- [ ] Hooks appear in Kiro panel

### Documentation

- [ ] All referenced files exist
- [ ] No broken links
- [ ] File paths are correct
- [ ] Content is complete

### Examples

- [ ] All example directories exist
- [ ] README files are present
- [ ] Example code is complete

### Templates

- [ ] Templates directory exists
- [ ] Key templates are present
- [ ] Template README is complete

## Common Issues and Solutions

### Issue: Power doesn't appear after installation

**Cause**: Power path is incorrect or power files are missing

**Solution**:

1. Verify power directory structure
2. Check that POWER.md exists in root of power directory
3. Verify frontmatter is valid YAML
4. Restart Kiro if necessary

### Issue: Steering file fails to load

**Cause**: File doesn't exist or has syntax errors

**Solution**:

1. Verify file exists in steering/ directory
2. Check markdown syntax
3. Verify file name matches exactly (case-sensitive)

### Issue: MCP server connection fails

**Cause**: Network issues or server unavailable

**Solution**:

1. Check internet connection
2. Verify firewall allows HTTPS to mcp.senzing.com
3. Test server URL in browser: <https://mcp.senzing.com/mcp>
4. Check Kiro MCP configuration

### Issue: Hook installation fails

**Cause**: Invalid JSON or missing fields

**Solution**:

1. Validate JSON syntax with `jq`
2. Verify all required fields are present
3. Check event types are valid
4. Verify file patterns are correct

## Updating the Power

When making changes to the power:

1. **Update version in CHANGELOG.md**
   - Follow semantic versioning
   - Document all changes

2. **Update POWER.md if needed**
   - Update "Last Updated" date
   - Update version number if major changes

3. **Test all changes**
   - Run through testing checklist
   - Verify no regressions

4. **Update development documentation**
   - Document changes in this file
   - Update README.md if structure changes

## Continuous Testing

For ongoing development:

1. **Test after each change**
   - Don't accumulate untested changes
   - Verify change doesn't break existing functionality

2. **Test in clean environment**
   - Use fresh workspace
   - Don't rely on cached state

3. **Test with real users**
   - Get feedback from actual boot camp users
   - Document issues in feedback files

4. **Monitor MCP server**
   - Check server availability regularly
   - Test new MCP tools as they're added

## Version History

- **2026-03-27**: Created testing guide with comprehensive checklist
- **Future**: Add automated testing scripts

## Related Documentation

- `README.md` - Development repository overview
- `CHANGELOG.md` - Version history
- `senzing-bootcamp/POWER.md` - Main power documentation
