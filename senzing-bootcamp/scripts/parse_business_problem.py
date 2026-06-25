#!/usr/bin/env python3
"""Parse business problem documents and derive query requirements.

Extracts success criteria and desired output fields from a business problem
markdown document (docs/business_problem.md) and derives query requirements
that can be used in Module 7 Step 1.

Usage:
    python senzing-bootcamp/scripts/parse_business_problem.py --file docs/business_problem.md
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BusinessProblemContent:
    """Structured content extracted from a business problem document.

    Args:
        success_criteria: List of measurable outcome strings from Success Criteria section.
        desired_output_format: The Format field from Desired Output section.
        desired_output_use_case: The Use case field from Desired Output section.
        desired_output_integration: The Integration field from Desired Output section.
    """

    success_criteria: list[str] = field(default_factory=list)
    desired_output_format: str = ""
    desired_output_use_case: str = ""
    desired_output_integration: str = ""


def parse_business_problem(content: str) -> BusinessProblemContent:
    """Extract Success Criteria bullets and Desired Output fields from markdown.

    Args:
        content: Raw markdown content of the business problem document.

    Returns:
        BusinessProblemContent with extracted fields.
    """
    bpc = BusinessProblemContent()

    # Extract Success Criteria section bullets
    sc_match = re.search(
        r"^##\s+Success\s+Criteria\s*\n(.*?)(?=^##\s|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if sc_match:
        section_text = sc_match.group(1)
        # Match bullet items (- or * prefix)
        bullets = re.findall(r"^\s*[-*]\s+(.+)$", section_text, re.MULTILINE)
        bpc.success_criteria = [b.strip() for b in bullets if b.strip()]

    # Extract Desired Output section fields
    do_match = re.search(
        r"^##\s+Desired\s+Output\s*\n(.*?)(?=^##\s|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    if do_match:
        section_text = do_match.group(1)

        # Extract **Format**: value
        fmt_match = re.search(
            r"\*\*Format\*\*\s*:\s*(.+?)$", section_text, re.MULTILINE
        )
        if fmt_match:
            bpc.desired_output_format = fmt_match.group(1).strip()

        # Extract **Use case**: value
        uc_match = re.search(
            r"\*\*Use\s+case\*\*\s*:\s*(.+?)$", section_text, re.MULTILINE
        )
        if uc_match:
            bpc.desired_output_use_case = uc_match.group(1).strip()

        # Extract **Integration**: value
        int_match = re.search(
            r"\*\*Integration\*\*\s*:\s*(.+?)$", section_text, re.MULTILINE
        )
        if int_match:
            bpc.desired_output_integration = int_match.group(1).strip()

    return bpc


def has_usable_content(bpc: BusinessProblemContent) -> bool:
    """Check if the parsed content has enough information to derive requirements.

    Returns True if at least one success criterion exists OR at least one
    desired output field is non-empty.

    Args:
        bpc: Parsed business problem content.

    Returns:
        True if usable content exists, False otherwise.
    """
    if bpc.success_criteria:
        return True
    if bpc.desired_output_format:
        return True
    if bpc.desired_output_use_case:
        return True
    if bpc.desired_output_integration:
        return True
    return False


def derive_query_requirements(
    bpc: BusinessProblemContent, max_count: int = 10
) -> list[dict[str, str]]:
    """Derive query requirements from business problem content.

    Produces between 1 and 10 query requirements, each with a "requirement"
    string and a "source" string indicating which success criterion or desired
    output field it derives from.

    Args:
        bpc: Parsed business problem content.
        max_count: Maximum number of requirements to derive (clamped to 1-10).

    Returns:
        List of dicts with "requirement" and "source" keys, bounded 1-10.
    """
    # Clamp max_count to valid range
    max_count = max(1, min(10, max_count))

    requirements: list[dict[str, str]] = []

    # Derive from success criteria
    for criterion in bpc.success_criteria:
        if len(requirements) >= max_count:
            break
        requirements.append({
            "requirement": f"Query to validate: {criterion}",
            "source": f"Success Criterion: {criterion}",
        })

    # Derive from desired output fields
    if bpc.desired_output_format and len(requirements) < max_count:
        requirements.append({
            "requirement": (
                f"Query to produce output in format: {bpc.desired_output_format}"
            ),
            "source": f"Desired Output Format: {bpc.desired_output_format}",
        })

    if bpc.desired_output_use_case and len(requirements) < max_count:
        requirements.append({
            "requirement": (
                f"Query supporting use case: {bpc.desired_output_use_case}"
            ),
            "source": f"Desired Output Use Case: {bpc.desired_output_use_case}",
        })

    if bpc.desired_output_integration and len(requirements) < max_count:
        requirements.append({
            "requirement": (
                f"Query for integration with: {bpc.desired_output_integration}"
            ),
            "source": f"Desired Output Integration: {bpc.desired_output_integration}",
        })

    # Ensure at least 1 requirement if there's any content at all
    if not requirements and has_usable_content(bpc):
        requirements.append({
            "requirement": "Query to address business problem objectives",
            "source": "Business Problem Document",
        })

    return requirements


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for parsing business problem documents.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    parser = argparse.ArgumentParser(
        description="Parse business problem document and derive query requirements"
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("docs/business_problem.md"),
        help="Path to business problem markdown file (default: docs/business_problem.md)",
    )
    args = parser.parse_args(argv)

    filepath: Path = args.file
    if not filepath.is_file():
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    content = filepath.read_text(encoding="utf-8")
    bpc = parse_business_problem(content)

    if not has_usable_content(bpc):
        print("No usable content found in business problem document.")
        print("Fallback: ask bootcamper directly for query requirements.")
        sys.exit(0)

    requirements = derive_query_requirements(bpc)

    print(f"Derived {len(requirements)} query requirement(s):\n")
    for i, req in enumerate(requirements, 1):
        print(f"  {i}. {req['requirement']}")
        print(f"     Source: {req['source']}")
        print()


if __name__ == "__main__":
    main()
