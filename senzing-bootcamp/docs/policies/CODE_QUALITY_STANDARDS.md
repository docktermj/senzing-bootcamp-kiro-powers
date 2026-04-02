# Code Quality Standards

## Overview

All source code generated during the Senzing Boot Camp must follow language-appropriate coding standards for the bootcamper's chosen programming language.

## Supported Languages

The boot camp supports the languages available through the Senzing MCP server. The agent queries the MCP server at the start of each session and asks the bootcamper to choose.

## Standards by Language

### Python

- **Style guide**: PEP-8
- **Max line length**: 100 characters
- **Indentation**: 4 spaces (never tabs)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants
- **Docstrings**: Triple quotes for all functions and classes
- **Imports**: Grouped (standard library, third-party, local), one per line, alphabetical within groups
- **Validation tools**: `pycodestyle`, `flake8`, `black`, `pylint`, `mypy`

### Java

- **Style guide**: Standard Java conventions
- **Indentation**: 4 spaces
- **Naming**: `camelCase` for methods/variables, `PascalCase` for classes, `UPPER_CASE` for constants
- **Documentation**: Javadoc for all public methods and classes
- **Imports**: Organized by package, no wildcard imports
- **Validation tools**: `checkstyle`, `spotbugs`, `PMD`

### C-sharp

- **Style guide**: .NET conventions
- **Indentation**: 4 spaces
- **Naming**: `PascalCase` for methods/classes/properties, `camelCase` for local variables/parameters, `UPPER_CASE` for constants
- **Documentation**: XML doc comments (`///`) for all public members
- **Imports**: `using` statements organized alphabetically
- **Validation tools**: `dotnet format`, Roslyn analyzers, StyleCop

### Rust

- **Style guide**: Rust community conventions
- **Indentation**: 4 spaces
- **Naming**: `snake_case` for functions/variables/modules, `PascalCase` for types/traits, `SCREAMING_SNAKE_CASE` for constants
- **Documentation**: `///` doc comments for public items
- **Validation tools**: `rustfmt`, `clippy`

### TypeScript / Node.js

- **Style guide**: Standard TypeScript conventions
- **Indentation**: 2 spaces
- **Naming**: `camelCase` for functions/variables, `PascalCase` for classes/interfaces/types, `UPPER_CASE` for constants
- **Documentation**: JSDoc or TSDoc for public functions and classes
- **Imports**: Organized (external, internal), no unused imports
- **Validation tools**: `eslint`, `prettier`, `tsc --noEmit`

## Agent Behavior

When generating code, the agent will:

1. Use the bootcamper's chosen language for all code generation
2. Follow the coding standards for that language
3. Add appropriate documentation (docstrings, Javadoc, XML doc, etc.)
4. Use proper naming conventions
5. Organize imports/using statements correctly
6. Keep lines within the language's standard max length

When users provide code, the agent will:

1. Check for coding standard compliance
2. Suggest fixes if non-compliant
3. Explain why compliance matters
4. Offer to fix issues automatically

## Version History

- **v2.0.0** (2026-04-01): Expanded from Python-only PEP-8 to multi-language standards
- **v1.0.0** (2026-03-17): Initial PEP-8 compliance documentation
