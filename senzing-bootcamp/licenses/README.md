# Senzing License Files

This directory is for storing your Senzing license file(s).

## Do I Need a License?

### Module 1 (Quick Demo)

**No license required** - Module 1 uses sample data and doesn't require a license.

### Module 0+ (SDK Installation and Beyond)

**License required** - You'll need a valid Senzing license to:

- Install and use the Senzing SDK
- Load your own data
- Perform entity resolution on production data
- Complete Modules 0 and 6-12

## How to Obtain a Senzing License

### Option 1: Evaluation License (Recommended for Boot Camp)

**For learning and evaluation purposes**, request a free evaluation license:

1. **Contact Senzing**:
   - **Email**: [support@senzing.com](mailto:support@senzing.com)
   - **Website**: [https://senzing.com/contact/](https://senzing.com/contact/)

2. **Request Information**:
   - Mention you're completing the Senzing Boot Camp
   - Specify "evaluation license" for learning purposes
   - Provide your name, company, and use case

3. **Receive License**:
   - Senzing will email you a `g2.lic` file
   - Typically received within 1-2 business days
   - Valid for evaluation period (usually 30-90 days)

4. **Install License**:
   - Save the `g2.lic` file to this directory: `licenses/g2.lic`
   - Ensure file permissions are readable: `chmod 644 licenses/g2.lic`
   - Restart any running Senzing processes

### Option 2: Production License

**For production deployments**, contact Senzing sales:

1. **Contact Senzing Sales**:
   - **Email**: [sales@senzing.com](mailto:sales@senzing.com)
   - **Website**: [https://senzing.com/contact/](https://senzing.com/contact/)

2. **Discuss Requirements**:
   - Number of data source records (DSRs)
   - Expected growth
   - Deployment environment (cloud, on-premise)
   - Support requirements

3. **Receive Quote**:
   - Senzing will provide pricing based on your needs
   - Licensing is typically based on DSR volume tiers

4. **Purchase and Install**:
   - Complete purchase process
   - Receive production license file
   - Install in `licenses/g2.lic`

### Option 3: Existing License

**If you already have a Senzing license**:

1. **System-Wide License** (already installed):
   - If Senzing is already installed with a system-wide license at `/etc/opt/senzing/g2.lic`
   - You don't need to place a license in this directory
   - The SDK will automatically use the system-wide license

2. **Project-Specific License** (recommended for boot camp):
   - Place your license file in this directory: `licenses/g2.lic`
   - This allows different projects to use different licenses
   - Useful for separating evaluation and production environments

## License File Placement

### Correct Location ✅

```text
licenses/
├── g2.lic                 # Your Senzing license file
├── .gitkeep               # Keeps directory in git
└── README.md              # This file
```

**Command**:

```bash
# Place your license file here
cp /path/to/your/g2.lic licenses/g2.lic

# Set proper permissions
chmod 644 licenses/g2.lic
```

### Incorrect Locations ❌

```text
❌ /tmp/g2.lic              # Temporary, will be deleted
❌ g2.lic                   # Project root (wrong location)
❌ config/g2.lic            # Config is for configuration, not licenses
❌ /etc/opt/senzing/g2.lic  # System-wide (use for system installation)
```

## License Priority

Senzing SDK checks for licenses in this order:

1. **Project-specific**: `licenses/g2.lic` (this directory)
2. **Environment variable**: `SENZING_LICENSE_PATH`
3. **System-wide**: `/etc/opt/senzing/g2.lic`

If you have a system-wide license, you don't need to place one here. The `licenses/` directory is for bootcampers who want a project-specific license.

## Verify License Installation

After placing your license file, verify it's working:

```bash
# Check if license file exists
ls -la licenses/g2.lic

# Verify Senzing can read the license
python3 -c "
from senzing import G2Product
import json

product = G2Product()
config = {
    'PIPELINE': {
        'CONFIGPATH': '/etc/opt/senzing',
        'LICENSESTRINGBASE64': open('licenses/g2.lic').read()
    }
}
product.init('LicenseCheck', json.dumps(config), False)
print('License valid!')
print('Version:', product.version())
product.destroy()
"
```

Expected output:

```text
License valid!
Version: 4.0.0
```

## Security and Git

### Important: Do NOT Commit License Files to Git

License files are sensitive and should never be committed to version control.

**The `.gitignore` file already excludes license files**:

```gitignore
# License files (sensitive - never commit)
licenses/*.lic

# Keep directory structure
!licenses/.gitkeep
!licenses/README.md
```

### Verify License is Ignored

```bash
# Check git status - license should not appear
git status

# If license appears, add to .gitignore
echo "licenses/*.lic" >> .gitignore
```

## License Types and Limitations

### Evaluation License

**Typical Limitations**:

- Time-limited (30-90 days)
- May have record count limits
- For evaluation and development only
- Not for production use

**Best for**:

- Completing the boot camp
- Proof of concept projects
- Learning and training
- Development and testing

### Production License

**Features**:

- No time limits
- Based on DSR volume tiers
- Production support included
- Suitable for production deployments

**Pricing Tiers** (approximate - contact Senzing for current pricing):

- **Tier 1**: Up to 1M DSRs
- **Tier 2**: 1M - 10M DSRs
- **Tier 3**: 10M - 100M DSRs
- **Tier 4**: 100M+ DSRs (custom pricing)

## Troubleshooting

### Issue: License File Not Found

**Symptoms**:

- Error: "License file not found"
- SDK initialization fails

**Solutions**:

1. Verify file exists: `ls -la licenses/g2.lic`
2. Check file permissions: `chmod 644 licenses/g2.lic`
3. Verify file path in configuration
4. Check for typos in filename (must be exactly `g2.lic`)

### Issue: License Expired

**Symptoms**:

- Error: "License expired"
- SDK refuses to initialize

**Solutions**:

1. Check license expiration date
2. Contact Senzing for license renewal
3. Request new evaluation license if needed
4. For production, contact sales for renewal

### Issue: License Invalid

**Symptoms**:

- Error: "Invalid license"
- License validation fails

**Solutions**:

1. Verify license file is not corrupted
2. Re-download license from Senzing
3. Check file encoding (should be plain text)
4. Contact Senzing support if issue persists

### Issue: Wrong License Type

**Symptoms**:

- License works but features are limited
- Record count limits exceeded

**Solutions**:

1. Verify license type (evaluation vs. production)
2. Check license limitations
3. Contact Senzing to upgrade license
4. Request appropriate license for your use case

## Frequently Asked Questions

### Can I use the boot camp without a license?

**Module 1 only**: Yes, Module 1 (Quick Demo) doesn't require a license.

**Module 0+**: No, you'll need a license to install the SDK and complete the remaining modules.

**Recommendation**: Request an evaluation license before starting Module 0.

### How long does it take to get an evaluation license?

Typically **1-2 business days** after contacting Senzing. Plan ahead!

### Can I share my license with others?

**No** - Senzing licenses are typically issued per user or organization. Each bootcamper should request their own evaluation license.

### What happens when my evaluation license expires?

- SDK will stop working
- You'll need to request a license renewal or purchase a production license
- Your data and configurations remain intact
- Contact Senzing before expiration to avoid interruption

### Do I need different licenses for development and production?

**Best practice**: Yes

- Use evaluation license for development and testing
- Use production license for production deployments
- Keep licenses separate by using project-specific license files

### Can I complete the boot camp with an expired license?

**No** - You'll need a valid license for Module 0+. Contact Senzing for renewal before your license expires.

## Contact Information

### Senzing Support

- **Email**: [support@senzing.com](mailto:support@senzing.com)
- **Website**: [https://senzing.com/support/](https://senzing.com/support/)

### Senzing Sales

- **Email**: [sales@senzing.com](mailto:sales@senzing.com)
- **Website**: [https://senzing.com/contact/](https://senzing.com/contact/)

### General Inquiries

- **Website**: [https://senzing.com](https://senzing.com)
- **Documentation**: [https://docs.senzing.com](https://docs.senzing.com)

## Next Steps

1. **Request License**: Contact Senzing for evaluation license
2. **Wait for Email**: Typically 1-2 business days
3. **Install License**: Place `g2.lic` in this directory
4. **Verify**: Run verification script above
5. **Continue Boot Camp**: Proceed to Module 0 (SDK Setup)

## Related Documentation

- **FAQ**: `docs/guides/FAQ.md` - Common questions about licensing
- **Module 0**: `docs/modules/MODULE_0_SDK_SETUP.md` - SDK installation
- **File Storage Policy**: `docs/policies/FILE_STORAGE_POLICY.md` - Where to store files
- **Cost Estimation**: Use MCP `search_docs` with query "pricing" for current information

---

**Need help?** Ask the Kiro agent or contact Senzing support.
