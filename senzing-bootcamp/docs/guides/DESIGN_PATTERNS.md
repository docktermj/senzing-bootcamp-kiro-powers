# Entity Resolution Design Patterns

## Overview

The Senzing Boot Camp includes 10 common entity resolution design patterns to help you identify and articulate your business problem. These patterns are presented during Module 2 when defining your use case.

To see the full pattern gallery with detailed matching attributes, expected outcomes, and agent guidance, ask the agent to load the `design-patterns.md` steering file:

> "Show me the entity resolution design patterns"

## Available Patterns

| Pattern | Use Case | Key Matching |
|---------|----------|--------------|
| Customer 360 | Unified customer view | Names, emails, phones, addresses |
| Fraud Detection | Identify fraud rings | Names, addresses, devices, IPs |
| Data Migration | Merge legacy systems | All available identifiers |
| Compliance Screening | Watchlist matching | Names, DOB, nationalities, IDs |
| Marketing Dedup | Eliminate duplicates | Names, addresses, emails |
| Patient Matching | Unified medical records | Names, DOB, SSN, MRNs |
| Vendor MDM | Clean vendor master | Company names, tax IDs, addresses |
| Claims Fraud | Detect staged accidents | Names, vehicles, providers |
| KYC/Onboarding | Verify identity | Names, DOB, SSN, gov IDs |
| Supply Chain | Unified supplier view | Company names, GLNs, tax IDs |

## How Patterns Are Used

1. During Module 2, the agent presents this gallery
2. You identify which pattern(s) match your situation
3. The selected pattern guides your problem definition, data source planning, and mapping priorities
4. Multiple patterns can be combined (e.g., Customer 360 + Fraud Detection)

## Detailed Pattern Information

Each pattern in the steering file includes:

- Typical scenario and best-fit industries
- Key matching attributes to focus on
- Expected outcomes and business value
- Guidance for combining with other patterns

For the full details, ask the agent or load `steering/design-patterns.md`.
