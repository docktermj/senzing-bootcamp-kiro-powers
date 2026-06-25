#!/usr/bin/env python3
"""Senzing Bootcamp - Volume Utility Module.

Provides record volume parsing, tier classification, persistence, and
guidance generation for the Module 6 volume guidance step.

Usage:
    python volume_utils.py
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIER_DEMO = "demo"
TIER_SMALL = "small"
TIER_MEDIUM = "medium"
TIER_LARGE = "large"
VALID_TIERS = (TIER_DEMO, TIER_SMALL, TIER_MEDIUM, TIER_LARGE)

TIER_BOUNDARIES: dict[str, tuple[int | float, int | float]] = {
    TIER_DEMO: (0, 500),
    TIER_SMALL: (500, 500_000),
    TIER_MEDIUM: (500_000, 10_000_000),
    TIER_LARGE: (10_000_000, float("inf")),
}


# ---------------------------------------------------------------------------
# License framing constants and value object
# ---------------------------------------------------------------------------

# Expansion path identifiers (stable, ordered). The canonical order is
# apply-existing, external-request, then in-flow MCP (when applicable).
PATH_APPLY_EXISTING = "apply_existing"      # apply an existing Senzing license
PATH_EXTERNAL_REQUEST = "external_request"  # request via support channel
PATH_IN_FLOW_MCP = "in_flow_mcp"            # request in-flow via submit_feedback


@dataclass(frozen=True)
class LicenseFramingContext:
    """Inputs the agent gathers (from MCP + known state) for license framing.

    The agent retrieves Senzing facts from the Senzing MCP server at request
    time and passes them in here; the pure framing helpers never embed
    hardcoded figures. ``capacity`` / ``validity`` are ``None`` when the MCP
    server does not return them or cannot be reached — the framing then omits
    the figure entirely.

    Attributes:
        capacity: Record capacity from the MCP server, or None when unavailable.
        validity: Validity period from the MCP server, or None when unavailable.
        submit_feedback_available: Whether the in-flow MCP ``submit_feedback``
            tool is available (from ``get_capabilities``).
        has_existing_license: Whether the bootcamper already has a Senzing
            license (from bootcamp preferences / their answer).
        mention_downsizing: Whether downsizing should be mentioned as one option.
    """

    capacity: int | None = None
    validity: str | None = None
    submit_feedback_available: bool = False
    has_existing_license: bool = False
    mention_downsizing: bool = True


def build_expansion_paths(
    submit_feedback_available: bool,
    has_existing_license: bool,
) -> list[str]:
    """Return the applicable expansion path ids, in canonical order.

    The canonical order is apply-existing, external-request, then in-flow MCP
    (when applicable).

    - apply-existing (``PATH_APPLY_EXISTING``) is always included.
    - external-request (``PATH_EXTERNAL_REQUEST``) is always included.
    - in-flow MCP (``PATH_IN_FLOW_MCP``) is included only when
      ``submit_feedback_available`` is True AND the bootcamper does not already
      have a license (``has_existing_license`` is False).

    Args:
        submit_feedback_available: Whether the in-flow MCP ``submit_feedback``
            tool is available (from ``get_capabilities``).
        has_existing_license: Whether the bootcamper already has a Senzing
            license.

    Returns:
        Ordered list of expansion path id strings.
    """
    paths: list[str] = [PATH_APPLY_EXISTING, PATH_EXTERNAL_REQUEST]

    if submit_feedback_available and not has_existing_license:
        paths.append(PATH_IN_FLOW_MCP)

    return paths


# Human-readable description for each expansion path id. The in-flow MCP path
# refers to the Senzing MCP server by name only — never by URL.
_EXPANSION_PATH_DESCRIPTIONS: dict[str, str] = {
    PATH_APPLY_EXISTING: (
        "**Apply an existing license** — if you already have a Senzing license, "
        "apply it to unlock its full record capacity."
    ),
    PATH_EXTERNAL_REQUEST: (
        "**Request an evaluation license** — request a larger evaluation license "
        "through the Senzing support channel."
    ),
    PATH_IN_FLOW_MCP: (
        "**Request an evaluation license in-flow** — request one without leaving "
        "the bootcamp by asking the Senzing MCP server to submit a license request "
        "for you (the `submit_feedback` tool with the `license_request` category)."
    ),
}


def build_license_framing(
    *,
    capacity: int | None = None,
    validity: str | None = None,
    submit_feedback_available: bool = False,
    has_existing_license: bool = False,
    mention_downsizing: bool = True,
) -> str:
    """Build the canonical "default license + expansion paths" framing text.

    Produces the single source-of-truth wording every dataset-sizing touchpoint
    reuses, so the message cannot drift between touchpoints. The text describes
    the built-in evaluation license as a default the bootcamper already has,
    lists the applicable expansion paths, and (optionally) notes downsizing as
    one option among several.

    Senzing facts are passed in by the agent from the Senzing MCP server and are
    never hardcoded: when ``capacity`` or ``validity`` is ``None`` the figure is
    omitted and the text states the value is currently unavailable from the MCP
    server.

    Args:
        capacity: Record capacity from the MCP server, or None when unavailable.
        validity: Validity period from the MCP server, or None when unavailable.
        submit_feedback_available: Whether the in-flow MCP ``submit_feedback``
            tool is available (from ``get_capabilities``).
        has_existing_license: Whether the bootcamper already has a Senzing
            license.
        mention_downsizing: Whether to mention downsizing as one option.

    Returns:
        The canonical framing text. Describes the limit as a built-in evaluation
        license the bootcamper already has, renders a description for every path
        from :func:`build_expansion_paths`, includes capacity/validity only when
        provided, positions expansion options before any downsizing mention, and
        refers to the Senzing MCP server by name only (no URLs).
    """
    lines: list[str] = []

    # --- Default-license framing (never a hard cap) ---
    lines.append(
        "**Your evaluation license:** Senzing includes a built-in evaluation "
        "license that you already have by default — it lets you start processing "
        "records right away with no license file."
    )

    # --- Capacity / validity facts (sourced from MCP, never hardcoded) ---
    if capacity is not None:
        lines.append(
            f"It currently covers up to {capacity} records, as reported by the "
            "Senzing MCP server."
        )
    else:
        lines.append(
            "Its exact record capacity is currently unavailable from the MCP "
            "server, so no specific figure is shown here."
        )

    if validity is not None:
        lines.append(
            f"Its validity period is {validity}, as reported by the Senzing MCP "
            "server."
        )
    else:
        lines.append(
            "Its validity period is currently unavailable from the MCP server, "
            "so no specific figure is shown here."
        )

    # --- Expansion paths (presented before/alongside any downsizing mention) ---
    lines.append(
        "\nIf your data is larger than the built-in evaluation license covers, "
        "you have options to process more records:"
    )
    for path_id in build_expansion_paths(submit_feedback_available, has_existing_license):
        lines.append(f"- {_EXPANSION_PATH_DESCRIPTIONS[path_id]}")

    # --- Downsizing as one option among several (after expansion options) ---
    if mention_downsizing:
        lines.append(
            "\nDownsizing your dataset (sampling, a smaller substitute, or a CORD "
            "subset) is also an option — but it is just one choice alongside the "
            "expansion paths above, not the only way forward."
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Word multiplier mappings
# ---------------------------------------------------------------------------

_WORD_MULTIPLIERS: dict[str, int] = {
    "thousand": 1_000,
    "thousands": 1_000,
    "million": 1_000_000,
    "millions": 1_000_000,
    "billion": 1_000_000_000,
    "billions": 1_000_000_000,
}

_SUFFIX_MULTIPLIERS: dict[str, int] = {
    "k": 1_000,
    "m": 1_000_000,
    "b": 1_000_000_000,
}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_volume_input(text: str) -> int | None:
    """Parse free-text volume input into an integer record count.

    Handles: plain digits, comma-separated ("1,000,000"), abbreviations
    ("1M", "500k", "10m"), decimal abbreviations ("1.5M"), and
    plain-language multipliers ("10 million", "5 thousand", "1.5 million").

    Args:
        text: Raw bootcamper input string.

    Returns:
        Integer record count, or None if unparseable.
    """
    if not text or not text.strip():
        return None

    cleaned = text.strip().lower()

    # Try word multiplier pattern: number (with optional decimal) followed by word
    # e.g., "10 million", "1.5 billion", "5 thousand"
    word_pattern = r"(\d[\d,]*\.?\d*)\s+(thousand|thousands|million|millions|billion|billions)"
    word_match = re.search(word_pattern, cleaned)
    if word_match:
        num_str = word_match.group(1).replace(",", "")
        word = word_match.group(2)
        multiplier = _WORD_MULTIPLIERS[word]
        return int(float(num_str) * multiplier)

    # Try suffix pattern: number (with optional decimal) followed by K/M/B
    # e.g., "500k", "1M", "1.5M", "2B"
    suffix_pattern = r"(\d[\d,]*\.?\d*)\s*([kmb])\b"
    suffix_match = re.search(suffix_pattern, cleaned)
    if suffix_match:
        num_str = suffix_match.group(1).replace(",", "")
        suffix = suffix_match.group(2)
        multiplier = _SUFFIX_MULTIPLIERS[suffix]
        return int(float(num_str) * multiplier)

    # Try plain digits or comma-separated digits
    # e.g., "1000000", "1,000,000"
    plain_pattern = r"(\d{1,3}(?:,\d{3})+|\d+)"
    plain_match = re.search(plain_pattern, cleaned)
    if plain_match:
        num_str = plain_match.group(1).replace(",", "")
        try:
            return int(num_str)
        except ValueError:
            return None

    return None


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def classify_tier(record_count: int) -> str:
    """Classify a record count into a volume tier.

    Uses TIER_BOUNDARIES to determine which tier the given record count
    falls into based on inclusive lower and exclusive upper bounds.

    Args:
        record_count: Non-negative integer record count.

    Returns:
        One of: "demo", "small", "medium", "large".

    Raises:
        ValueError: If record_count is negative.
    """
    if record_count < 0:
        raise ValueError(f"record_count must be non-negative, got {record_count}")

    for tier, (lower, upper) in TIER_BOUNDARIES.items():
        if record_count >= lower and record_count < upper:
            return tier

    # Should not be reachable given TIER_LARGE upper is infinity
    return TIER_LARGE  # pragma: no cover


def should_ask_volume(preferences: dict) -> bool:
    """Determine if the volume question should be asked.

    Returns False if preferences contains a valid production_volume entry
    (both raw_value as int and tier as recognized string). Returns True
    otherwise (missing, empty, invalid tier, non-integer raw_value).

    Args:
        preferences: Parsed bootcamp_preferences dict.

    Returns:
        True if the volume question should be asked.
    """
    if not isinstance(preferences, dict):
        return True

    production_volume = preferences.get("production_volume")
    if not isinstance(production_volume, dict):
        return True

    raw_value = production_volume.get("raw_value")
    if not isinstance(raw_value, int):
        return True

    tier = production_volume.get("tier")
    if tier not in VALID_TIERS:
        return True

    return False


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def persist_volume_selection(
    raw_value: int,
    tier: str,
    preferences_path: str,
    progress_path: str,
    step_number: int,
) -> None:
    """Persist volume selection to preferences and write checkpoint.

    Writes production_volume key to preferences YAML and updates
    progress JSON with the step number.

    Creates parent directories if they don't exist.

    Args:
        raw_value: Parsed integer record count.
        tier: Classified tier string.
        preferences_path: Path to bootcamp_preferences.yaml.
        progress_path: Path to bootcamp_progress.json.
        step_number: Step number for checkpoint.

    Raises:
        OSError: If files cannot be written.
    """
    prefs_path = Path(preferences_path)
    prog_path = Path(progress_path)

    # --- Write production_volume to preferences YAML ---
    prefs_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing content if file exists
    existing_lines: list[str] = []
    if prefs_path.is_file():
        existing_lines = prefs_path.read_text(encoding="utf-8").splitlines()

    # Build the new production_volume YAML block
    new_block = [
        "production_volume:",
        f"  raw_value: {raw_value}",
        f"  tier: {tier}",
    ]

    # Find and replace existing production_volume section, or append
    output_lines: list[str] = []
    i = 0
    found = False
    while i < len(existing_lines):
        line = existing_lines[i]
        stripped = line.strip()
        if stripped == "production_volume:" or stripped.startswith("production_volume:"):
            # Replace this key and its indented sub-keys
            found = True
            output_lines.extend(new_block)
            i += 1
            # Skip indented lines belonging to this key
            while i < len(existing_lines):
                next_line = existing_lines[i]
                if next_line == "" or next_line[0] in (" ", "\t"):
                    i += 1
                else:
                    break
        else:
            output_lines.append(line)
            i += 1

    if not found:
        # Append the new block at the end
        if output_lines and output_lines[-1].strip() != "":
            output_lines.append("")
        output_lines.extend(new_block)

    # Write preferences file
    prefs_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")

    # --- Write step checkpoint to progress JSON ---
    prog_path.parent.mkdir(parents=True, exist_ok=True)

    progress_data: dict = {}
    if prog_path.is_file():
        content = prog_path.read_text(encoding="utf-8")
        if content.strip():
            progress_data = json.loads(content)

    # Update current_step and step_history
    progress_data["current_step"] = step_number
    step_history = progress_data.setdefault("step_history", {})
    # Use module 6 as the module number for this step
    step_history["6"] = {
        "last_completed_step": step_number,
        "updated_at": _utc_now_iso(),
    }

    prog_path.write_text(
        json.dumps(progress_data, indent=2) + "\n", encoding="utf-8"
    )


def _utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string.

    Returns:
        ISO 8601 formatted UTC timestamp.
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Guidance generators
# ---------------------------------------------------------------------------


def get_license_guidance(
    tier: str | None,
    *,
    capacity: int | None = None,
    validity: str | None = None,
    submit_feedback_available: bool = False,
    has_existing_license: bool = False,
) -> str | None:
    """Generate license guidance text for the given tier.

    Refactored to own no hardcoded Senzing facts: the demo tier no longer
    embeds a hardcoded record figure, and non-demo tiers delegate to
    :func:`build_license_framing` so the canonical "default license + expansion
    paths" wording cannot drift. The Senzing MCP server URL never appears in the
    output (it lives only in ``mcp.json``); Senzing facts are passed in by the
    agent from the MCP server and are omitted when unavailable.

    The keyword-only fact/flag parameters default to the safe
    figure-omitted, in-flow-omitted framing, matching the behavior when the MCP
    server's facts are unavailable.

    Args:
        tier: Volume tier string, or None if not set.
        capacity: Record capacity from the MCP server, or None when unavailable.
        validity: Validity period from the MCP server, or None when unavailable.
        submit_feedback_available: Whether the in-flow MCP ``submit_feedback``
            tool is available (from ``get_capabilities``).
        has_existing_license: Whether the bootcamper already has a Senzing
            license.

    Returns:
        Formatted guidance string, or None if tier is not set (skip).
    """
    if tier is None:
        return None

    if tier == TIER_DEMO:
        # Demo tier (<= built-in evaluation limit): the built-in evaluation
        # license is sufficient for the stated volume. Include the specific
        # figure only when the agent supplies it from the MCP server.
        if capacity is not None:
            figure = (
                f" (it currently covers up to {capacity} records, as reported by "
                "the Senzing MCP server)"
            )
        else:
            figure = ""
        return (
            "**License guidance:** The built-in evaluation license you already "
            f"have is sufficient for your stated volume{figure}. No additional "
            "license action is needed."
        )

    # small, medium, large: present the canonical default-license + expansion
    # paths framing, sourced from the Senzing MCP server (never hardcoded).
    return build_license_framing(
        capacity=capacity,
        validity=validity,
        submit_feedback_available=submit_feedback_available,
        has_existing_license=has_existing_license,
    )


def get_architecture_guidance(tier: str) -> str:
    """Generate architecture guidance text for the given tier.

    Always includes production recommendation label and bootcamp
    single-threaded disclaimer.

    Args:
        tier: Volume tier string.

    Returns:
        Formatted guidance string.
    """
    lines: list[str] = ["**Production Recommendation — Loading Architecture:**\n"]

    if tier == TIER_DEMO:
        lines.append(
            "Single-threaded loading is sufficient for your stated volume. "
            "No additional architecture planning is needed."
        )
    elif tier == TIER_SMALL:
        lines.append(
            "Single-threaded loading is recommended for initial loads at this scale. "
            "Multi-threading becomes beneficial beyond 100,000 records."
        )
    elif tier == TIER_MEDIUM:
        lines.append(
            "Multi-threaded loading with a thread pool is recommended for your volume.\n\n"
            "For production patterns, use the MCP `generate_scaffold` tool with your "
            "`record_count` parameter to generate an optimized threaded loader.\n\n"
            "If the MCP tool is unavailable, you can invoke it manually later:\n"
            "  generate_scaffold(record_count=<your_count>)"
        )
    elif tier == TIER_LARGE:
        lines.append(
            "Distributed or queue-based loading architecture is recommended for your volume.\n\n"
            "For platform-specific patterns, use the MCP `sdk_guide` tool with "
            "`topic='load'` to get detailed distributed loading guidance.\n\n"
            "If the MCP tool is unavailable, you can invoke it manually later:\n"
            "  sdk_guide(topic='load')"
        )
    else:
        # Fallback for unrecognized tier — still provide generic guidance
        lines.append(
            "Single-threaded loading is recommended as a starting point. "
            "Consult the MCP server for architecture guidance tailored to your volume."
        )

    lines.append(
        "\n\n*Note: The bootcamp uses single-threaded loading for learning purposes "
        "regardless of your production tier.*"
    )

    return "\n".join(lines)


def get_database_guidance(tier: str, current_database: str = "sqlite") -> str:
    """Generate database guidance text for the given tier.

    Args:
        tier: Volume tier string.
        current_database: Currently configured database type.

    Returns:
        Formatted guidance string.
    """
    lines: list[str] = []

    if tier in (TIER_DEMO, TIER_SMALL):
        lines.append(
            "**Database guidance:** SQLite is sufficient for production use at your "
            "stated volume. No database change is needed."
        )
    elif tier in (TIER_MEDIUM, TIER_LARGE):
        db = current_database.lower()
        if db == "postgresql":
            lines.append(
                "**Database guidance:** Your environment is already configured with "
                "PostgreSQL, which is well suited for production use at your stated volume."
            )
        else:
            lines.append(
                "**Database guidance:** For production use at your stated volume, "
                "PostgreSQL is recommended. SQLite is limited to a single concurrent "
                "writer, which becomes a bottleneck when loading or querying at volumes "
                "above 500K records."
            )

    # Bootcamp-continues disclaimer (all tiers)
    lines.append(
        f"\nThe bootcamp continues using the currently configured database "
        f"({current_database}). Database migration is covered in a later module."
    )

    return "\n".join(lines)


def get_performance_guidance(tier: str) -> str:
    """Generate performance expectations text for the given tier.

    Always references MCP search_docs with category="configuration".

    Args:
        tier: Volume tier string.

    Returns:
        Formatted guidance string.
    """
    mcp_reference = (
        "For current performance guidance, use the MCP `search_docs` tool with "
        '`category="configuration"`.'
    )

    if tier in (TIER_DEMO, TIER_SMALL):
        return (
            "**Performance expectations:** Loading completes in seconds to minutes "
            "at your stated volume. No additional configuration beyond default settings "
            f"is needed for acceptable load performance.\n\n{mcp_reference}"
        )

    if tier == TIER_MEDIUM:
        return (
            "**Performance expectations:** Loading takes minutes to hours depending on "
            "CPU core count and thread configuration. Module 8 (Performance) covers "
            f"optimization techniques for this scale.\n\n{mcp_reference}"
        )

    # large tier
    return (
        "**Performance expectations:** Loading takes hours to days at this volume. "
        "Distributed architecture and hardware planning are required for production "
        "deployment at this scale. Modules 8 and 11 cover optimization and "
        f"deployment strategies.\n\n{mcp_reference}"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Run volume utilities.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    parser = argparse.ArgumentParser(
        description="Senzing Bootcamp - Volume Utility Module."
    )
    parser.parse_args(argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":
    main()
