# Module 0: Quick Demo (Optional)

## Overview

Module 0 provides a demonstration of Senzing entity resolution using sample data. This optional module is perfect for first-time users who want to see entity resolution in action before working with their own data.

This module offers multiple demo options to ensure everyone can see entity resolution working, regardless of their environment.

**Time**:

- First time (Docker): 15-20 minutes (includes 2-5 min Docker image download)
- Subsequent runs (Docker): 10-15 minutes
- Simulation Demo: 5-10 minutes (no setup required)

**Output**: Working demo showing entity resolution results

## Prerequisites

### For Docker Demo (Recommended - Real SDK)

- ✅ Docker installed and running (version 20.0+)
- ✅ 2GB free disk space for Senzing SDK image
- ✅ Network access to pull Docker images
- ✅ Proper Docker permissions (ability to run containers)

**First-time setup**: 2-5 minutes to download 1.6GB Docker image

### For Simulation Demo (No Installation - Shows Concepts)

- ✅ Python 3.8+ installed
- ✅ No other requirements!

**Setup time**: Instant (no downloads)

**Note**: Simulation demo shows what Senzing would do using pre-computed results. It's perfect for quick preview or when Docker isn't available.

### For Native SDK Demo (Advanced - Real SDK)

- ✅ Senzing SDK installed locally
- ✅ Python 3.8+ with senzing package
- ✅ SQLite or PostgreSQL

**Setup time**: 15-30 minutes (SDK installation)

## Choosing Your Demo Path

**Recommended for most users**: Docker Demo

- ✓ Real Senzing SDK
- ✓ No permanent installation
- ✓ Clean and isolated
- ⏱ 15-20 minutes first time

**Best for quick preview**: Simulation Demo

- ✓ No Docker needed
- ✓ Instant results
- ✓ Shows concepts clearly
- ⚠ Simulation, not real SDK
- ⏱ 5-10 minutes

**Best for developers**: Native SDK Demo

- ✓ Full SDK capabilities
- ✓ Better performance
- ✓ Reusable for later modules
- ⏱ 10-15 minutes (if SDK already installed)

## Learning Objectives

By the end of this module, you will:

- See Senzing entity resolution working in real-time
- Watch duplicate records automatically match and merge
- Understand WHY records matched (match explanations)
- Observe the before/after transformation (5 records → X entities)
- Connect the demo to your own use case

## What You'll Do

1. Choose a sample dataset (Las Vegas, London, or Moscow)
2. Review sample records showing duplicates
3. Set up Senzing SDK (automatic - uses Docker or local installation)
4. Initialize an in-memory SQLite database
5. Load sample records into Senzing
6. Query the resolved entities
7. See match explanations showing WHY records matched
8. Compare before/after (5 records → X entities)

## Sample Datasets

### Las Vegas Dataset

- **Type:** Customer records
- **Records**: ~1,000
- **Use case**: Retail/hospitality customer deduplication
- **Duplicates**: Same customers with variations in names, addresses, phones

### London Dataset

- **Type:** Person records
- **Records**: ~1,000
- **Use case**: Identity management
- **Duplicates**: Same people with name variations and different contact info

### Moscow Dataset

- **Type:** Organization records
- **Records**: ~1,000
- **Use case**: B2B vendor/supplier matching
- **Duplicates**: Same companies with different names and addresses

## Demo Script Structure

The generated demo script will:

1. **Check for Senzing SDK** - Detects if SDK is installed, offers Docker alternative
2. **Initialize Senzing** with in-memory SQLite database
3. **Load sample records** from the chosen dataset (with progress bar)
4. **Query resolved entities** to show which records matched
5. **Display match explanations** showing WHY records matched (name similarity, address match, etc.)
6. **Show statistics** (records loaded, entities created, match rate)
7. **Display example entities** with all matching records side-by-side
8. **Provide before/after comparison** (e.g., "5 records → 3 entities")

This is a real, working demonstration - not a simulation!

## Example Output

