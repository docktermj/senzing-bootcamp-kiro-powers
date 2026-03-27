# Senzing Kiro Power

This repository contains the Senzing Boot Camp Kiro Power and its development documentation.

## Repository Structure

This repository is organized into two main directories:

### `senzing-bootcamp/` - The Power Distribution

Contains ONLY files that are part of the distributed power:

- `POWER.md` - Main power documentation with frontmatter metadata
- `mcp.json` - MCP server configuration
- `steering/` - Steering files for guided workflows
- `docs/` - User-facing documentation (guides, policies, feedback templates)
- `hooks/` - Kiro hook definitions
- `examples/` - Example projects
- `templates/` - Code templates
- `CHANGELOG.md` - Version history

**Audience**: Bootcamp users and AI agents running the bootcamp

### `senzing-bootcamp-power-development/` - Development Repository

Contains everything related to developing and maintaining the power:

- Development documentation
- Agent implementation guides
- Improvement notes and decisions
- Historical reference material
- Build and cleanup notes
- Testing documentation
- Reorganization summaries

**Audience**: Power developers, maintainers, and contributors

## For Contributors

When developing the power:

1. **User-facing content** goes in `senzing-bootcamp/`
2. **Development notes** go in `senzing-bootcamp-power-development/`
3. **Test changes** using the guide in `senzing-bootcamp-power-development/TESTING.md`
4. **Update CHANGELOG.md** for all user-facing changes
5. **Follow the repository organization** defined in `.kiro/steering/repository-organization.md`

## For Users

To use the Senzing Boot Camp power:

1. Install the power from the `senzing-bootcamp/` directory
2. Follow the instructions in `senzing-bootcamp/POWER.md`
3. Refer to user guides in `senzing-bootcamp/docs/guides/`

## References

- [Kiro Powers: Build Smarter Workflows with On‑Demand AI Capabilities]
- GitHub repositories hosting Kiro Powers
  - <https://github.com/kirodotdev/powers>

[Kiro Powers: Build Smarter Workflows with On‑Demand AI Capabilities]: https://builder.aws.com/content/373GVprvpSEBWTyj92tP5gq4LmW/kiro-powers-build-smarter-workflows-with-ondemand-ai-capabilities
