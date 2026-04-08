---
inclusion: conditional
fileMatchPattern: "**/*.cs"
---

# C# Standards

- .NET conventions, 4-space indent
- `PascalCase` methods/classes/properties, `camelCase` locals/parameters, `UPPER_CASE` constants
- XML doc comments (`///`) on all public members
- `using` statements alphabetical
- Validate with: `dotnet format`, Roslyn analyzers, StyleCop