```text
Checking Senzing SDK installation...
✓ Senzing SDK found (version 3.8.0)

Initializing Senzing engine with in-memory database...
✓ Engine initialized

Loading sample records...
[====================] 100% (5/5 records loaded)

Resolving entities...
✓ Entity resolution complete

Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Records loaded:              5
Entities created:            3
Duplicates found:            2 (40% match rate)
Average records per entity:  1.67
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example Resolved Entity:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Entity ID: 1
Records matched: 3

Record 1 (CRM_SYSTEM):
  Name:    John Smith
  Address: 123 Main St, Las Vegas, NV 89101
  Phone:   (555) 123-4567
  Email:   john.smith@email.com

Record 2 (SUPPORT_SYSTEM):
  Name:    J. Smith
  Address: 123 Main Street, Las Vegas, NV 89101
  Phone:   555-123-4567
  Email:   jsmith@email.com

Record 3 (SALES_SYSTEM):
  Name:    John R Smith
  Address: 123 Main St Apt 1, Las Vegas, NV 89101
  Phone:   (555) 123-4567
  Email:   john.smith@email.com

Match Explanation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Why these records matched:

Record 1 ↔ Record 2:
  ✓ Name similarity:    92% (John Smith ≈ J. Smith)
  ✓ Address match:      100% (same address, different format)
  ✓ Phone match:        100% (same number, different format)
  ✓ Overall confidence: 98% - STRONG MATCH

Record 1 ↔ Record 3:
  ✓ Name similarity:    95% (John Smith ≈ John R Smith)
  ✓ Address match:      95% (123 Main St ≈ 123 Main St Apt 1)
  ✓ Phone match:        100%
  ✓ Email match:        100%
  ✓ Overall confidence: 99% - STRONG MATCH

Record 2 ↔ Record 3:
  ✓ Name similarity:    90% (J. Smith ≈ John R Smith)
  ✓ Address match:      95%
  ✓ Phone match:        100%
  ✓ Overall confidence: 96% - STRONG MATCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key Insights:
• Senzing automatically recognized these as the same person
• No manual rules were required
• Different data formats were handled automatically
• Confidence scores show match strength
```

## Key Concepts Demonstrated

### Entity Resolution

- Multiple records about the same real-world entity are identified and linked
- No manual rules required - Senzing learns from the data
- Confidence scores show match strength

### Feature Extraction

- Names, addresses, phones are parsed into features
- Features are standardized (e.g., "St" → "Street")
- Features are scored and compared

### Entity-Centric Learning

- As more records are added, resolution improves
- The engine learns patterns from your data
- No training data required

### Understanding `get_stats()` vs. Record Counts

A common pitfall: `sz_engine.get_stats()` tracks per-process workload statistics for the current engine session, not the total records in the repository. It resets after each call and may return `-1` for fields like `loadedRecords` if stats haven't accumulated. To get accurate record counts, track them during loading (e.g., increment a counter per successful `add_record` call) rather than relying on `get_stats()`. The correct use of `get_stats()` is for monitoring ongoing operations, covered in Module 9 (Performance Testing).

## File Locations

All Module 0 demo code is saved in `src/quickstart_demo/`:

```text
src/quickstart_demo/
├── demo_las_vegas.py          # Demo script for Las Vegas dataset
├── demo_london.py              # Demo script for London dataset
├── demo_moscow.py              # Demo script for Moscow dataset
├── sample_data_las_vegas.jsonl # Sample data
├── sample_data_london.jsonl    # Sample data
└── sample_data_moscow.jsonl    # Sample data
```

## Running the Demo

The demo runs automatically when you start Module 0. The agent will:

1. Check if Senzing SDK is installed
2. If not installed, offer to:
   - Use Docker (recommended for quick demo)
   - Guide you through SDK installation
3. Generate and run the demo script
4. Display results in real-time

### Manual Execution

If you want to run the demo again later:

```bash
# Navigate to demo directory
cd src/quickstart_demo

# Run the demo
python demo_las_vegas.py
```

### Using Docker (No Installation Required)

```bash
# Run demo in Docker container
docker run -v $(pwd)/src/quickstart_demo:/data \
  senzing/senzing-tools \
  python /data/demo_las_vegas.py
```

## What to Look For

### Good Matches

- Same person/organization with minor variations
- Different data quality levels matched correctly
- Nicknames and abbreviations handled properly

### Interesting Cases

- Records that almost match but don't (different people with similar names)
- Records that match despite significant differences (poor data quality)
- Multiple records from same source matched together

### Statistics

- Match rate: What percentage of records are duplicates?
- Entity distribution: How many records per entity on average?
- Data quality: How consistent is the data?

## Connecting to Your Use Case

After the demo, consider:

- How does this compare to your data?
- What matching criteria matter most for you?
- What data quality issues might you have?
- How many duplicates do you expect?

## Next Steps

After completing the demo:

