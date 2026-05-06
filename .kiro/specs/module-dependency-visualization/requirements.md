# Requirements: Module Dependency Visualization

## Overview

`module-dependencies.yaml` defines the module dependency graph but it's only machine-readable. This feature generates visual representations of the dependency graph showing the bootcamper's current position, completed modules, and available next steps.

## Requirements

1. A new script `senzing-bootcamp/scripts/visualize_dependencies.py` generates a text-based dependency graph from `config/module-dependencies.yaml` and `config/bootcamp_progress.json`
2. The default output is an ASCII diagram showing all 11 modules with their dependency relationships, using box-drawing characters for connections
3. Completed modules are marked with ✅, the current module with 📍, available (unlocked) modules with 🔓, and locked modules with 🔒
4. The diagram shows the four learning tracks as labeled paths through the graph, with the bootcamper's active track highlighted
5. Running `python visualize_dependencies.py --format mermaid` outputs a Mermaid flowchart diagram suitable for rendering in Markdown
6. Running `python visualize_dependencies.py --format text` (default) outputs the ASCII diagram
7. The agent can invoke this visualization when the bootcamper asks about their learning path, what's next, or module dependencies
8. The visualization is added to the `status.py` output as an optional section (shown with `--graph` flag)
9. The keyword "learning path", "module map", "dependency graph", and "what's next" in `steering-index.yaml` trigger the agent to offer the visualization
10. If no progress file exists, the visualization shows all modules as locked except Module 1 (the universal entry point)
11. The script uses stdlib only — ASCII rendering with box-drawing characters, no external graphing libraries
12. The Mermaid output includes node styling (green for complete, blue for current, gray for locked) via Mermaid class definitions

## Non-Requirements

- This does not generate image files (PNG, SVG) — text and Mermaid only
- This does not modify the dependency graph structure
- This does not replace the module-transitions.md steering logic
- This does not show time estimates (that's a separate feature)
