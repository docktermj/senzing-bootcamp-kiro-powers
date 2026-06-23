#!/usr/bin/env python3
"""Senzing Bootcamp — Entry Point Assessment.

Determines where a bootcamper should begin (or resume) the Senzing Bootcamp
by reading the module-artifacts manifest, scanning the filesystem for produced
artifacts, checking Senzing SDK importability, and outputting a per-module
checklist with a recommended entry point.

Usage:
    python scripts/assess_entry_point.py
    python scripts/assess_entry_point.py --project-dir /path/to/project
    python scripts/assess_entry_point.py --manifest /path/to/module-artifacts.yaml

Cross-platform: Linux, macOS, Windows.  Stdlib only — no third-party deps.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class Artifact:
    """A single artifact expected by a module."""

    path: str
    type: str  # "file" or "directory"
    description: str
    required: bool


@dataclass
class ModuleManifest:
    """Parsed representation of a single module's manifest entry."""

    number: int
    produces: list[Artifact] = field(default_factory=list)
    requires_from: dict[int, list[str]] = field(default_factory=dict)


@dataclass
class ArtifactStatus:
    """Result of checking a single artifact's presence."""

    artifact: Artifact
    present: bool


@dataclass
class ModuleStatus:
    """Completeness state of a single module."""

    number: int
    complete: bool
    artifact_statuses: list[ArtifactStatus] = field(default_factory=list)


@dataclass
class SdkStatus:
    """Result of the SDK importability check."""

    available: bool | None  # None = unknown (no Python found)
    version: str | None = None
    note: str | None = None


@dataclass
class Recommendation:
    """The final entry point recommendation."""

    module_number: int | None  # None means graduation
    module_name: str = ""
    reason: str = ""


@dataclass
class AssessmentReport:
    """Complete assessment result."""

    module_statuses: list[ModuleStatus] = field(default_factory=list)
    sdk_status: SdkStatus = field(default_factory=lambda: SdkStatus(available=None))
    recommendation: Recommendation = field(
        default_factory=lambda: Recommendation(module_number=None)
    )


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _normalize_path(manifest_path: str) -> Path:
    """Convert a manifest path (always forward-slash) to a platform Path.

    Handles both 'data/raw/' and 'data\\raw\\' by normalizing through
    PurePosixPath then converting to native Path.

    Args:
        manifest_path: Path string from the manifest file.

    Returns:
        Platform-native Path object.
    """
    # Normalize backslashes to forward slashes, strip trailing slashes
    cleaned = manifest_path.replace("\\", "/").rstrip("/")
    return Path(PurePosixPath(cleaned))


def _is_dir_present(path: Path) -> bool:
    """Check whether a directory exists and is non-empty.

    Args:
        path: Path to the directory to check.

    Returns:
        True if the directory exists and contains at least one entry.
    """
    try:
        return path.is_dir() and any(path.iterdir())
    except (PermissionError, OSError):
        return False


def _is_file_present(path: Path) -> bool:
    """Check whether a file exists and has size greater than zero.

    Args:
        path: Path to the file to check.

    Returns:
        True if the file exists and has a non-zero size.
    """
    try:
        return path.is_file() and path.stat().st_size > 0
    except (PermissionError, OSError):
        return False


def _find_python() -> str | None:
    """Locate a Python interpreter on the system PATH.

    Tries 'python3' first, then falls back to 'python'.

    Returns:
        Absolute path to the Python interpreter, or None if not found.
    """
    return shutil.which("python3") or shutil.which("python")


# ---------------------------------------------------------------------------
# Manifest Parser
# ---------------------------------------------------------------------------


def _parse_bool(value: str) -> bool:
    """Parse a boolean string value from YAML.

    Args:
        value: String representation of a boolean (true/false/True/False).

    Returns:
        The boolean value.

    Raises:
        ValueError: If the value is not a recognized boolean string.
    """
    lower = value.strip().lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def _strip_quotes(value: str) -> str:
    """Remove surrounding quotes from a YAML string value.

    Args:
        value: A string that may be wrapped in single or double quotes.

    Returns:
        The string with surrounding quotes removed.
    """
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in ('"', "'"):
        return stripped[1:-1]
    return stripped


