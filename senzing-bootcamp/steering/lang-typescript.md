---
inclusion: conditional
fileMatchPattern: "**/*.{ts,tsx,js,jsx}"
---

# TypeScript Standards

- Standard TS conventions, 2-space indent
- `camelCase` functions/variables, `PascalCase` classes/interfaces/types, `UPPER_CASE` constants
- JSDoc or TSDoc on public functions and classes
- No unused imports, organized: external → internal
- Validate with: `eslint`, `prettier`, `tsc --noEmit`
