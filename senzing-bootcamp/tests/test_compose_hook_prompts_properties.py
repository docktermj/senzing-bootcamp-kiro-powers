"""Property-based tests for the compose_hook_prompts.py composer logic.

Feature: hook-architecture-improvements (Theme B — hook-prompt deduplication).

These are *script-behavior* property tests exercising the composer over
Hypothesis-generated templates / fragment sets (and over temp copies of the
real gate-hook files). Per ``structure.md``, script-behavior tests live in
``senzing-bootcamp/tests/`` (tests that read the *real* on-disk hook files for
the no-op refactor invariants live in the repo-root ``tests/``).

Properties covered:

- **Property 3** — Composition fully expands fragments and leaves no residual
  markers. Validates: Requirements 6.1, 6.2
- **Property 5** — Unknown fragment references are reported and fail (exit 1 +
  name). Validates: Requirements 6.5
- **Property 8** — Composed hooks are schema-valid and preserve the ``when``
  block. Validates: Requirements 8.2, 8.3
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import compose_hook_prompts  # noqa: E402
import hook_prompt_fragments  # noqa: E402
from compose_hook_prompts import (  # noqa: E402
    HOOK_TEMPLATES,
    UnknownFragmentError,
    compose_hook,
    compose_prompt,
    serialize_hook,
)

# The real hooks directory (used only as a read-only template source that gets
# copied into per-example temp dirs — never written to).
_REAL_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"

# Event types seen across the real hook files; used to generate when blocks.
_EVENT_TYPES = [
    "preToolUse",
    "agentStop",
    "postToolUse",
    "fileEdited",
    "fileCreated",
    "promptSubmit",
]


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


def st_fragment_name() -> st.SearchStrategy[str]:
    """Generate valid marker names (must match the composer's ``[A-Za-z0-9_]+``)."""
    return st.from_regex(r"[A-Za-z0-9_]{1,12}", fullmatch=True)


def st_safe_text(min_size: int = 0, max_size: int = 40) -> st.SearchStrategy[str]:
    """Generate literal/fragment text that cannot accidentally form a marker.

    Braces are excluded so generated text can never introduce a spurious
    ``{{fragment:`` substring; control/surrogate chars are excluded so the text
    round-trips cleanly through JSON and the import-based fragment loader.
    """
    return st.text(
        alphabet=st.characters(
            blacklist_characters="{}",
            blacklist_categories=("Cs", "Cc"),
        ),
        min_size=min_size,
        max_size=max_size,
    )


def st_fragments(
    min_size: int = 1, max_size: int = 5
) -> st.SearchStrategy[dict[str, str]]:
    """Generate a fragment-name -> non-empty text mapping."""
    return st.dictionaries(
        keys=st_fragment_name(),
        values=st_safe_text(min_size=1, max_size=40),
        min_size=min_size,
        max_size=max_size,
    )


@st.composite
def st_template_with_markers(
    draw: st.DrawFn,
) -> tuple[str, dict[str, str], list[str]]:
    """Build a template by interleaving literal text and resolvable markers.

    Returns:
        ``(template, fragments, referenced_names)`` where every
        ``{{fragment:NAME}}`` marker in *template* resolves to a key in
        *fragments*.
    """
    fragments = draw(st_fragments())
    names = list(fragments)

    n_markers = draw(st.integers(min_value=1, max_value=6))
    parts: list[str] = []
    referenced: list[str] = []
    for _ in range(n_markers):
        parts.append(draw(st_safe_text()))
        name = draw(st.sampled_from(names))
        parts.append("{{fragment:" + name + "}}")
        referenced.append(name)
    parts.append(draw(st_safe_text()))

    return "".join(parts), fragments, referenced


@st.composite
def st_template_with_unknown(
    draw: st.DrawFn,
) -> tuple[str, dict[str, str], str]:
    """Build a template referencing a marker name guaranteed absent from *fragments*.

    Returns:
        ``(template, fragments, absent_name)``.
    """
    fragments = draw(st_fragments(min_size=0, max_size=4))
    absent = draw(st_fragment_name())
    assume(absent not in fragments)

    template = (
        draw(st_safe_text())
        + "{{fragment:"
        + absent
        + "}}"
        + draw(st_safe_text())
    )
    return template, fragments, absent


@st.composite
def st_when_block(draw: st.DrawFn) -> dict[str, object]:
    """Generate a varied but schema-plausible ``when`` block."""
    when: dict[str, object] = {"type": draw(st.sampled_from(_EVENT_TYPES))}
    if draw(st.booleans()):
        when["toolTypes"] = draw(
            st.lists(
                st.sampled_from(["write", "read"]),
                min_size=1,
                max_size=2,
                unique=True,
            )
        )
    if draw(st.booleans()):
        when["patterns"] = draw(
            st.lists(
                st.from_regex(r"\*\.[a-z]{1,4}", fullmatch=True),
                min_size=1,
                max_size=2,
                unique=True,
            )
        )
    return when


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_main_silently(argv: list[str]) -> tuple[int, str, str]:
    """Invoke ``compose_hook_prompts.main(argv)`` capturing stdout/stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = compose_hook_prompts.main(argv)
    return code, out.getvalue(), err.getvalue()


def _write_fragments_module(path: Path, fragments: dict[str, str]) -> None:
    """Write a stdlib-only fragment-source module exposing ``FRAGMENTS``."""
    path.write_text(
        "from __future__ import annotations\n"
        f"FRAGMENTS = {fragments!r}\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Property 3 — Composition fully expands fragments and leaves no residual markers
# ---------------------------------------------------------------------------


class TestComposition:
    """Property 3: compose_prompt expands every marker and leaves no markers.

    **Validates: Requirements 6.1, 6.2**
    """

    # Feature: hook-architecture-improvements, Property 3
    @given(case=st_template_with_markers())
    @settings(max_examples=20)
    def test_all_referenced_fragments_present_and_no_residual_markers(
        self, case: tuple[str, dict[str, str], list[str]]
    ) -> None:
        template, fragments, referenced = case

        result = compose_prompt(template, fragments)

        # (a) The full text of each referenced fragment is present in the output.
        for name in referenced:
            assert fragments[name] in result

        # (b) No unexpanded marker substring remains.
        assert "{{fragment:" not in result

    # Feature: hook-architecture-improvements, Property 3
    @given(case=st_template_with_markers())
    @settings(max_examples=20)
    def test_marker_free_template_is_unchanged(
        self, case: tuple[str, dict[str, str], list[str]]
    ) -> None:
        template, fragments, _referenced = case

        # A template with no markers at all must pass through verbatim.
        marker_free = template.replace("{{fragment:", "{ {fragment:")
        assert compose_prompt(marker_free, fragments) == marker_free


# ---------------------------------------------------------------------------
# Property 5 — Unknown fragment references are reported and fail (exit 1 + name)
# ---------------------------------------------------------------------------


class TestUnknownFragment:
    """Property 5: an undefined marker raises UnknownFragmentError; main() exits 1.

    **Validates: Requirements 6.5**
    """

    # Feature: hook-architecture-improvements, Property 5
    @given(case=st_template_with_unknown())
    @settings(max_examples=20)
    def test_compose_prompt_raises_on_unknown_fragment(
        self, case: tuple[str, dict[str, str], str]
    ) -> None:
        template, fragments, absent = case

        with pytest.raises(UnknownFragmentError) as exc_info:
            compose_prompt(template, fragments)

        assert exc_info.value.fragment_name == absent

    # Feature: hook-architecture-improvements, Property 5
    @given(omitted=st.sampled_from(sorted(hook_prompt_fragments.FRAGMENTS)))
    @settings(max_examples=20)
    def test_main_verify_exits_one_and_reports_missing_fragment(
        self, omitted: str
    ) -> None:
        # A real gate-hook template references every fragment, so removing any
        # one fragment from the source makes main() fail with exit 1 and report
        # that fragment name.
        td = tempfile.mkdtemp()
        try:
            hooks_dir = Path(td) / "hooks"
            hooks_dir.mkdir()
            for hook_id in HOOK_TEMPLATES:
                shutil.copy(
                    _REAL_HOOKS_DIR / f"{hook_id}.kiro.hook",
                    hooks_dir / f"{hook_id}.kiro.hook",
                )

            fragments_path = Path(td) / "partial_fragments.py"
            remaining = {
                name: text
                for name, text in hook_prompt_fragments.FRAGMENTS.items()
                if name != omitted
            }
            _write_fragments_module(fragments_path, remaining)

            argv = [
                "--verify",
                "--hooks-dir",
                str(hooks_dir),
                "--fragments",
                str(fragments_path),
            ]
            code, _out, err = _run_main_silently(argv)

            assert code == 1
            assert f"unknown fragment '{omitted}'" in err
        finally:
            shutil.rmtree(td, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 8 — Composed hooks are schema-valid and preserve the when block
# ---------------------------------------------------------------------------


class TestSchemaPreservation:
    """Property 8: composed output is valid JSON with required fields and an
    unchanged ``when`` block.

    **Validates: Requirements 8.2, 8.3**
    """

    # Feature: hook-architecture-improvements, Property 8
    @given(
        hook_id=st.sampled_from(sorted(HOOK_TEMPLATES)),
        when=st_when_block(),
    )
    @settings(max_examples=20)
    def test_composed_hook_is_schema_valid_and_preserves_when_block(
        self, hook_id: str, when: dict[str, object]
    ) -> None:
        td = tempfile.mkdtemp()
        try:
            hooks_dir = Path(td) / "hooks"
            hooks_dir.mkdir()

            # Start from the real hook file, then swap in the generated when block
            # so we exercise composition against arbitrary (but schema-plausible)
            # when blocks while keeping a valid then.prompt template to compose.
            original = json.loads(
                (_REAL_HOOKS_DIR / f"{hook_id}.kiro.hook").read_text(encoding="utf-8")
            )
            original["when"] = when
            (hooks_dir / f"{hook_id}.kiro.hook").write_text(
                json.dumps(original, indent=2), encoding="utf-8"
            )

            composed = compose_hook(
                hook_id, hook_prompt_fragments.FRAGMENTS, hooks_dir=hooks_dir
            )

            # Required schema fields are all present.
            for field in ("name", "version", "when", "then"):
                assert field in composed, f"missing required field: {field}"

            # The when block (type + any toolTypes/patterns) is deep-equal.
            assert composed["when"] == when

            # then.prompt is a self-contained string with no residual markers.
            assert isinstance(composed["then"]["prompt"], str)
            assert "{{fragment:" not in composed["then"]["prompt"]

            # The serialized hook is valid JSON that round-trips exactly.
            serialized = serialize_hook(composed)
            assert json.loads(serialized) == composed
        finally:
            shutil.rmtree(td, ignore_errors=True)