def _parse_inline_list(value: str) -> list[str]:
    """Parse a YAML inline list like '["a", "b"]' or '[]'.

    Args:
        value: String representation of an inline list.

    Returns:
        List of string items.

    Raises:
        ValueError: If the value is not a valid inline list.
    """
    stripped = value.strip()
    if not (stripped.startswith("[") and stripped.endswith("]")):
        raise ValueError(f"Expected inline list, got: {value!r}")
    inner = stripped[1:-1].strip()
    if not inner:
        return []
    items = []
    for item in inner.split(","):
        items.append(_strip_quotes(item.strip()))
    return items


def _indent_level(line: str) -> int:
    """Count leading spaces on a line.

    Args:
        line: A text line.

    Returns:
        Number of leading space characters.
    """
    return len(line) - len(line.lstrip(" "))


def parse_manifest(text: str) -> list[ModuleManifest]:
    """Parse module-artifacts.yaml content into structured data.

    Args:
        text: Raw YAML text content of the manifest file.

    Returns:
        List of ModuleManifest entries in module-number order.

    Raises:
        ValueError: If the YAML structure is malformed or missing required fields.
    """
    lines = text.splitlines()
    modules: dict[int, ModuleManifest] = {}

    # State tracking
    in_modules = False
    current_module: int | None = None
    in_produces = False
    in_requires_from = False
    current_artifact: dict[str, str] | None = None
    current_req_module: int | None = None
    modules_indent: int | None = None
    module_key_indent: int | None = None

    for line_num, raw_line in enumerate(lines, start=1):
        # Skip empty lines and comments
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue

        indent = _indent_level(raw_line)
        content = raw_line.strip()

        # Top-level keys
        if indent == 0:
            # Flush any pending artifact
            if current_artifact is not None:
                _flush_artifact(current_artifact, modules, current_module, line_num)
                current_artifact = None

            if content == "modules:":
                in_modules = True
                in_produces = False
                in_requires_from = False
                current_module = None
                modules_indent = None
                module_key_indent = None
            else:
                # Other top-level keys (e.g., version:) — skip
                in_modules = False
                in_produces = False
                in_requires_from = False
                current_module = None
            continue

        if not in_modules:
            continue

        # Module number keys (e.g., "  4:")
        if content.endswith(":") and content[:-1].strip().isdigit():
            # Check this is at the right indent level for a module key
            if modules_indent is None:
                modules_indent = indent
            if module_key_indent is None:
                module_key_indent = indent

            if indent == module_key_indent:
                # Flush any pending artifact from previous module
                if current_artifact is not None:
                    _flush_artifact(current_artifact, modules, current_module, line_num)
                    current_artifact = None

                module_num = int(content[:-1].strip())
                current_module = module_num
                if module_num not in modules:
                    modules[module_num] = ModuleManifest(number=module_num)
                in_produces = False
                in_requires_from = False
                current_req_module = None
                continue

        if current_module is None:
            continue

        # produces: key
        if content == "produces:":
            # Flush any pending artifact
            if current_artifact is not None:
                _flush_artifact(current_artifact, modules, current_module, line_num)
                current_artifact = None
            in_produces = True
            in_requires_from = False
            current_req_module = None
            continue

        # requires_from: key (with possible inline value)
        if content.startswith("requires_from:"):
            # Flush any pending artifact
            if current_artifact is not None:
                _flush_artifact(current_artifact, modules, current_module, line_num)
                current_artifact = None
            in_produces = False
            in_requires_from = True
            current_req_module = None
            # Check for inline empty mapping: requires_from: {}
            after = content[len("requires_from:"):].strip()
            if after == "{}":
                in_requires_from = False
            continue

        # Inside produces section
        if in_produces:
            if content.startswith("- "):
                # Flush previous artifact if any
                if current_artifact is not None:
                    _flush_artifact(current_artifact, modules, current_module, line_num)

                # Start new artifact — parse the first field on the same line
                current_artifact = {}
                field_part = content[2:].strip()  # Remove "- "
                if ":" in field_part:
                    key, _, val = field_part.partition(":")
                    current_artifact[key.strip()] = _strip_quotes(val.strip())
            elif current_artifact is not None and ":" in content:
                # Continuation field of current artifact
                key, _, val = content.partition(":")
                current_artifact[key.strip()] = _strip_quotes(val.strip())
            continue

        # Inside requires_from section
        if in_requires_from:
            # Check for module number key with inline list: "2: [...]"
            if ":" in content:
                key_part, _, val_part = content.partition(":")
                key_str = key_part.strip()
                val_str = val_part.strip()

                if key_str.isdigit():
                    current_req_module = int(key_str)
                    manifest = modules[current_module]
                    if current_req_module not in manifest.requires_from:
                        manifest.requires_from[current_req_module] = []

                    # Check for inline list
                    if val_str.startswith("["):
                        paths = _parse_inline_list(val_str)
                        manifest.requires_from[current_req_module].extend(paths)
                        current_req_module = None
                    continue

            # Sequence items under a requires_from module key
            if content.startswith("- ") and current_req_module is not None:
                path_val = _strip_quotes(content[2:].strip())
                modules[current_module].requires_from[current_req_module].append(path_val)
                continue

    # Flush final pending artifact
    if current_artifact is not None:
        _flush_artifact(current_artifact, modules, current_module, len(lines) + 1)

    if not modules:
        raise ValueError("No modules found in manifest")

    # Return sorted by module number
    return sorted(modules.values(), key=lambda m: m.number)


