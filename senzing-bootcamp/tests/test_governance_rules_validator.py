"""Load-error and CLI example tests for validate_governance_rules.py.

Feature: governance-rule-conformance

These are concrete, non-input-varying unit tests for the validator's CLI surface
and load-error handling — the cases that complement the Hypothesis property
suite. They exercise the real ``main(argv=None)`` entry point and the ``run``
orchestrator, checking exit codes, stream routing, and the completion-count
gate, plus a sanity check that the shipped registry carries the eight seed rule
ids.

Covered cases:
    * Load errors (Requirement 4.7): a missing registry and an unparseable
      registry each exit 1, write the load error to stderr, and emit NO
      completion counts on stdout.
    * ``main([])`` over the real repository uses the default paths (the shipped
      registry + inferred repo root) and exits 0 with the success message and
      completion counts on stdout (Requirement 11.2).
    * ``main(["--registry", ...])`` with an explicit ``--repo-root`` exits 0 for
      a conformant temp registry and 1 for one with a failing assertion
      (Requirement 11.2).
    * Stream routing (Requirement 11.5): violations go to stderr; the success
      message and completion counts go to stdout.
    * Behavioral-only skip (Requirement 8.2): a ``static_checkable: false`` entry
      is not evaluated or failed, and is excluded from the rules-checked count.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make senzing-bootcamp/scripts/ importable (scripts are not packages).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_governance_rules import (  # noqa: E402
    load_registry,
    main,
    run,
)

# The repository root: <repo_root>/senzing-bootcamp/tests/<this file>.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SHIPPED_REGISTRY = _REPO_ROOT / "senzing-bootcamp" / "config" / "governance-rules.yaml"

# The eight statically-checkable seed rule ids that must ship in the registry.
_SEED_RULE_IDS = (
    "pointer-prefix",
    "mcp-first",
    "rule-06-license-mcp",
    "rule-15-module3-visualization-gate",
    "hook-name-form",
    "feedback-file-path",
    "frontmatter-inclusion",
    "graduation-completion-summary",
)

# A marker string that the completion-count lines always contain. Its absence
# from stdout proves the counts were suppressed (a load/schema halt).
_COUNT_MARKER = "Rule Entries checked"


def _write(path: Path, text: str) -> Path:
    """Write ``text`` to ``path`` (UTF-8) and return the path."""
    path.write_text(text, encoding="utf-8")
    return path


def _valid_registry_text() -> str:
    """Return a conformant two-assertion registry in the YAML subset.

    Both assertions target ``target.txt``; callers create that file under the
    ``--repo-root`` they pass so the assertions resolve and pass.
    """
    return (
        "rules:\n"
        '  - id: "rule-one"\n'
        '    rule: "First rule text."\n'
        '    category: "test-category"\n'
        "    enforced_by:\n"
        '      - "target.txt"\n'
        "    assertions:\n"
        '      - type: "file_exists"\n'
        '        file: "target.txt"\n'
        '      - type: "substring_present"\n'
        '        file: "target.txt"\n'
        '        value: "hello"\n'
    )


def _failing_registry_text() -> str:
    """Return a structurally valid registry whose single assertion fails."""
    return (
        "rules:\n"
        '  - id: "rule-fail"\n'
        '    rule: "Failing rule text."\n'
        '    category: "test-category"\n'
        "    enforced_by:\n"
        '      - "target.txt"\n'
        "    assertions:\n"
        '      - type: "substring_present"\n'
        '        file: "target.txt"\n'
        '        value: "absent-from-the-file"\n'
    )


def _behavioral_only_registry_text() -> str:
    """Return a registry pairing one passing static rule with a behavioral one.

    The behavioral-only entry sets ``static_checkable: false`` and carries no
    assertions, so the validator must skip it (never failing on it) and exclude
    it from the rules-checked count.
    """
    return (
        "rules:\n"
        '  - id: "static-rule"\n'
        '    rule: "Static rule text."\n'
        '    category: "test-category"\n'
        "    enforced_by:\n"
        '      - "target.txt"\n'
        "    assertions:\n"
        '      - type: "file_exists"\n'
        '        file: "target.txt"\n'
        '  - id: "behavioral-rule"\n'
        '    rule: "Behavioral-only rule text."\n'
        '    category: "behavioral-only"\n'
        "    enforced_by:\n"
        '      - "target.txt"\n'
        "    static_checkable: false\n"
        "    assertions:\n"
    )


class TestLoadErrors:
    """A missing or unparseable registry is a load error.

    Validates: Requirements 4.7, 11.5
    """

    def test_missing_registry_exits_1_no_counts(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A non-existent registry file exits 1 with the error on stderr.

        The load error halts before evaluation, so the completion counts are
        suppressed (Requirement 5.5 / 4.7).
        """
        missing = tmp_path / "nope.yaml"

        exit_code = main(["--registry", str(missing), "--repo-root", str(tmp_path)])
        captured = capsys.readouterr()

        assert exit_code == 1
        # The load error names the registry and is written to stderr.
        assert "could not load registry" in captured.err
        assert str(missing) in captured.err
        # No completion counts are emitted on a load halt.
        assert _COUNT_MARKER not in captured.out
        assert _COUNT_MARKER not in captured.err

    def test_unparseable_non_rules_top_key_exits_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A registry whose top-level key is not ``rules:`` is a load error."""
        registry = _write(
            tmp_path / "governance-rules.yaml",
            'notrules:\n  - id: "x"\n',
        )

        exit_code = main(
            ["--registry", str(registry), "--repo-root", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "could not load registry" in captured.err
        assert _COUNT_MARKER not in captured.out

    def test_unparseable_unterminated_quote_exits_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A registry with an unterminated double-quoted scalar is a load error."""
        registry = _write(
            tmp_path / "governance-rules.yaml",
            'rules:\n  - id: "unterminated\n',
        )

        exit_code = main(
            ["--registry", str(registry), "--repo-root", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 1
        assert "could not load registry" in captured.err
        # A load halt never reports completion counts.
        assert _COUNT_MARKER not in captured.out
        assert _COUNT_MARKER not in captured.err


class TestMainDefaults:
    """``main([])`` validates the shipped registry over the real repository.

    Validates: Requirements 11.2, 11.5
    """

    def test_main_no_args_passes_over_real_repo(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """With no args, the default paths resolve to the conformant repo.

        The shipped ``governance-rules.yaml`` is conformant (task 7.1), so a
        no-arg run exits 0 and prints the success message plus the completion
        counts (eight rules checked, zero violations) to stdout.
        """
        exit_code = main([])
        captured = capsys.readouterr()

        assert exit_code == 0, (
            "main([]) should pass over the conformant shipped registry; "
            f"stderr was:\n{captured.err}"
        )
        assert "Governance rule conformance: PASS" in captured.out
        assert "Rule Entries checked: 8" in captured.out
        assert "Violations found: 0" in captured.out
        # Success path writes nothing to stderr.
        assert captured.err == ""


class TestMainWithRegistry:
    """``main(["--registry", ...])`` honors an explicit registry and repo root.

    Validates: Requirements 11.2, 11.5
    """

    def test_valid_registry_exits_0_counts_on_stdout(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A conformant temp registry exits 0 with counts on stdout, stderr clean."""
        _write(tmp_path / "target.txt", "hello world")
        registry = _write(tmp_path / "governance-rules.yaml", _valid_registry_text())

        exit_code = main(
            ["--registry", str(registry), "--repo-root", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0, f"unexpected stderr:\n{captured.err}"
        assert "Governance rule conformance: PASS" in captured.out
        assert "Rule Entries checked: 1" in captured.out
        assert "Violations found: 0" in captured.out
        assert captured.err == ""

    def test_failing_registry_exits_1_violation_on_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A failing assertion exits 1, routing the violation to stderr only.

        Stream routing (Requirement 11.5/5.6): the violation detail — including
        the failing rule id, the assertion, and the file path — goes to stderr,
        never stdout. Completion counts still print (the run completed).
        """
        _write(tmp_path / "target.txt", "hello world")
        registry = _write(
            tmp_path / "governance-rules.yaml", _failing_registry_text()
        )

        exit_code = main(
            ["--registry", str(registry), "--repo-root", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 1
        # Violation details are on stderr and name the rule, assertion, and file.
        assert "rule-fail" in captured.err
        assert "substring_present" in captured.err
        assert "target.txt" in captured.err
        # The success banner never appears, and the violation is not on stdout.
        assert "Governance rule conformance: PASS" not in captured.out
        assert "rule-fail" not in captured.out
        # The run completed, so completion counts are still emitted on stdout.
        assert "Rule Entries checked: 1" in captured.out
        assert "Violations found: 1" in captured.out


class TestBehavioralOnlySkip:
    """Behavioral-only entries are skipped, not evaluated or counted.

    Validates: Requirements 8.2
    """

    def test_behavioral_only_rule_is_skipped(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A ``static_checkable: false`` entry never fails the run.

        The registry pairs a passing static rule with a behavioral-only rule
        that carries no assertions. The run exits 0, and the rules-checked count
        reflects only the single statically-checkable rule.
        """
        _write(tmp_path / "target.txt", "present")
        registry = _write(
            tmp_path / "governance-rules.yaml", _behavioral_only_registry_text()
        )

        # Assert via the run() result that only the static rule was counted.
        result = run(registry, tmp_path)
        assert result.exit_code == 0
        assert result.violations == []
        assert result.rules_checked == 1

        # And via the CLI/stdout count for the same registry.
        exit_code = main(
            ["--registry", str(registry), "--repo-root", str(tmp_path)]
        )
        captured = capsys.readouterr()

        assert exit_code == 0, f"unexpected stderr:\n{captured.err}"
        assert "Rule Entries checked: 1" in captured.out
        assert "Violations found: 0" in captured.out


class TestSeedRegistry:
    """The shipped registry carries the eight statically-checkable seed ids.

    Validates: Requirements 11.2 (seed-rule presence, Requirement 7)
    """

    def test_shipped_registry_contains_eight_seed_ids(self) -> None:
        """``load_registry`` of the shipped file exposes every seed rule id."""
        raw_entries = load_registry(_SHIPPED_REGISTRY)
        ids = {raw.get("id") for raw in raw_entries}

        for seed_id in _SEED_RULE_IDS:
            assert seed_id in ids, f"shipped registry is missing seed id {seed_id!r}"
