---
inclusion: manual
---

# Entity Resolution Design Pattern Gallery

When starting Module 2, offer users a gallery of common entity resolution patterns to help them identify which pattern(s) match their situation.

## Pattern Overview

| Pattern                  | Use Case                | Key Matching                      | Typical ROI                            |
|--------------------------|-------------------------|-----------------------------------|----------------------------------------|
| **Customer 360**         | Unified customer view   | Names, emails, phones, addresses  | Improved service, targeted marketing   |
| **Fraud Detection**      | Identify fraud rings    | Names, addresses, devices, IPs    | Loss prevention, faster detection      |
| **Data Migration**       | Merge legacy systems    | All available identifiers         | Reduced storage, simplified ops        |
| **Compliance Screening** | Watchlist matching      | Names, DOB, nationalities, IDs    | Regulatory compliance, risk mitigation |
| **Marketing Dedup**      | Eliminate duplicates    | Names, addresses, emails          | Reduced mailing costs, better metrics  |
| **Patient Matching**     | Unified medical records | Names, DOB, SSN, MRNs             | Patient safety, care coordination      |
| **Vendor MDM**           | Clean vendor master     | Company names, tax IDs, addresses | Better pricing, consolidated spend     |
| **Claims Fraud**         | Detect staged accidents | Names, vehicles, providers        | Reduced fraudulent payouts             |
| **KYC/Onboarding**       | Verify identity         | Names, DOB, SSN, gov IDs          | Reduced fraud, compliance              |
| **Supply Chain**         | Unified supplier view   | Company names, GLNs, tax IDs      | Visibility, risk management            |

## When to Use Each Pattern

### Customer 360

**Best for**: Multiple customer touchpoints, CRM consolidation

**Typical scenario**: You have customer data scattered across multiple systems (web, mobile, call center, retail) and need a unified view to improve service and marketing.

**Key matching attributes**:

- Names (including nicknames and variations)
- Email addresses
- Phone numbers
- Physical addresses
- Customer IDs from various systems

**Expected outcomes**:

- Single customer view across all touchpoints
- Better targeted marketing campaigns
- Improved customer service
- Reduced duplicate communications

### Fraud Detection

**Best for**: Financial services, insurance, e-commerce

**Typical scenario**: You need to identify fraud rings, synthetic identities, or coordinated fraudulent activity across accounts.

**Key matching attributes**:

- Names and aliases
- Addresses (especially shared addresses)
- Device fingerprints
- IP addresses
- Phone numbers
- Email addresses

**Expected outcomes**:

- Faster fraud detection
- Identification of fraud networks
- Reduced false positives
- Loss prevention

### Data Migration

**Best for**: M&A, system consolidation, cloud migration

**Typical scenario**: You're merging data from multiple legacy systems and need to eliminate duplicates while preserving all relationships.

**Key matching attributes**:

- All available identifiers from source systems
- Names, addresses, contact information
- Legacy system IDs
- Tax IDs, account numbers

**Expected outcomes**:

- Reduced storage costs
- Simplified operations
- Clean master data
- Preserved data relationships

### Compliance Screening

**Best for**: Banking, fintech, international trade

**Typical scenario**: You need to screen customers, vendors, or transactions against watchlists for regulatory compliance.

**Key matching attributes**:

- Full names and aliases
- Date of birth
- Nationalities
- Government IDs (passport, national ID)
- Addresses

**Expected outcomes**:

- Regulatory compliance
- Risk mitigation
- Reduced false positives
- Faster screening process

### Marketing Dedup

**Best for**: Email campaigns, direct mail, lead management

**Typical scenario**: You need to eliminate duplicate contacts to reduce costs and improve campaign metrics.

**Key matching attributes**:

- Names
- Addresses (mailing addresses)
- Email addresses
- Phone numbers

**Expected outcomes**:

- Reduced mailing costs
- Better campaign metrics
- Improved deliverability
- Enhanced customer experience

### Patient Matching

**Best for**: Hospital networks, HIE, patient portals

**Typical scenario**: You need to match patient records across facilities to ensure care coordination and patient safety.

**Key matching attributes**:

- Names (including maiden names)
- Date of birth
- Social Security Number
- Medical Record Numbers (MRNs)
- Addresses
- Phone numbers

**Expected outcomes**:

- Patient safety improvements
- Better care coordination
- Reduced duplicate records
- Improved clinical outcomes

### Vendor MDM

**Best for**: Procurement, accounts payable, spend analysis

**Typical scenario**: You need to consolidate vendor master data to improve pricing, reduce duplicates, and analyze spend.

**Key matching attributes**:

- Company names (including DBAs)
- Tax IDs (EIN, VAT)
- Addresses
- DUNS numbers
- Bank account information

**Expected outcomes**:

- Better pricing through volume consolidation
- Reduced duplicate vendors
- Improved spend visibility
- Streamlined procurement

### Claims Fraud

**Best for**: Insurance, workers comp, auto claims

**Typical scenario**: You need to detect staged accidents, coordinated claims, or fraudulent provider networks.

**Key matching attributes**:

- Names of claimants
- Vehicle information
- Provider information
- Addresses
- Phone numbers
- Dates and locations of incidents

**Expected outcomes**:

- Reduced fraudulent payouts
- Faster fraud detection
- Identification of fraud rings
- Lower loss ratios

### KYC/Onboarding

**Best for**: Banking, fintech, account opening

**Typical scenario**: You need to verify customer identity during onboarding and detect duplicate accounts or synthetic identities.

**Key matching attributes**:

- Full names
- Date of birth
- Social Security Number
- Government IDs
- Addresses
- Phone numbers

**Expected outcomes**:

- Reduced fraud during onboarding
- Regulatory compliance
- Faster account opening
- Better risk assessment

### Supply Chain

**Best for**: Manufacturing, logistics, procurement

**Typical scenario**: You need a unified view of suppliers across the supply chain to manage risk and improve visibility.

**Key matching attributes**:

- Company names
- GLNs (Global Location Numbers)
- Tax IDs
- Addresses
- DUNS numbers

**Expected outcomes**:

- Improved supply chain visibility
- Better risk management
- Consolidated supplier relationships
- Enhanced compliance

## Agent Behavior

When user starts Module 2:

1. Present this gallery and ask which pattern(s) match their situation
2. Help them identify the most relevant pattern(s)
3. Use the selected pattern to guide problem definition
4. Set realistic expectations based on the pattern's typical outcomes
5. Recommend key matching attributes to focus on during data mapping (Module 5)

## Multiple Patterns

Users may need to combine multiple patterns. For example:

- **Customer 360 + Fraud Detection**: Unified customer view with fraud monitoring
- **Vendor MDM + Compliance Screening**: Clean vendor master with watchlist screening
- **Patient Matching + Compliance**: Patient records with HIPAA compliance

When users identify multiple patterns, help them prioritize and plan the implementation order.
