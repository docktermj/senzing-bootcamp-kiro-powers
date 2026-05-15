# Requirements: TypeScript/Node.js Language Maturity Alignment

## Overview

Ensure TypeScript/Node.js language support is accurately represented across the power, noting maturity differences compared to Python/Java/C# where they exist, and verifying `find_examples` coverage is equivalent.

## Requirements

1. Audit all module steering files for TypeScript-specific guidance gaps compared to other languages
2. Add maturity notes to POWER.md and lang-typescript.md if `find_examples` coverage for TypeScript is significantly lower than Python/Java
3. Verify `generate_scaffold` and `sdk_guide` produce equivalent quality output for TypeScript across all workflows (initialize, add_records, query, redo, full_pipeline)
4. Add TypeScript-specific troubleshooting entries to `common-pitfalls.md` for known SDK differences (async patterns, type definitions, ESM vs CJS)
5. Update `lang-typescript.md` with any platform-specific notes discovered during the audit (e.g., Node.js version requirements, native module compilation)
6. Ensure the onboarding language selection prompt does not imply all languages have identical support depth