- **Ready to start?** → Proceed to Module 1 (Business Problem)
- **Want to try another dataset?** → Run another demo
- **Have questions?** → Ask about specific entity resolution concepts

## Common Questions

**Q: Do I need to install Senzing to run the demo?**
A: No! The demo can run in Docker with no installation. If you want to install the SDK, the agent will guide you through it.

**Q: Does this actually run Senzing, or is it a simulation?**
A: This runs the real Senzing SDK! You'll see actual entity resolution happening, not a simulation or mock-up.

**Q: Can I use my own data for the demo?**
A: The demo uses sample data to ensure a quick, successful experience. You'll work with your data starting in Module 2.

**Q: How accurate is entity resolution?**
A: Accuracy depends on data quality. Typical match rates: 90-99% precision, 85-95% recall. The demo shows real match confidence scores.

**Q: Can I skip this module?**
A: Yes, it's optional. Skip to Module 1 if you're ready to start with your data. But we recommend the demo - it only takes 10 minutes and shows the value immediately.

## Troubleshooting Module 0

### Issue: Docker Database Initialization Failed

**Symptoms**:

- Error: "unable to open database file"
- Error: "SQLITE3: ERROR (14) cannot open file"
- Error: "SzDatabaseError - SENZ1001"
- Database creation fails in Docker container

**Causes**:

- Docker volume mount permission issues
- SELinux/AppArmor restrictions
- Insufficient permissions in container
- File system incompatibility

**Solutions** (try in order):

1. **Use Simulation Demo instead** (Recommended - Instant Solution)

   ```text
   Ask agent: "Use simulation demo instead"
   ```

   - ✓ No Docker required
   - ✓ Shows same concepts
   - ✓ Instant results
   - ✓ Always works
   - ⚠ Simulation, not real SDK

2. **Use in-memory database** (Docker - Automatic)
   - Agent will automatically try this
   - No file system permissions needed
   - Database stored in RAM only
   - Works around permission issues

