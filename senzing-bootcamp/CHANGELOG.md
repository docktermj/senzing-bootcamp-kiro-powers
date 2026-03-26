# Changelog

All notable changes to the Senzing Boot Camp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.26.0] - 2026-03-24

### Added

- Live demo implementation for Module 0 that actually runs Senzing SDK
- New demo template: `templates/demo_quick_start.py` with working entity resolution
- Match explanation display showing WHY records matched with confidence scores
- Before/after comparison showing transformation (e.g., 5 records → 3 entities)
- SDK availability check with Docker fallback option
- Detailed match explanations in demo output

### Changed

- Module 0 documentation now emphasizes live demonstration vs simulation
- Steering workflow updated to require actual SDK execution
- Demo workflow now shows sample records BEFORE resolution
- Enhanced example output with detailed match explanations and confidence scores
- Updated success criteria to include actual execution verification
- Improved troubleshooting section for SDK installation

### Fixed

- Module 0 now delivers on promise of "seeing entity resolution in action"
- Demo creates "aha moment" by showing real technology working
- First-time user experience significantly improved

### User Feedback Addressed

- Issue: Quick Demo only showed sample data without running Senzing
- Solution: Implemented live demo that actually runs SDK and shows match explanations
- Impact: Users now see real entity resolution and understand value immediately

## [0.25.3] - 2026-03-24

### Feedback in 0.25.3

- User feedback received about Module 0 not actually demonstrating Senzing in action
- Identified need for live demo vs static explanation

## [0.25.0] - 2026-03-17

### Added in 0.25.0

- Initial Module 0 (Quick Demo) documentation
- Sample dataset descriptions (Las Vegas, London, Moscow)
- Demo script structure documentation

## [0.24.0] - 2026-03-17

### Added in 0.24.0

- Complete boot camp power with 13 modules (0-12)
- Design pattern gallery with 10 common patterns
- 3 example projects (simple, multi-source, production)
- 10+ code templates for utilities
- Steering guides for all modules
- Progress tracking system
- PEP-8 compliance checking

### Documentation

- Complete module documentation (MODULE_0 through MODULE_12)
- Steering guide with detailed workflows
- Agent instructions and best practices
- Common pitfalls and troubleshooting guides

## Version History

- **v0.26.0** (2026-03-24): Live demo implementation for Module 0
- **v0.25.3** (2026-03-24): User feedback collection
- **v0.25.0** (2026-03-17): Initial Module 0 documentation
- **v0.24.0** (2026-03-17): Initial boot camp power release

## Feedback

We welcome feedback on the boot camp experience! Please document any issues, confusion points, or suggestions in `docs/feedback/`.

When you complete the boot camp, please share your feedback file with the power author.
