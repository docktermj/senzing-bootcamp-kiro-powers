# Installation Verification Policy

## Policy

Before performing any software installation (especially Senzing), always verify that the software hasn't already been installed. This prevents conflicts, duplicate installations, and wasted time.

## Why This Matters

Users may:
- Try the boot camp multiple times
- Have Senzing already installed from previous attempts
- Be working in a shared environment
- Have multiple Python environments
- Be testing different configurations

Installing over an existing installation can cause:
- Version conflicts
- Configuration corruption
- Database connection issues
- Wasted time
- Frustration

## Verification Steps for Senzing

### Step 1: Check Python Package

```bash
# Check if Senzing Python package is installed
python -c "import senzing; print('Senzing version:', senzing.__version__)" 2>/dev/null

# Alternative: Check with pip
pip list | grep senzing

# Alternative: Check with pip show
pip show senzing
```

**Expected output if installed**:
```
Senzing version: 4.0.0
```

**Expected output if NOT installed**:
```
ModuleNotFoundError: No module named 'senzing'
```

### Step 2: Check Installation Directories

```bash
# Check for Senzing installation directory (Linux/macOS)
ls -la /opt/senzing 2>/dev/null

# Check for Senzing configuration directory
ls -la /etc/opt/senzing 2>/dev/null

# Check for Senzing data directory
ls -la /var/opt/senzing 2>/dev/null
```

**Expected output if installed**:
```
drwxr-xr-x  5 root root 4096 Jan 17 10:00 /opt/senzing
drwxr-xr-x  3 root root 4096 Jan 17 10:00 /etc/opt/senzing
drwxr-xr-x  4 root root 4096 Jan 17 10:00 /var/opt/senzing
```

**Expected output if NOT installed**:
```
ls: cannot access '/opt/senzing': No such file or directory
```

### Step 3: Test Engine Initialization

```python
# test_senzing_installation.py
import sys

try:
    import senzing
    from senzing import G2Engine
    
    print(f"✅ Senzing package found")
    print(f"   Version: {senzing.__version__}")
    
    # Try to initialize engine
    engine = G2Engine()
    print(f"✅ Senzing engine initialized successfully")
    engine.destroy()
    
    print("\n✅ Senzing is installed and working")
    sys.exit(0)
    
except ImportError:
    print("❌ Senzing package not found")
    print("   Senzing is NOT installed")
    sys.exit(1)
    
except Exception as e:
    print(f"⚠️  Senzing package found but engine initialization failed")
    print(f"   Error: {e}")
    print("   Installation may be incomplete or corrupted")
    sys.exit(2)
```

Run with:
```bash
python test_senzing_installation.py
```

## Decision Tree

```
Is Senzing installed?
│
├─→ YES → Check version
│   │
│   ├─→ Compatible version (V4.0 or V3.x)?
│   │   │
│   │   ├─→ YES → Use existing installation
│   │   │   └─→ Skip to configuration (Module 4, step 5)
│   │   │
│   │   └─→ NO → Ask user
│   │       ├─→ Keep old version? → Use it (may have limitations)
│   │       └─→ Upgrade? → Uninstall old, install new
│   │
│   └─→ Installation broken/corrupted?
│       └─→ Uninstall and reinstall
│
└─→ NO → Proceed with installation
    └─→ Follow Module 4 installation steps
```

## Agent Behavior

### Before Module 4 (SDK Setup)

1. **Always check first**:
   ```python
   # Run verification check
   python -c "import senzing; print(senzing.__version__)" 2>/dev/null
   ```

2. **If installed**:
   - Inform user: "Senzing version X.X is already installed"
   - Ask: "Would you like to use the existing installation?"
   - If yes: Skip to configuration (step 5)
   - If no: Provide uninstall instructions, then install

3. **If not installed**:
   - Proceed with installation steps
   - Use `sdk_guide` for platform-specific commands

4. **If installation broken**:
   - Inform user of the issue
   - Recommend uninstall and clean reinstall
   - Provide troubleshooting guidance

### During Installation

1. **Don't assume**:
   - Don't assume Senzing is not installed
   - Don't assume user wants to reinstall
   - Don't assume existing installation is broken

2. **Communicate clearly**:
   - Tell user what you're checking
   - Explain what you found
   - Explain options available

