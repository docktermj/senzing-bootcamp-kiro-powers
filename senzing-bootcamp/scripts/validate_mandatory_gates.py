#!/usr/bin/env python3
"""Validate mandatory gate checkpoints in bootcamp progress.

Parses steering files for ⛔ mandatory gate markers, cross-references against
config/bootcamp_progress.json checkpoint entries, and reports any mandatory gate
steps that were skipped without a corresponding checkpoint or skipped_steps entry.

Usage:
    python senzing-bootcamp/scripts/validate_mandatory_gates.py
    python senzing-bootcamp/scripts/validate_mandatory_gates.py --progress path/to/progress.json
    python senzing-bootcamp/scripts/validate_mandatory_gates.py --steering path/to/steering/

Exit codes:
    0 — All mandatory gate checkpoints satisfied (or no progress to validate)
    1 — Violation detected: mandatory gate step skipped without checkpoint

Examples:
    # Validate using default paths (relative to script location)
    python senzing-bootcamp/scripts/validate_mandatory_gates.py

    # Validate a specific progress file
    python senzing-bootcamp/scripts/validate_mandatory_gates.py \\
        --progress senzing-bootcamp/config/bootcamp_progress.json

    # Validate with explicit steering directory
    python senzing-bootcamp/scripts/validate_mandatory_gates.py \\
        --steering senzing-bootcamp/steering/
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Register module in sys.modules for dataclass annotation resolution.
# Required when imported via importlib.util without prior sys.modules registration.
if __name__ not in sys.modules:
    import types as _types

    _mod = _types.ModuleType(__name__)
    _mod.__dict__.update(globals())
    sys.modules[__name__] = _mod

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class MandatoryGate:
    """A mandatory gate step parsed from a steering file.

    Attributes:
        module: The module number (e.g., 3).
        step: The step number within the module (e.g., 9).
        source_file: Path to the steering file containing the gate.
        required_checkpoints: List of checkpoint keys that must be present.
    """

    module: int
    step: int
    source_file: str
    required_checkpoints: list[str] = field(default_factory=list)


@dataclass
class Violation:
    """A mandatory gate violation detected during validation.

    Attributes:
        gate: The mandatory gate that was violated.
        current_step: The current step in progress (past the gate).
        missing_checkpoints: Checkpoint keys that are missing.
        message: Human-readable description of the violation.
    """

    gate: MandatoryGate
    current_step: int
    missing_checkpoints: list[str]
    message: str


@dataclass
class ValidationResult:
    """Result of validating mandatory gates against progress.

    Attributes:
        violations: List of violations found.
        gates_checked: Number of mandatory gates checked.
        passed: Whether validation passed (no violations).
    """

    violations: list[Violation] = field(default_factory=list)
    gates_checked: int = 0
    passed: bool = True


# ---------------------------------------------------------------------------
# Mandatory gate definitions
# ---------------------------------------------------------------------------

# Module 3 Step 9 requires these checkpoints to be present with "passed" status
_MODULE3_STEP9_CHECKPOINTS = ["web_service", "web_page"]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_mandatory_gates(steering_dir: Path) -> list[MandatoryGate]:
    """Parse steering files for ⛔ mandatory gate markers.

    Scans markdown files in the steering directory for step headings that
    contain the ⛔ MANDATORY GATE designation.

    Args:
        steering_dir: Path to the steering directory.

    Returns:
        List of MandatoryGate instances found in steering files.
    """
    gates: list[MandatoryGate] = []

    if not steering_dir.is_dir():
        return gates

    for md_file in sorted(steering_dir.glob("module-*.md")):
        content = md_file.read_text(encoding="utf-8")
        gates.extend(_parse_gates_from_file(content, md_file))

    return gates


def _parse_gates_from_file(content: str, file_path: Path) -> list[MandatoryGate]:
    """Parse mandatory gates from a single steering file.

    Args:
        content: The full text content of the steering file.
        file_path: Path to the file (for reporting).

    Returns:
        List of MandatoryGate instances found in this file.
    """
    gates: list[MandatoryGate] = []

    # Extract module number from filename (e.g., module-03-... → 3)
    module_match = re.search(r"module-(\d+)", file_path.name)
    if not module_match:
        return gates
    module_num = int(module_match.group(1))

    # Find all step sections and check for ⛔ markers
    step_pattern = re.compile(r"^###\s+Step\s+(\d+):", re.MULTILINE)
    step_matches = list(step_pattern.finditer(content))

    for i, match in enumerate(step_matches):
        step_num = int(match.group(1))
        start = match.start()

        # Find end of this step section
        if i + 1 < len(step_matches):
            end = step_matches[i + 1].start()
        else:
            # Find next phase heading or end of file
            next_phase = re.search(r"^##\s+Phase", content[start + 1:], re.MULTILINE)
            end = (start + 1 + next_phase.start()) if next_phase else len(content)

        section = content[start:end]

        # Check for ⛔ MANDATORY GATE pattern
        if re.search(r"⛔\s*MANDATORY\s*GATE", section):
            gate = MandatoryGate(
                module=module_num,
                step=step_num,
                source_file=str(file_path.name),
                required_checkpoints=_get_required_checkpoints(module_num, step_num),
            )
            gates.append(gate)

    return gates


def _get_required_checkpoints(module: int, step: int) -> list[str]:
    """Get the required checkpoint keys for a mandatory gate step.

    Args:
        module: The module number.
        step: The step number.

    Returns:
        List of checkpoint keys that must have "passed" status.
    """
    if module == 3 and step == 9:
        return _MODULE3_STEP9_CHECKPOINTS[:]
    return []


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_progress(
    progress: dict,
    gates: list[MandatoryGate],
) -> ValidationResult:
    """Validate progress against mandatory gates.

    For each mandatory gate, checks whether current_step has advanced past it.
    If so, verifies that the corresponding checkpoints exist with "passed" status
    OR that a skipped_steps entry exists for that gate step.

    Args:
        progress: The parsed bootcamp_progress.json content.
        gates: List of mandatory gates to check.

    Returns:
        ValidationResult with any violations found.
    """
    result = ValidationResult()

    for gate in gates:
        result.gates_checked += 1
        violation = _check_gate(progress, gate)
        if violation:
            result.violations.append(violation)
            result.passed = False

    return result


def _check_gate(progress: dict, gate: MandatoryGate) -> Violation | None:
    """Check a single mandatory gate against progress state.

    Args:
        progress: The parsed bootcamp_progress.json content.
        gate: The mandatory gate to check.

    Returns:
        A Violation if the gate was violated, None otherwise.
    """
    current_module = progress.get("current_module")
    current_step = progress.get("current_step")

    # If not in the same module, no violation possible from this gate
    if current_module != gate.module:
        # If the module is completed (in modules_completed), check if gate was satisfied
        modules_completed = progress.get("modules_completed", [])
        if gate.module not in modules_completed:
            return None
        # Module is completed — check checkpoints were recorded
    elif current_step is None or current_step <= gate.step:
        # Haven't passed the gate yet — no violation
        return None

    # Check if skipped_steps entry exists (bootcamper-initiated skip)
    skipped_steps = progress.get("skipped_steps", {})
    skip_key = f"{gate.module}.{gate.step}"
    if skip_key in skipped_steps:
        return None

    # Check if required checkpoints exist with "passed" status
    verification_key = f"module_{gate.module}_verification"
    verification = progress.get(verification_key, {})
    checks = verification.get("checks", {})

    missing_checkpoints: list[str] = []
    for checkpoint_key in gate.required_checkpoints:
        checkpoint = checks.get(checkpoint_key, {})
        if checkpoint.get("status") != "passed":
            missing_checkpoints.append(checkpoint_key)

    if not missing_checkpoints:
        return None

    # Violation: past the gate without checkpoints or skip entry
    step_ref = f"Module {gate.module} Step {gate.step}"
    message = (
        f"⛔ VIOLATION: {step_ref} is a mandatory gate step but was skipped "
        f"without checkpoint evidence. current_step={current_step}, "
        f"missing checkpoints: {', '.join(missing_checkpoints)}. "
        f"No skipped_steps entry for '{skip_key}' found."
    )

    return Violation(
        gate=gate,
        current_step=current_step if current_step is not None else 0,
        missing_checkpoints=missing_checkpoints,
        message=message,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """Run mandatory gate validation.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).
    """
    parser = argparse.ArgumentParser(
        description="Validate mandatory gate checkpoints in bootcamp progress.",
    )
    parser.add_argument(
        "--progress",
        default=None,
        help=(
            "Path to bootcamp_progress.json. "
            "Defaults to config/bootcamp_progress.json relative to bootcamp root."
        ),
    )
    parser.add_argument(
        "--steering",
        default=None,
        help=(
            "Path to steering directory. "
            "Defaults to steering/ relative to bootcamp root."
        ),
    )
    args = parser.parse_args(argv)

    # Resolve paths relative to the bootcamp root
    bootcamp_root = Path(__file__).resolve().parent.parent
    steering_dir = Path(args.steering) if args.steering else bootcamp_root / "steering"
    progress_path = (
        Path(args.progress) if args.progress else bootcamp_root / "config" / "bootcamp_progress.json"
    )

    # Parse mandatory gates from steering files
    gates = parse_mandatory_gates(steering_dir)
    if not gates:
        print("No mandatory gates found in steering files.")
        sys.exit(0)

    # Read progress file
    if not progress_path.exists():
        # No progress file means no progress — no violation possible
        print(f"Progress file not found: {progress_path}")
        print("No progress recorded — no mandatory gate violations possible.")
        sys.exit(0)

    try:
        raw = progress_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Error reading progress file: {exc}", file=sys.stderr)
        sys.exit(1)

    if not raw.strip():
        print("Progress file is empty.", file=sys.stderr)
        sys.exit(1)

    try:
        progress = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in progress file: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(progress, dict):
        print("Progress file must contain a JSON object.", file=sys.stderr)
        sys.exit(1)

    # Validate
    result = validate_progress(progress, gates)

    # Report
    print(f"Mandatory gates checked: {result.gates_checked}")
    if result.passed:
        print("✅ All mandatory gate checkpoints satisfied.")
        sys.exit(0)
    else:
        print(f"❌ {len(result.violations)} violation(s) detected:", file=sys.stderr)
        for violation in result.violations:
            print(f"  {violation.message}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