def _flush_artifact(
    artifact_dict: dict[str, str],
    modules: dict[int, ModuleManifest],
    current_module: int | None,
    line_num: int,
) -> None:
    """Validate and add a parsed artifact to its module.

    Args:
        artifact_dict: Dictionary of artifact fields parsed so far.
        modules: The modules dictionary being built.
        current_module: The current module number.
        line_num: Current line number for error reporting.

    Raises:
        ValueError: If required artifact fields are missing.
    """
    if current_module is None:
        raise ValueError(f"Line {line_num}: artifact found outside of a module")

    if "path" not in artifact_dict:
        raise ValueError(
            f"Line {line_num}: artifact in module {current_module} missing 'path' field"
        )
    if "type" not in artifact_dict:
        raise ValueError(
            f"Line {line_num}: artifact in module {current_module} missing 'type' field"
        )

    artifact = Artifact(
        path=artifact_dict["path"],
        type=artifact_dict["type"],
        description=artifact_dict.get("description", ""),
        required=_parse_bool(artifact_dict.get("required", "true")),
    )
    modules[current_module].produces.append(artifact)


# ---------------------------------------------------------------------------
# Artifact Scanner
# ---------------------------------------------------------------------------


def scan_artifacts(
    artifacts: list[Artifact],
    project_dir: Path,
) -> list[ArtifactStatus]:
    """Check each artifact's presence in the project directory.

    Args:
        artifacts: List of artifacts to check.
        project_dir: Root directory to resolve artifact paths against.

    Returns:
        List of ArtifactStatus results, one per input artifact.
    """
    results: list[ArtifactStatus] = []
    for artifact in artifacts:
        resolved = project_dir / _normalize_path(artifact.path)
        try:
            if artifact.type == "directory":
                present = _is_dir_present(resolved)
            else:
                present = _is_file_present(resolved)
        except PermissionError:
            present = False
        results.append(ArtifactStatus(artifact=artifact, present=present))
    return results


# ---------------------------------------------------------------------------
# SDK Checker
# ---------------------------------------------------------------------------