3. **Respect user choice**:
   - If user wants to keep existing installation, use it
   - If user wants to reinstall, help with that
   - If user is unsure, recommend using existing if compatible

## Verification Commands by Platform

### Linux (apt-based)
```bash
# Check package
dpkg -l | grep senzing

# Check Python package
python3 -c "import senzing; print(senzing.__version__)"

# Check directories
ls -la /opt/senzing /etc/opt/senzing /var/opt/senzing
```

### Linux (yum-based)
```bash
# Check package
rpm -qa | grep senzing

# Check Python package
python3 -c "import senzing; print(senzing.__version__)"

# Check directories
ls -la /opt/senzing /etc/opt/senzing /var/opt/senzing
```

### macOS
```bash
# Check Python package
python3 -c "import senzing; print(senzing.__version__)"

# Check with pip
pip3 list | grep senzing

# Check Homebrew (if installed via brew)
brew list | grep senzing
```

### Windows
```powershell
# Check Python package
python -c "import senzing; print(senzing.__version__)"

# Check with pip
pip list | findstr senzing

# Check installation directory
dir "C:\Program Files\Senzing"
```

### Docker
```bash
# Check if Senzing container exists
docker ps -a | grep senzing

# Check if Senzing image exists
docker images | grep senzing

# Check if container is running
docker ps | grep senzing
```

## Uninstall Instructions (if needed)

### Python Package Only
```bash
pip uninstall senzing
```

### Full Installation (Linux apt)
```bash
sudo apt-get remove senzing-api
sudo apt-get purge senzing-api
sudo rm -rf /opt/senzing /etc/opt/senzing /var/opt/senzing
```

### Full Installation (Linux yum)
```bash
sudo yum remove senzing-api
sudo rm -rf /opt/senzing /etc/opt/senzing /var/opt/senzing
```

### Full Installation (macOS)
```bash
pip3 uninstall senzing
# If installed via Homebrew
brew uninstall senzing
```

### Docker
```bash
# Stop and remove container
docker stop senzing-container
docker rm senzing-container

# Remove image (optional)
docker rmi senzing/senzing-tools
```

## Documentation Updates

All documentation has been updated to include verification:

### steering/steering.md - Module 4
- ✅ Added "Check if Senzing is already installed" as first step
- ✅ Verification commands for Python, system, and pip
- ✅ Decision tree for existing installations
- ✅ Skip to configuration if already installed
- ✅ Test scripts for verification

### steering/agent-instructions.md
- ✅ Added "Check if Senzing is already installed before installing"
- ✅ Verify existing installation version and compatibility
- ✅ Skip installation if compatible version exists

### steering/common-pitfalls.md
- ✅ New pitfall: "Installing Over Existing Installation"
- ✅ Verification commands
- ✅ Solution: Always check first

### steering/quick-reference.md
- ✅ Added verification check as FIRST step in Module 4
- ✅ Important note: "Always verify Senzing is not already installed"

### POWER.md
- ✅ Module 4 description updated: "Check if Senzing is already installed"

## Testing the Verification

Create a test script to verify the verification process:

```bash
#!/bin/bash
# test_verification.sh

echo "Testing Senzing installation verification..."
echo ""

echo "1. Checking Python package..."
if python -c "import senzing; print('Found:', senzing.__version__)" 2>/dev/null; then
    echo "   ✅ Senzing Python package is installed"
else
    echo "   ❌ Senzing Python package is NOT installed"
fi
echo ""

echo "2. Checking installation directories..."
if [ -d "/opt/senzing" ]; then
    echo "   ✅ /opt/senzing exists"
else
    echo "   ❌ /opt/senzing does not exist"
fi

if [ -d "/etc/opt/senzing" ]; then
    echo "   ✅ /etc/opt/senzing exists"
else
    echo "   ❌ /etc/opt/senzing does not exist"
fi

if [ -d "/var/opt/senzing" ]; then
    echo "   ✅ /var/opt/senzing exists"
else
    echo "   ❌ /var/opt/senzing does not exist"
fi
echo ""

echo "3. Testing engine initialization..."
python test_senzing_installation.py
```

## Summary

✅ Always verify before installing  
✅ Check Python package, directories, and engine  
✅ Use existing installation if compatible  
✅ Ask user before reinstalling  
✅ Provide clear communication  
✅ All documentation updated  
✅ Agent instructions include verification  
✅ Common pitfalls guide includes this issue
