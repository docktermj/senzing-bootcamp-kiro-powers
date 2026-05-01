#!/usr/bin/env python3
"""Senzing Bootcamp - Verbosity Control Logic.

Pure-function module for managing bootcamp verbosity preferences.
Provides preset resolution, natural language term matching, category
level adjustment with clamping, and preferences YAML serialization.

All functions are stdlib-only (no PyYAML).

Usage:
    from verbosity import resolve_preset, adjust_category, match_nl_term

    prefs = resolve_preset("standard")
    prefs = adjust_category(prefs, "explanations", +1)
    category = match_nl_term("code detail")  # -> "code_walkthroughs"
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class VerbosityPreferences:
    """A bootcamper's verbosity settings.

    Attributes:
        preset: One of "concise", "standard", "detailed", or "custom".
        categories: Mapping of category name to verbosity level (1-3).
    """

    preset: str
    categories: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CATEGORIES: list[str] = [
    "explanations",
    "code_walkthroughs",
    "step_recaps",
    "technical_details",
    "code_execution_framing",
]
"""The five defined output category names."""

PRESETS: dict[str, dict[str, int]] = {
    "concise": {
        "explanations": 1,
        "code_walkthroughs": 1,
        "step_recaps": 2,
        "technical_details": 1,
        "code_execution_framing": 1,
    },
    "standard": {
        "explanations": 2,
        "code_walkthroughs": 2,
        "step_recaps": 2,
        "technical_details": 2,
        "code_execution_framing": 2,
    },
    "detailed": {
        "explanations": 3,
        "code_walkthroughs": 3,
        "step_recaps": 3,
        "technical_details": 3,
        "code_execution_framing": 3,
    },
}
"""Preset name -> per-category verbosity levels."""

NL_TERM_MAP: dict[str, str] = {
    # explanations
    "explanations": "explanations",
    "context": "explanations",
    "explain": "explanations",
    "why": "explanations",
    # code_walkthroughs
    "code detail": "code_walkthroughs",
    "code walkthrough": "code_walkthroughs",
    "code walkthroughs": "code_walkthroughs",
    "line by line": "code_walkthroughs",
    # step_recaps
    "recaps": "step_recaps",
    "summaries": "step_recaps",
    "recap": "step_recaps",
    "summary": "step_recaps",
    # technical_details
    "technical": "technical_details",
    "internals": "technical_details",
    "technical detail": "technical_details",
    "technical details": "technical_details",
    # code_execution_framing
    "before and after": "code_execution_framing",
    "execution framing": "code_execution_framing",
    "code framing": "code_execution_framing",
    "framing": "code_execution_framing",
}
"""Natural language term -> Output_Category name."""


# ---------------------------------------------------------------------------
# Pure functions (tasks 1.2 – 1.5)
# ---------------------------------------------------------------------------

def resolve_preset(preset_name: str) -> VerbosityPreferences:
    """Return VerbosityPreferences for a named preset.

    Args:
        preset_name: One of "concise", "standard", "detailed".

    Returns:
        VerbosityPreferences with the preset's per-category levels.

    Raises:
        ValueError: If preset_name is not a recognized preset.
    """
    if preset_name not in PRESETS:
        valid = ", ".join(sorted(PRESETS))
        raise ValueError(f"Unknown preset {preset_name!r}. Valid presets: {valid}")
    return VerbosityPreferences(preset=preset_name, categories=dict(PRESETS[preset_name]))


def detect_preset(categories: dict[str, int]) -> str:
    """Return the preset name matching the given category levels, or "custom".

    Args:
        categories: A dict of category_name -> level.

    Returns:
        "concise", "standard", "detailed", or "custom".
    """
    for name, levels in PRESETS.items():
        if categories == levels:
            return name
    return "custom"


def adjust_category(
    prefs: VerbosityPreferences, category: str, delta: int
) -> VerbosityPreferences:
    """Return new preferences with one category's level adjusted by delta.

    Clamps the result to [1, 3]. Sets preset to "custom" if the result
    no longer matches any named preset.

    Args:
        prefs: Current preferences.
        category: The category to adjust.
        delta: +1 for "more", -1 for "less".

    Returns:
        New VerbosityPreferences (original is not mutated).

    Raises:
        ValueError: If category is not a recognized category name.
    """
    if category not in CATEGORIES:
        valid = ", ".join(CATEGORIES)
        raise ValueError(
            f"Unknown category {category!r}. Valid categories: {valid}"
        )
    new_categories = dict(prefs.categories)
    new_categories[category] = max(1, min(3, new_categories[category] + delta))
    new_preset = detect_preset(new_categories)
    return VerbosityPreferences(preset=new_preset, categories=new_categories)


def match_nl_term(term: str) -> str | None:
    """Match a natural language term to an Output_Category name.

    Normalizes the input by lowercasing and stripping whitespace, then
    looks up the result in NL_TERM_MAP.

    Args:
        term: The user's term (e.g., "code detail", "recaps", "internals").

    Returns:
        The matching category name, or None if no match.
    """
    return NL_TERM_MAP.get(term.lower().strip())


def serialize_preferences(prefs: VerbosityPreferences) -> str:
    """Convert VerbosityPreferences to a YAML string fragment.

    Uses string formatting only (no PyYAML). Categories are output in
    the order defined by the CATEGORIES constant.

    Args:
        prefs: The verbosity preferences to serialize.

    Returns:
        A YAML string suitable for writing under the ``verbosity`` key.
        No trailing newline after the last line.
    """
    lines: list[str] = [f"preset: {prefs.preset}", "categories:"]
    for cat in CATEGORIES:
        lines.append(f"  {cat}: {prefs.categories[cat]}")
    return "\n".join(lines)


def deserialize_preferences(yaml_text: str) -> VerbosityPreferences:
    """Parse a YAML verbosity block into VerbosityPreferences.

    Uses minimal custom parsing (stdlib only, no PyYAML). Expects the
    format produced by :func:`serialize_preferences`.

    Args:
        yaml_text: The YAML text representing verbosity preferences.

    Returns:
        A VerbosityPreferences instance with the parsed values.

    Raises:
        ValueError: If the YAML structure is invalid (missing preset,
            missing categories, or non-integer levels).
    """
    preset: str | None = None
    categories: dict[str, int] = {}
    in_categories = False

    for raw_line in yaml_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue

        # Detect indented lines belonging to the categories block.
        is_indented = raw_line.startswith(" ")

        if is_indented and in_categories:
            if ":" not in stripped:
                raise ValueError(f"Invalid category line: {stripped!r}")
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            try:
                categories[key] = int(value)
            except ValueError:
                raise ValueError(
                    f"Non-integer level for category {key!r}: {value!r}"
                ) from None
        else:
            in_categories = False
            if ":" not in stripped:
                raise ValueError(f"Invalid line: {stripped!r}")
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if key == "preset":
                preset = value
            elif key == "categories":
                in_categories = True
            # Ignore unrecognized top-level keys for forward compatibility.

    if preset is None:
        raise ValueError("Missing 'preset' field in verbosity YAML")
    if not categories:
        raise ValueError("Missing 'categories' map in verbosity YAML")

    return VerbosityPreferences(preset=preset, categories=categories)


def validate_preferences(data: dict) -> list[str]:
    """Validate a verbosity preferences dict structure.

    Checks that the dict contains a valid ``preset`` field, a valid
    ``categories`` map with all five required categories, integer
    levels in range 1–3, and a recognized preset name.

    Args:
        data: The dict to validate (typically parsed from YAML).

    Returns:
        A list of error strings. Empty list means valid.
    """
    errors: list[str] = []

    # --- preset field ---
    if "preset" not in data:
        errors.append("Missing 'preset' field")
    else:
        preset = data["preset"]
        if not isinstance(preset, str):
            errors.append(
                f"'preset' must be a string, got {type(preset).__name__}"
            )
        elif preset not in ("concise", "standard", "detailed", "custom"):
            errors.append(
                f"'preset' must be one of concise, standard, detailed, custom; "
                f"got {preset!r}"
            )

    # --- categories field ---
    if "categories" not in data:
        errors.append("Missing 'categories' field")
    else:
        categories = data["categories"]
        if not isinstance(categories, dict):
            errors.append(
                f"'categories' must be a dict, got {type(categories).__name__}"
            )
        else:
            for cat in CATEGORIES:
                if cat not in categories:
                    errors.append(f"Missing category '{cat}'")

            for cat, level in categories.items():
                if cat not in CATEGORIES:
                    continue
                if not isinstance(level, int):
                    errors.append(
                        f"Category '{cat}' level must be an int, "
                        f"got {type(level).__name__}"
                    )
                elif level < 1 or level > 3:
                    errors.append(
                        f"Category '{cat}' level must be 1-3, got {level}"
                    )

    return errors
