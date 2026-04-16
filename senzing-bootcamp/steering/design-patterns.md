---
inclusion: manual
---

# Entity Resolution Design Pattern Gallery

Offer this gallery during Module 2 to help users identify their use case.

## Patterns

| Pattern | Use Case | Key Matching | Typical ROI |
| ------- | -------- | ------------ | ----------- |
| Customer 360 | Unified customer view across touchpoints | Names, emails, phones, addresses | Improved service, targeted marketing |
| Fraud Detection | Identify fraud rings, synthetic identities | Names, addresses, devices, IPs | Loss prevention, faster detection |
| Data Migration | Merge legacy systems, M&A consolidation | All available identifiers | Reduced storage, simplified ops |
| Compliance Screening | Watchlist matching for regulatory compliance | Names, DOB, nationalities, IDs | Regulatory compliance, risk mitigation |
| Marketing Dedup | Eliminate duplicate contacts | Names, addresses, emails | Reduced mailing costs, better metrics |
| Patient Matching | Unified medical records across facilities | Names, DOB, SSN, MRNs | Patient safety, care coordination |
| Vendor MDM | Clean vendor master data | Company names, tax IDs, addresses | Better pricing, consolidated spend |
| Claims Fraud | Detect staged accidents, coordinated claims | Names, vehicles, providers | Reduced fraudulent payouts |
| KYC/Onboarding | Verify identity during account opening | Names, DOB, SSN, gov IDs | Reduced fraud, compliance |
| Supply Chain | Unified supplier view across supply chain | Company names, GLNs, tax IDs | Visibility, risk management |

## Which Pattern Fits?

Walk through these questions:

1. **What entities?** People → Q2. Organizations → Vendor MDM or Supply Chain. Both → Customer 360 or Data Migration.
2. **Primary goal?** Find duplicates → Marketing Dedup. Unify across systems → Customer 360 or Data Migration. Detect fraud → Fraud Detection or Claims Fraud. Regulatory → Compliance Screening or KYC. Patient care → Patient Matching.
3. **One-time or ongoing?** One-time → Data Migration or Marketing Dedup. Ongoing → Customer 360, Fraud Detection, Compliance Screening.

If the user's case spans multiple patterns, start with the one that delivers the most immediate business value.

## Agent Behavior

1. Present the table above
2. Walk through the 3 questions to narrow down
3. Use the selected pattern to guide Module 2 problem definition
4. Recommend key matching attributes for Module 5 data mapping
5. If multiple patterns apply, help prioritize implementation order

## Where Senzing Fits in Your Architecture

A common misconception is putting text search (Elasticsearch/OpenSearch) before entity resolution. The correct layering is:

```text
Raw Data → Senzing (entity resolution) → Resolved Entities → Search Index (Elasticsearch/OpenSearch)
```

**Senzing first:** Senzing performs fuzzy matching, identity intelligence, and entity resolution — it figures out which records refer to the same real-world entity. This is not text search; it's probabilistic identity matching using names, addresses, phones, IDs, and other features.

**Search index second:** After Senzing resolves entities, index the resolved entity IDs and their attributes into Elasticsearch/OpenSearch for fast document retrieval, faceted search, and full-text queries.

**Why this order matters:** If you search first and resolve second, you'll miss matches that Senzing would catch (name variations, address normalization, cross-source linking). Senzing's matching is fundamentally different from text search — it uses entity-centric learning, not keyword matching.

Present this architecture when the user's problem involves search, lookup, or retrieval alongside entity resolution. Reference it again in Module 8 (Query & Validation) when building query programs.