3. **Check Docker permissions** (Linux)

   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER

   # Log out and back in, then verify
   docker ps
   ```

4. **Disable SELinux temporarily** (Linux only - if applicable)

   ```bash
   # Check if SELinux is the issue
   getenforce

   # If "Enforcing", temporarily disable
   sudo setenforce 0

   # Run demo, then re-enable
   sudo setenforce 1
   ```

5. **Try different Docker volume mount** (Advanced)
   - Agent will try /tmp, /var/tmp, /app
   - If all fail, use Simulation Demo

**Recommended**: Use Simulation Demo - it's faster and always works!

---

### Issue: Docker Not Installed or Not Running

**Symptoms**:

- "docker: command not found"
- "Cannot connect to the Docker daemon"
- "Docker is not running"

**Solutions**:

1. **Use Simulation Demo** (Recommended)
   - No Docker required
   - Shows same concepts
   - Instant results

2. **Install Docker**
   - **macOS**: [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - **Linux**: `sudo apt install docker.io` (Ubuntu/Debian)
   - **Windows**: [Docker Desktop](https://www.docker.com/products/docker-desktop)

3. **Start Docker** (if installed but not running)

   ```bash
   # macOS/Windows: Start Docker Desktop application

   # Linux:
   sudo systemctl start docker
   ```

4. **Skip to Module 1**
   - Come back to Module 0 later
   - Install SDK in Module 5
   - See real SDK in Module 6

---

### Issue: Docker Image Download is Slow or Stuck

**Symptoms**:

- Download taking >5 minutes
- Progress appears stuck
- "Pulling from..." message for long time

**Causes**:

- Slow network connection
- Large image size (1.6GB)
- Network congestion

**Solutions**:

1. **Be patient** - 1.6GB image takes time
   - Expected: 2-5 minutes on good connection
   - May take 10-15 minutes on slow connection

2. **Check network speed**

   ```bash
   # Test connection
   ping docker.io
   ```

3. **Use Simulation Demo** (Instant alternative)
   - No download required
   - Shows same concepts
   - Continue learning immediately

4. **Try again later**
   - Network may be congested
   - Try during off-peak hours

---

### Issue: Demo Runs But No Matches Found

**This shouldn't happen** with sample data - the records are designed to match.

**If it does happen**:

1. **Check sample data loaded correctly**
   - Verify 5 records were loaded
   - Check for error messages during loading

2. **Verify Senzing engine initialized**
   - Look for "Engine initialized" message
   - Check for initialization errors

3. **Contact support** - This indicates a bug
   - Share error messages with agent
   - Provide full output log
   - This is unexpected behavior

---

### Issue: Want to See Real SDK, Not Simulation

**If simulation demo was used but you want to see real SDK**:

**Options**:

1. **Install Docker** and retry Docker demo
   - Follow Docker installation instructions above
   - Return to Module 0 after installation

2. **Install Senzing SDK** locally (Module 5)
   - Complete Module 5 (SDK Setup)
   - Return to Module 0 with installed SDK
   - Run native SDK demo

3. **Continue to Module 6**
   - You'll see real SDK in action
   - Module 6 loads actual data
   - More comprehensive than Module 0 demo

4. **Accept simulation for now**
   - Concepts are the same
   - Real SDK comes later
   - Focus on learning entity resolution

---

### Issue: Python Not Installed (For Simulation Demo)

**Symptoms**:

- "python: command not found"
- "python3: command not found"

**Solutions**:

1. **Install Python 3.8+**
   - **macOS**: `brew install python3` or download from [python.org](https://www.python.org)
   - **Linux**: `sudo apt install python3` (Ubuntu/Debian)
   - **Windows**: Download from [python.org](https://www.python.org)

2. **Verify installation**

   ```bash
   python3 --version
   # Should show: Python 3.8.x or higher
   ```

3. **Skip to Module 1**
   - Come back to Module 0 later
   - See real SDK in Module 6

---

### Issue: Module 0 Taking Longer Than Expected

**Expected times**:

- **First time (Docker)**: 15-20 minutes (includes download)
- **Subsequent runs (Docker)**: 10-15 minutes
- **Simulation Demo**: 5-10 minutes

**If taking longer**:

1. **Check what's taking time**
   - Docker image download? (2-5 minutes is normal)
   - Database initialization? (Should be <1 minute)
   - Demo execution? (Should be <2 minutes)

2. **Use Simulation Demo** for faster experience
   - Instant execution
   - No setup time
   - Same learning outcomes

3. **Continue anyway**
   - First-time setup is one-time cost
   - Subsequent runs will be faster

---

### Issue: Permission Denied Errors

**Symptoms**:

- "Permission denied" when creating files
- "Cannot write to directory"

**Causes**:

- Insufficient permissions in project directory
- Running in protected directory

**Solutions**:

1. **Check project directory permissions**

   ```bash
   ls -la
   ```

2. **Move to user directory**

   ```bash
   # Create project in home directory
   cd ~
   mkdir my-senzing-project
   cd my-senzing-project
   ```

3. **Fix permissions** (if needed)

   ```bash
   chmod 755 .
   ```

---

### Getting Help

**If none of these solutions work**:

1. **Try Simulation Demo**
   - Guaranteed to work
   - No dependencies
   - Shows same concepts

2. **Share error messages with agent**
   - Copy full error output
   - Describe what you tried
   - Agent can provide specific guidance

3. **Skip to Module 1**
   - Continue learning
   - Return to Module 0 later
   - See real SDK in Module 6

4. **Contact Senzing support**
   - Provide error details
   - Share environment info (OS, Docker version)
   - Include steps to reproduce

---

### Pre-Flight Check

**Before starting Module 0, verify your environment**:

Run the pre-flight check script:

```bash
./scripts/check_module0_prerequisites.sh
```

This will check:

- ✓ Docker availability
- ✓ Disk space
- ✓ Network connectivity
- ✓ Python installation

And provide recommendations based on your environment.

---

## Success Criteria

**For Docker Demo**:
✅ Senzing SDK is running (Docker or local installation)
✅ Demo script executes successfully
✅ Sample data loads without errors
✅ Entities are resolved and displayed with match explanations
✅ You understand what entity resolution does and WHY records matched
✅ You can see the before/after transformation
✅ You're excited to try it with your own data!

**For Simulation Demo**:
✅ Simulation script runs successfully
✅ Sample records displayed (before resolution)
✅ Resolved entities displayed (after resolution)
✅ Match explanations shown with confidence scores
✅ You understand entity resolution concepts
✅ You understand this is a simulation (not real SDK)
✅ You're ready to see the real SDK in Module 6!

**Either demo achieves the goal**: Understanding how entity resolution works!

## Related Documentation

- `../../POWER.md` - Boot camp overview
- `../../steering/steering.md` - Module 0 workflow
- `QUICK_START.md` - Quick start guide

## Version History

- **v3.0.0** (2026-03-17): Module 0 documentation created