def check_sdk() -> SdkStatus:
    """Check whether the Senzing Python SDK is importable.

    Uses shutil.which to find a Python interpreter, then runs a subprocess
    that attempts `import senzing` with a 15-second timeout.

    Returns:
        SdkStatus with availability, version, and optional diagnostic note.
    """
    python = _find_python()
    if python is None:
        return SdkStatus(
            available=None,
            version=None,
            note="No Python interpreter found on PATH",
        )

    try:
        result = subprocess.run(
            [python, "-c", "import senzing; print(senzing.__version__)"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return SdkStatus(
            available=False,
            version=None,
            note="SDK import check timed out after 15 seconds",
        )

    if result.returncode == 0:
        return SdkStatus(
            available=True,
            version=result.stdout.strip(),
            note=None,
        )

    return SdkStatus(available=False, version=None, note=None)


# ---------------------------------------------------------------------------
# Completeness Logic
# ---------------------------------------------------------------------------


def determine_completeness(
    manifest: ModuleManifest,
    artifact_statuses: list[ArtifactStatus],
) -> ModuleStatus:
    """Determine whether a module is complete based on required artifact presence.

    A module is complete if and only if ALL artifacts with required=True are present.
    Artifacts with required=False are reported but do not affect completeness.

    Args:
        manifest: The module's manifest entry.
        artifact_statuses: Scan results for the module's artifacts.

    Returns:
        ModuleStatus with completeness determination.
    """
    required_statuses = [s for s in artifact_statuses if s.artifact.required]
    complete = all(s.present for s in required_statuses)
    return ModuleStatus(
        number=manifest.number,
        complete=complete,
        artifact_statuses=artifact_statuses,
    )


# ---------------------------------------------------------------------------
# Recommendation Engine
# ---------------------------------------------------------------------------

# Standard module names used in recommendations.
_MODULE_NAMES: dict[int, str] = {
    1: "Business Problem",
    2: "SDK Setup",
    3: "System Verification",
    4: "Data Collection",
    5: "Data Quality & Mapping",
    6: "Data Processing",
    7: "Query, Visualize, and Discover",
    8: "Performance Testing & Benchmarking",
    9: "Security Hardening",
    10: "Monitoring & Observability",
    11: "Package & Deploy",
}


def recommend_entry_point(
    module_statuses: list[ModuleStatus],
    sdk_status: SdkStatus,
) -> Recommendation:
    """Determine the recommended entry point module.

    Logic:
    1. If SDK is unavailable and module 2 is incomplete → recommend module 2
    2. Otherwise, recommend the first incomplete module in ascending order
    3. If all modules are complete → recommend graduation

    Args:
        module_statuses: Completeness states for modules 4-11.
        sdk_status: Result of the SDK importability check.

    Returns:
        Recommendation with module number, name, and reason.
    """
    # Build a lookup by module number for quick access
    status_by_number = {ms.number: ms for ms in module_statuses}

    # Rule 1: If SDK is unavailable and module 2 is incomplete, recommend module 2
    if sdk_status.available is False:
        mod2 = status_by_number.get(2)
        if mod2 is not None and not mod2.complete:
            return Recommendation(
                module_number=2,
                module_name=_MODULE_NAMES.get(2, "Module 2"),
                reason="Senzing SDK is not available; complete SDK Setup first",
            )

    # Rule 2: Recommend the first incomplete module in ascending order
    for ms in sorted(module_statuses, key=lambda s: s.number):
        if not ms.complete:
            return Recommendation(
                module_number=ms.number,
                module_name=_MODULE_NAMES.get(ms.number, f"Module {ms.number}"),
                reason="First incomplete module in sequence",
            )

    # Rule 3: All modules are complete → graduation
    return Recommendation(
        module_number=None,
        module_name="Graduation",
        reason="All modules complete",
    )


# ---------------------------------------------------------------------------
# Output Formatter
# ---------------------------------------------------------------------------


def format_report(report: AssessmentReport) -> str:
    """Format the assessment report as a human-readable checklist.

    Output structure:
    - Per-module section with artifact checklist (path, type, required, status)
    - SDK check result (availability + version)
    - Summary recommendation line

    Args:
        report: The complete assessment result.

    Returns:
        Formatted string for terminal output.
    """
    lines: list[str] = []

    # Per-module sections
    for module_status in report.module_statuses:
        module_num = module_status.number
        module_name = _MODULE_NAMES.get(module_num, f"Module {module_num}")
        lines.append(f"=== Module {module_num}: {module_name} ===")

        for artifact_status in module_status.artifact_statuses:
            artifact = artifact_status.artifact
            marker = "\u2713" if artifact_status.present else "\u2717"
            required_label = "required" if artifact.required else "optional"
            lines.append(
                f"  [{marker}] {artifact.path}"
                f"  ({artifact.type}, {required_label})"
            )

        status_label = "COMPLETE" if module_status.complete else "INCOMPLETE"
        lines.append(f"  Status: {status_label}")
        lines.append("")

    # SDK check section
    lines.append("=== SDK Check ===")
    if report.sdk_status.available is None:
        lines.append("  Available: Unknown")
    elif report.sdk_status.available:
        lines.append("  Available: Yes")
    else:
        lines.append("  Available: No")

    if report.sdk_status.version:
        lines.append(f"  Version: {report.sdk_status.version}")

    if report.sdk_status.note:
        lines.append(f"  Note: {report.sdk_status.note}")

    lines.append("")

    # Recommendation section
    lines.append("=== Recommendation ===")
    if report.recommendation.module_number is not None:
        lines.append(
            f"  Start at Module {report.recommendation.module_number}:"
            f" {report.recommendation.module_name}"
        )
    else:
        lines.append(f"  {report.recommendation.module_name}")

    if report.recommendation.reason:
        lines.append(f"  Reason: {report.recommendation.reason}")

    return "\n".join(lines)



# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Entry point for the assess_entry_point script.

    Args:
        argv: Optional argument list (defaults to sys.argv[1:]).

    CLI options:
        --project-dir PATH  Project directory to scan (default: cwd)
        --manifest PATH     Path to module-artifacts.yaml
                           (default: config/module-artifacts.yaml relative to script dir)

    Exit codes:
        0: Assessment completed successfully
        1: Unrecoverable error (missing manifest, unreadable file)
    """
    # Default manifest path: config/module-artifacts.yaml relative to the power root
    # (script lives in senzing-bootcamp/scripts/, power root is senzing-bootcamp/)
    script_dir = Path(__file__).resolve().parent.parent
    default_manifest = str(script_dir / "config" / "module-artifacts.yaml")

    parser = argparse.ArgumentParser(
        description="Assess bootcamp entry point based on module artifact presence.",
    )
    parser.add_argument(
        "--project-dir",
        default=os.getcwd(),
        help="Project directory to scan (default: current working directory)",
    )
    parser.add_argument(
        "--manifest",
        default=default_manifest,
        help="Path to module-artifacts.yaml (default: config/module-artifacts.yaml)",
    )

    args = parser.parse_args(argv)
    project_dir = Path(args.project_dir)
    manifest_path = Path(args.manifest)

    # Read manifest file
    if not manifest_path.exists():
        print(f"Error: manifest file not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    try:
        text = manifest_path.read_text(encoding="utf-8")
    except (PermissionError, OSError) as exc:
        print(f"Error: cannot read manifest file: {manifest_path}: {exc}", file=sys.stderr)
        sys.exit(1)

    # Parse manifest
    try:
        modules = parse_manifest(text)
    except ValueError as exc:
        print(f"Error: malformed manifest: {exc}", file=sys.stderr)
        sys.exit(1)

    # Scan artifacts per module and determine completeness
    module_statuses: list[ModuleStatus] = []
    for module in modules:
        artifact_statuses = scan_artifacts(module.produces, project_dir)
        status = determine_completeness(module, artifact_statuses)
        module_statuses.append(status)

    # Check SDK availability
    sdk_status = check_sdk()

    # Determine recommendation
    recommendation = recommend_entry_point(module_statuses, sdk_status)

    # Build report, format, and print
    report = AssessmentReport(
        module_statuses=module_statuses,
        sdk_status=sdk_status,
        recommendation=recommendation,
    )
    output = format_report(report)
    print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
