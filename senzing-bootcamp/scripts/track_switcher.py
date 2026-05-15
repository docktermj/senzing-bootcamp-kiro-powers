#!/usr/bin/env python3
"""Senzing Bootcamp - Track Switcher.

Computes the effect of switching from one bootcamp track to another,
given the current progress state. Can also apply the switch by updating
config/bootcamp_progress.json.

Usage:
    # Dry-run (default): compute and print switch effect as JSON
    python3 scripts/track_switcher.py --from core_bootcamp --to advanced_topics \\
        --progress config/bootcamp_progress.json

    # Apply: compute and write to progress file
    python3 scripts/track_switcher.py --from core_bootcamp --to advanced_topics \\
        --progress config/bootcamp_progress.json --apply
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# YAML Parsing (minimal, stdlib only)
# ---------------------------------------------------------------------------


def load_track_definitions(yaml_path: Path) -> dict[str, list[int]]:
    """Load track definitions from module-dependencies.yaml.

    Parses the 'tracks' section and returns a mapping of track name
    to ordered list of module numbers.

    Args:
        yaml_path: Path to module-dependencies.yaml.

    Returns:
        Dict mapping track name (e.g., 'core_bootcamp') to list of module numbers.

    Raises:
        FileNotFoundError: If yaml_path does not exist.
        ValueError: If the YAML structure is invalid or tracks section is missing.
    """
    if not yaml_path.exists():
        raise FileNotFoundError(f"Module dependencies file not found: {yaml_path}")

    content = yaml_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    tracks: dict[str, list[int]] = {}
    in_tracks_section = False
    current_track: str | None = None

    for line in lines:
        stripped = line.rstrip()

        # Detect top-level 'tracks:' section
        if stripped == "tracks:":
            in_tracks_section = True
            continue

        # Exit tracks section when another top-level key appears
        if in_tracks_section and stripped and not stripped[0].isspace() and stripped.endswith(":"):
            in_tracks_section = False
            continue

        if not in_tracks_section:
            continue

        # Detect track name (2-space indent, ends with colon)
        track_match = re.match(r"^  (\w+):$", stripped)
        if track_match:
            current_track = track_match.group(1)
            continue

        # Detect modules line within a track (4-space indent)
        modules_match = re.match(r"^    modules:\s*\[(.+)\]", stripped)
        if modules_match and current_track is not None:
            modules_str = modules_match.group(1)
            module_numbers = [int(x.strip()) for x in modules_str.split(",")]
            tracks[current_track] = module_numbers
            continue

    if not tracks:
        raise ValueError(
            f"No tracks found in {yaml_path}. Expected a 'tracks' section with module lists."
        )

    return tracks


def load_module_names(yaml_path: Path) -> dict[int, str]:
    """Load module number-to-name mapping from module-dependencies.yaml.

    Parses the 'modules' section and returns a mapping of module number
    to module name.

    Args:
        yaml_path: Path to module-dependencies.yaml.

    Returns:
        Dict mapping module number to module name (e.g., {1: "Business Problem"}).

    Raises:
        FileNotFoundError: If yaml_path does not exist.
        ValueError: If the YAML structure is invalid or modules section is missing.
    """
    if not yaml_path.exists():
        raise FileNotFoundError(f"Module dependencies file not found: {yaml_path}")

    content = yaml_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    module_names: dict[int, str] = {}
    in_modules_section = False
    current_module: int | None = None

    for line in lines:
        stripped = line.rstrip()

        # Detect top-level 'modules:' section
        if stripped == "modules:":
            in_modules_section = True
            continue

        # Exit modules section when another top-level key appears
        if in_modules_section and stripped and not stripped[0].isspace() and stripped.endswith(":"):
            in_modules_section = False
            continue

        if not in_modules_section:
            continue

        # Detect module number (2-space indent, number followed by colon)
        module_num_match = re.match(r"^  (\d+):$", stripped)
        if module_num_match:
            current_module = int(module_num_match.group(1))
            continue

        # Detect name line within a module (4-space indent)
        name_match = re.match(r'^    name:\s*"(.+)"', stripped)
        if name_match and current_module is not None:
            module_names[current_module] = name_match.group(1)
            continue

    if not module_names:
        raise ValueError(
            f"No modules found in {yaml_path}. Expected a 'modules' section with name fields."
        )

    return module_names


# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------


@dataclass
class SwitchResult:
    """Result of computing a track switch effect."""

    current_track: str
    target_track: str
    is_noop: bool
    remaining_modules: list[int]
    remaining_module_names: dict[int, str]
    extra_modules: list[int]
    extra_module_names: dict[int, str]
    modules_completed: list[int]


# ---------------------------------------------------------------------------
# Core Computation
# ---------------------------------------------------------------------------


def compute_switch(
    current_track: str,
    target_track: str,
    modules_completed: list[int],
    track_definitions: dict[str, list[int]],
    module_names: dict[int, str],
) -> SwitchResult:
    """Compute the effect of switching from current_track to target_track.

    Pure function — no side effects.

    Args:
        current_track: The bootcamper's current track name.
        target_track: The desired target track name.
        modules_completed: List of module numbers already completed.
        track_definitions: Track name → ordered module list mapping.
        module_names: Module number → name mapping.

    Returns:
        SwitchResult with computed remaining/extra modules.

    Raises:
        ValueError: If target_track or current_track is not a valid track name.
    """
    valid_tracks = sorted(track_definitions.keys())

    if current_track not in track_definitions:
        raise ValueError(
            f"Invalid track name: '{current_track}'. "
            f"Valid tracks: {', '.join(valid_tracks)}"
        )

    if target_track not in track_definitions:
        raise ValueError(
            f"Invalid track name: '{target_track}'. "
            f"Valid tracks: {', '.join(valid_tracks)}"
        )

    target_modules = track_definitions[target_track]
    completed_set = set(modules_completed)
    target_set = set(target_modules)

    # No-op detection
    is_noop = current_track == target_track

    # Remaining modules: in target track, not yet completed, preserving target ordering
    remaining_modules = [m for m in target_modules if m not in completed_set]
    remaining_module_names = {m: module_names.get(m, f"Module {m}") for m in remaining_modules}

    # Extra modules: completed modules NOT in the target track
    extra_modules = [m for m in modules_completed if m not in target_set]
    extra_module_names = {m: module_names.get(m, f"Module {m}") for m in extra_modules}

    return SwitchResult(
        current_track=current_track,
        target_track=target_track,
        is_noop=is_noop,
        remaining_modules=remaining_modules,
        remaining_module_names=remaining_module_names,
        extra_modules=extra_modules,
        extra_module_names=extra_module_names,
        modules_completed=modules_completed,
    )


# ---------------------------------------------------------------------------
# Progress File Update
# ---------------------------------------------------------------------------


def apply_switch(progress_path: Path, switch_result: SwitchResult) -> None:
    """Apply a track switch by updating the progress file atomically.

    Reads the current progress file, updates track, current_module,
    current_step, and last_activity fields, then writes atomically
    via temp file + os.replace.

    Args:
        progress_path: Path to bootcamp_progress.json.
        switch_result: The computed switch result to apply.

    Raises:
        OSError: If the atomic write fails (original file is not modified).
    """
    data = json.loads(progress_path.read_text(encoding="utf-8"))

    data["track"] = switch_result.target_track
    data["current_module"] = (
        switch_result.remaining_modules[0] if switch_result.remaining_modules else None
    )
    data["current_step"] = None
    data["last_activity"] = datetime.now(timezone.utc).isoformat()

    # Atomic write: write to temp file then rename
    dir_path = progress_path.parent
    fd = None
    tmp_path = None
    try:
        fd = tempfile.NamedTemporaryFile(
            mode="w",
            dir=dir_path,
            suffix=".tmp",
            delete=False,
            encoding="utf-8",
        )
        tmp_path = fd.name
        fd.write(json.dumps(data, indent=2) + "\n")
        fd.close()
        fd = None
        os.replace(tmp_path, progress_path)
    except BaseException:
        if fd is not None:
            fd.close()
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for track switching.

    Flags:
        --from: Current track name.
        --to: Target track name.
        --progress: Path to bootcamp_progress.json.
        --apply: Actually write the switch (default is dry-run).
        --yaml: Override path to module-dependencies.yaml.
    """
    parser = argparse.ArgumentParser(
        description="Compute or apply a bootcamp track switch."
    )
    parser.add_argument(
        "--from",
        dest="from_track",
        required=True,
        help="Current track name",
    )
    parser.add_argument(
        "--to",
        dest="to_track",
        required=True,
        help="Target track name",
    )
    parser.add_argument(
        "--progress",
        required=True,
        help="Path to bootcamp_progress.json",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Actually write the switch (default is dry-run)",
    )
    parser.add_argument(
        "--yaml",
        default=None,
        help="Override path to module-dependencies.yaml",
    )

    args = parser.parse_args(argv)

    # Resolve YAML path
    if args.yaml:
        yaml_path = Path(args.yaml)
    else:
        yaml_path = Path(__file__).resolve().parent.parent / "config" / "module-dependencies.yaml"

    # Load YAML
    try:
        track_definitions = load_track_definitions(yaml_path)
        module_names = load_module_names(yaml_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Load progress
    progress_path = Path(args.progress)
    modules_completed: list[int] = []

    if progress_path.exists():
        try:
            progress_data = json.loads(progress_path.read_text(encoding="utf-8"))
            modules_completed = progress_data.get("modules_completed", [])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"ERROR: Cannot parse progress file: {progress_path}", file=sys.stderr)
            sys.exit(1)
    elif args.apply:
        print(f"ERROR: Progress file not found: {progress_path}", file=sys.stderr)
        sys.exit(1)

    # Compute switch
    try:
        result = compute_switch(
            current_track=args.from_track,
            target_track=args.to_track,
            modules_completed=modules_completed,
            track_definitions=track_definitions,
            module_names=module_names,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    # Output or apply
    if args.apply:
        try:
            apply_switch(progress_path, result)
        except OSError as e:
            print(f"ERROR: Failed to write progress file: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Track switched from '{result.current_track}' to '{result.target_track}'.")
    else:
        # Dry-run: print JSON with string keys for JSON compatibility
        output = {
            "current_track": result.current_track,
            "target_track": result.target_track,
            "is_noop": result.is_noop,
            "remaining_modules": result.remaining_modules,
            "remaining_module_names": {
                str(k): v for k, v in result.remaining_module_names.items()
            },
            "extra_modules": result.extra_modules,
            "extra_module_names": {
                str(k): v for k, v in result.extra_module_names.items()
            },
            "modules_completed": result.modules_completed,
        }
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
