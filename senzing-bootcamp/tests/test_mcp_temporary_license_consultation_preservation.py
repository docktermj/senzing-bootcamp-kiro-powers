"""Preservation property tests for the mcp-temporary-license-consultation bugfix.

Property 2: Preservation — Sufficient-License Paths and Structural Invariants
Unchanged.

The fix (tasks 3.1–3.3) is additive and touches only three license-insufficient
regions:

- Module 1 Step 6d ("does not have license" branch)
- Module 2 Step 5a (built-in evaluation license explanation)
- Module 2 Step 5c "no license" branch

Everything else must remain byte-identical. These tests observe the UNFIXED
steering files, snapshot the regions the fix will NOT touch via SHA-256
(mirroring the ``_STEP_HASHES`` pattern in ``test_module2_license_question.py``),
and use structural assertions (marker counts, presence checks) for the regions
adjacent to the edits. The MCP server URL is read dynamically from ``mcp.json``
and never hardcoded here (a security hook blocks hardcoded MCP URLs).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

EXPECTED OUTCOME on UNFIXED code: ALL tests PASS (this captures the baseline
behavior that must be preserved).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_MODULE_01_FILE = _STEERING_DIR / "module-01-phase1-discovery.md"
_MODULE_02_FILE = _STEERING_DIR / "module-02-sdk-setup.md"
_MCP_JSON_FILE = _BOOTCAMP_DIR / "mcp.json"

# Emoji markers (escaped to keep this file plain-ASCII-safe in source).
_POINTER = "\U0001f449"  # 👉
_STOP_SIGN = "\U0001f6d1"  # 🛑


# ---------------------------------------------------------------------------
# License situation model (mirrors the exploration suite / design)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LicenseSituation:
    """A license-handling situation encountered during the bootcamp.

    Attributes:
        total_record_count: Total records across the bootcamper's sources.
        has_sufficient_license: Whether a sufficient custom license is present.
        error_code: A SENZ error code observed during load, or None.
    """

    total_record_count: int
    has_sufficient_license: bool
    error_code: str | None


def is_bug_condition(x: LicenseSituation) -> bool:
    """Return True when the license is insufficient (the bug-triggering case).

    Args:
        x: The license situation to classify.

    Returns:
        True when capacity is exceeded or a SENZ9000 capacity error occurred
        AND no sufficient custom license is present.
    """
    return (
        x.total_record_count > 500 or x.error_code == "SENZ9000"
    ) and not x.has_sufficient_license


@st.composite
def st_license_situation(draw: st.DrawFn) -> LicenseSituation:
    """Strategy that generates LicenseSituation values across the input space."""
    total = draw(st.integers(min_value=0, max_value=10_000_000))
    has_license = draw(st.booleans())
    error_code = draw(st.sampled_from([None, "SENZ9000", "SENZ0002"]))
    return LicenseSituation(total, has_license, error_code)


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the full UTF-8 text of a file."""
    return path.read_text(encoding="utf-8")


def _sha256(content: str) -> str:
    """Return the SHA-256 hex digest of ``content``."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _mcp_server_url() -> str:
    """Read the MCP server URL from mcp.json (the single source of truth).

    Returns:
        The configured MCP server URL string. Read dynamically so the URL is
        never hardcoded in this test file.
    """
    data = json.loads(_read(_MCP_JSON_FILE))
    server = data["mcpServers"]["senzing-mcp-server"]
    return str(server["url"])


def _mcp_server_host() -> str:
    """Return just the host portion of the MCP server URL (no scheme/path)."""
    url = _mcp_server_url()
    host = re.sub(r"^[a-z]+://", "", url)
    return host.split("/")[0]


# ---------------------------------------------------------------------------
# Module 2 section extraction helpers
# ---------------------------------------------------------------------------


def _extract_step5(content: str) -> str:
    """Extract the Module 2 'Step 5: Configure License' section."""
    pattern = re.compile(
        r"(## Step 5: Configure License.*?)"
        r"(?=\n## (?:Step \d|Success Criteria|Transition|Troubleshooting|Agent Behavior))",
        re.DOTALL,
    )
    match = pattern.search(content)
    assert match is not None, "Could not find '## Step 5: Configure License' section"
    return match.group(1)


def _extract_step_section_m2(content: str, step_num: int) -> str | None:
    """Extract a Module 2 ``## Step N:`` section by number."""
    next_headings = {
        1: "Step 2:",
        2: "Step 3:",
        3: "Step 4:",
        4: "Step 5:",
        5: "Step 6:",
        6: "Step 7:",
        7: "Step 8:",
        8: "Step 9:",
        9: "Success Criteria",
    }
    next_h = next_headings.get(step_num, "Success Criteria")
    pattern = re.compile(
        rf"(## Step {step_num}:.*?)(?=\n## {re.escape(next_h)})",
        re.DOTALL,
    )
    match = pattern.search(content)
    return match.group(1) if match else None


def _slice_between(text: str, start_pat: str, end_pat: str | None) -> str | None:
    """Return the slice of ``text`` from ``start_pat`` up to ``end_pat``.

    Args:
        text: The text to slice.
        start_pat: Regex marking the (inclusive) start.
        end_pat: Regex marking the (exclusive) end, or None for end-of-text.

    Returns:
        The matched slice, or None if ``start_pat`` is not found.
    """
    start_match = re.search(start_pat, text)
    if not start_match:
        return None
    start = start_match.start()
    if end_pat is None:
        return text[start:]
    end_match = re.search(end_pat, text[start_match.end():])
    end = start_match.end() + end_match.start() if end_match else len(text)
    return text[start:end]


def _extract_step5_header(content: str) -> str | None:
    """Step 5 header region: the gate + license-check-order callout (pre-5a)."""
    return _slice_between(_extract_step5(content), r"## Step 5: Configure License", r"### 5a\.")


def _extract_5a(content: str) -> str | None:
    """Module 2 Step 5a region (EDITED by the fix — structural checks only)."""
    return _slice_between(_extract_step5(content), r"### 5a\.", r"### 5b\.")


def _extract_5b(content: str) -> str | None:
    """Module 2 Step 5b region: the single 👉 license question + STOP."""
    return _slice_between(_extract_step5(content), r"### 5b\.", r"### 5c\.")


def _extract_5c_has_license(content: str) -> str | None:
    """Module 2 Step 5c 'has license' branches (Base64 / .lic) — preserved."""
    return _slice_between(
        _extract_step5(content),
        r"### 5c\.",
        r"\*\*IF the bootcamper has no license:\*\*",
    )


def _extract_5c_no_license(content: str) -> str | None:
    """Module 2 Step 5c 'no license' branch (EDITED — structural checks only)."""
    return _slice_between(
        _extract_step5(content),
        r"\*\*IF the bootcamper has no license:\*\*",
        r"### 5d\.",
    )


def _extract_5d(content: str) -> str | None:
    """Module 2 Step 5d region: LICENSEFILE config + license: custom recording."""
    return _slice_between(_extract_step5(content), r"### 5d\.", r"\*\*Checkpoint:\*\*")


# ---------------------------------------------------------------------------
# Module 1 sub-step extraction helpers
# ---------------------------------------------------------------------------

_M1_SUBSTEP_ORDER = ["6a", "6b", "6c", "6d", "6e"]


def _extract_m1_substep(content: str, sub_id: str) -> str | None:
    """Extract a Module 1 ``**6x.`` sub-step block by identifier.

    Args:
        content: The full Module 1 markdown.
        sub_id: One of '6a', '6b', '6c', '6d', '6e'.

    Returns:
        The sub-step block from its ``**6x.`` marker up to the next sub-step
        marker (or, for 6e, up to the numbered Step 7 'Confirm' item).
    """
    start_match = re.search(rf"\*\*{re.escape(sub_id)}\.", content)
    if not start_match:
        return None
    start = start_match.start()
    idx = _M1_SUBSTEP_ORDER.index(sub_id)
    if idx + 1 < len(_M1_SUBSTEP_ORDER):
        nxt = _M1_SUBSTEP_ORDER[idx + 1]
        end_match = re.search(rf"\*\*{re.escape(nxt)}\.", content[start_match.end():])
        end = start_match.end() + end_match.start() if end_match else len(content)
    else:
        end_match = re.search(r"\n\d+\.\s\*\*Confirm", content[start_match.end():])
        end = start_match.end() + end_match.start() if end_match else len(content)
    return content[start:end]


# ---------------------------------------------------------------------------
# Baselines — SHA-256 snapshots of UNFIXED regions the fix will NOT touch.
# Mirrors the ``_STEP_HASHES`` snapshot pattern. The Module 2 step1-9 hashes
# match those locked in test_module2_license_question.py (cross-validation).
# ---------------------------------------------------------------------------

_BASELINE_HASHES: dict[str, str] = {
    # Module 2 non-license sections (Steps 1-4 and 6-9)
    "m2_step1": "68d4a9cd86708c3ac65c2fd2613b0e79c8770ae7cc455d580c0275a721c8d5d7",
    "m2_step2": "d699ce64d2b9f6f8f834466b7886611343554f5d3e7f1bf89c39ad7d58cf92a0",
    "m2_step3": "3591982547aded6cd5da8870c3c6d8ffa6476f92fa00ea21c9fa1299f6cf4088",
    "m2_step4": "5ee5168b5bfe301fcf7f6841ef78f3ab334dfc1b413e7440cc598fc72d69e6be",
    "m2_step6": "67f0d91f31c40a0ef08336845a0a001ab959d4dc38c8ef5864e7a0141df4837f",
    "m2_step7": "e70acaae1640b0259e3cc5927f5ea27c88a98b3625cc2d5a6eca36ca367bb7a2",
    "m2_step8": "a7589b48765763d59c3b6ebff53af14dee93bf8823d2f9e948f58334b85f3305",
    "m2_step9": "feae2a6c6c0dc8af1450941a29336be77de8058412bd2243c9d01ec88da74fce",
    # Module 2 Step 5 preserved sub-regions (header gate, 5b question, 5c
    # "has license" branches, 5d LICENSEFILE config) — NOT 5a / 5c "no license"
    "m2_step5_header": "3a579d5d831f98ada306970dd610bddf4811a8607d8cd3750535125ec995c0b6",
    "m2_5b": "061344e980dfa46ac70251a75eac875cedf91ef779311a9856e942fb660f6274",
    "m2_5c_has_license": "8f4721c2c4fe42d3af9ec1e861ad6bc674ab3471e67b7acebd9285ec16eab27b",
    "m2_5d": "1656db835193fb7ee569b206b22478138d86668a2e5c2c202df8f6810892bc8f",
    # Module 1 preserved license sub-steps (6a, 6b, 6c, 6e) — NOT 6d (edited)
    # NOTE (module1-license-request-option re-baseline): the m1_6b hash was
    # re-baselined observation-first from the current bytes. That spec is
    # chartered to edit Step 6b (Task 1.1 added the in-flow MCP
    # License_Request_Option to the Step 6b licensing-trigger reference), so the
    # 6b region legitimately changed for this spec. The other preserved
    # sub-steps (6a, 6c, 6e) remain byte-identical to baseline.
    "m1_6a": "06d0c151f7973f09d05f789afb572f7c788f523f2a6e0918be03a9004f76755a",
    "m1_6b": "ef5bb1131098a3f1502c72694232ae0f758fc7d5e9a626a1b564bf47de536d91",
    "m1_6c": "461b6fc579b83b42460e93eb8414d05bbbec48c6da76a3cc92286a83cbbbc2fc",
    "m1_6e": "28c9fdd1338c0cf4b165d10e639e8b17383b6564235f648b85c0a7a35b4846b0",
}


def _current_region(key: str) -> str:
    """Return the current text for a baseline region key (raises if missing)."""
    if key.startswith("m2_step") and key != "m2_step5_header":
        m2 = _read(_MODULE_02_FILE)
        section = _extract_step_section_m2(m2, int(key.replace("m2_step", "")))
    elif key == "m2_step5_header":
        section = _extract_step5_header(_read(_MODULE_02_FILE))
    elif key == "m2_5b":
        section = _extract_5b(_read(_MODULE_02_FILE))
    elif key == "m2_5c_has_license":
        section = _extract_5c_has_license(_read(_MODULE_02_FILE))
    elif key == "m2_5d":
        section = _extract_5d(_read(_MODULE_02_FILE))
    elif key.startswith("m1_"):
        section = _extract_m1_substep(_read(_MODULE_01_FILE), key.replace("m1_", ""))
    else:  # pragma: no cover - guard against typos in keys
        raise KeyError(f"Unknown baseline key: {key}")
    assert section is not None, f"Could not extract region for baseline key '{key}'"
    return section


# ===========================================================================
# Frontmatter preservation
# **Validates: Requirements 3.4**
# ===========================================================================


class TestFrontmatterPreservation:
    """Both steering files retain ``inclusion: manual`` frontmatter.

    EXPECTED OUTCOME on UNFIXED code: PASS."""

    def test_module1_frontmatter_manual(self) -> None:
        """**Validates: Requirements 3.4** — Module 1 keeps inclusion: manual."""
        content = _read(_MODULE_01_FILE)
        assert content.startswith("---\ninclusion: manual\n---"), (
            "Module 1 must retain '---\\ninclusion: manual\\n---' frontmatter"
        )

    def test_module2_frontmatter_manual(self) -> None:
        """**Validates: Requirements 3.4** — Module 2 keeps inclusion: manual."""
        content = _read(_MODULE_02_FILE)
        assert content.startswith("---\ninclusion: manual\n---"), (
            "Module 2 must retain '---\\ninclusion: manual\\n---' frontmatter"
        )


# ===========================================================================
# Non-license sections preserved (hash-locked)
# **Validates: Requirements 3.6**
# ===========================================================================


class TestNonLicenseSectionsPreserved:
    """Module 2 Steps 1-4 and 6-9 are byte-identical to baseline.

    EXPECTED OUTCOME on UNFIXED code: PASS."""

    def test_module2_non_license_steps_unchanged(self) -> None:
        """**Validates: Requirements 3.6** — non-license Module 2 steps unchanged."""
        for key in ("m2_step1", "m2_step2", "m2_step3", "m2_step4",
                    "m2_step6", "m2_step7", "m2_step8", "m2_step9"):
            actual = _sha256(_current_region(key))
            assert actual == _BASELINE_HASHES[key], (
                f"{key} content changed.\n"
                f"Expected: {_BASELINE_HASHES[key]}\nActual:   {actual}"
            )


# ===========================================================================
# Module 2 Step 5 preserved sub-regions (hash-locked)
# **Validates: Requirements 3.2, 3.3**
# ===========================================================================


class TestModule2Step5PreservedRegions:
    """Step 5 header, 5b, 5c 'has license' branches, and 5d are unchanged.

    These regions are NOT touched by the fix (which edits only 5a and the 5c
    'no license' branch). EXPECTED OUTCOME on UNFIXED code: PASS."""

    def test_step5_header_unchanged(self) -> None:
        """**Validates: Requirements 3.3** — gate + license-check-order callout."""
        actual = _sha256(_current_region("m2_step5_header"))
        assert actual == _BASELINE_HASHES["m2_step5_header"], (
            "Step 5 header (gate + license-check order) changed."
        )

    def test_step5b_question_unchanged(self) -> None:
        """**Validates: Requirements 3.3** — the 5b license question is unchanged."""
        actual = _sha256(_current_region("m2_5b"))
        assert actual == _BASELINE_HASHES["m2_5b"], "Step 5b question region changed."

    def test_step5c_has_license_branches_unchanged(self) -> None:
        """**Validates: Requirements 3.2** — Base64 decode / .lic branches unchanged."""
        section = _current_region("m2_5c_has_license")
        # Spot-check the key mechanics live inside this hashed region.
        assert "base64 --decode > licenses/g2.lic" in section
        assert "NEVER ask the user to paste a license key into chat" in section
        actual = _sha256(section)
        assert actual == _BASELINE_HASHES["m2_5c_has_license"], (
            "Step 5c 'has license' branches changed."
        )

    def test_step5d_licensefile_config_unchanged(self) -> None:
        """**Validates: Requirements 3.2** — PIPELINE LICENSEFILE + license: custom."""
        section = _current_region("m2_5d")
        assert "PIPELINE" in section and "LICENSEFILE" in section
        assert '"licenses/g2.lic"' in section
        assert "`license: custom`" in section
        actual = _sha256(section)
        assert actual == _BASELINE_HASHES["m2_5d"], "Step 5d config region changed."


# ===========================================================================
# Module 1 preserved sub-steps (hash-locked) + 6a skip path
# **Validates: Requirements 3.1, 3.2**
# ===========================================================================


class TestModule1PreservedSubsteps:
    """Module 1 sub-steps 6a, 6b, 6c, 6e are byte-identical to baseline.

    The fix edits only Step 6d. EXPECTED OUTCOME on UNFIXED code: PASS."""

    def test_substeps_6a_6b_6c_6e_unchanged(self) -> None:
        """**Validates: Requirements 3.1, 3.2** — preserved Module 1 sub-steps."""
        for key in ("m1_6a", "m1_6b", "m1_6c", "m1_6e"):
            actual = _sha256(_current_region(key))
            assert actual == _BASELINE_HASHES[key], (
                f"{key} content changed.\n"
                f"Expected: {_BASELINE_HASHES[key]}\nActual:   {actual}"
            )

    def test_step6a_skips_6b_to_6e_and_proceeds_to_step7(self) -> None:
        """**Validates: Requirements 3.1** — <= 500 records skip 6b-6e -> Step 7."""
        section = _current_region("m1_6a")
        assert "skip Steps 6b\u20136e and proceed directly to Step 7" in section, (
            "Step 6a must retain the '<= 500 records skip 6b-6e -> Step 7' path"
        )


# ===========================================================================
# Module 2 Step 5 structural invariants (regions adjacent to the edits)
# **Validates: Requirements 3.3, 3.4**
# ===========================================================================


class TestStep5StructuralInvariants:
    """Step 5 keeps exactly one 👉 and one STOP, plus its gate, contacts, and
    checkpoint — verified structurally because the fix edits 5a / 5c 'no license'.

    EXPECTED OUTCOME on UNFIXED code: PASS."""

    def test_step5_exactly_one_pointer_question(self) -> None:
        """**Validates: Requirements 3.3** — exactly one 👉 (the 5b question)."""
        step5 = _extract_step5(_read(_MODULE_02_FILE))
        assert step5.count(_POINTER) == 1, (
            f"Step 5 must contain exactly one pointer marker; found {step5.count(_POINTER)}"
        )

    def test_step5_exactly_one_stop(self) -> None:
        """**Validates: Requirements 3.3** — exactly one whole-word STOP in Step 5."""
        step5 = _extract_step5(_read(_MODULE_02_FILE))
        stops = re.findall(r"\bSTOP\b", step5)
        assert len(stops) == 1, f"Step 5 must contain exactly one STOP; found {len(stops)}"

    def test_step5_mandatory_gate_marker(self) -> None:
        """**Validates: Requirements 3.3** — the MANDATORY GATE marker is present."""
        step5 = _extract_step5(_read(_MODULE_02_FILE))
        assert "\u26d4 MANDATORY GATE \u2014 Never skip this step" in step5, (
            "Step 5 must retain the 'MANDATORY GATE - Never skip this step' marker"
        )

    def test_step5_license_check_order_callout(self) -> None:
        """**Validates: Requirements 3.3** — the license-check order callout unchanged."""
        step5 = _extract_step5(_read(_MODULE_02_FILE))
        assert "**License check order:**" in step5
        assert "project-local `licenses/g2.lic`" in step5
        assert "built-in evaluation (500 records)" in step5

    def test_step5_email_contacts_and_readme_present(self) -> None:
        """**Validates: Requirements 3.4** — email contacts + README reference present."""
        step5 = _extract_step5(_read(_MODULE_02_FILE))
        assert "support@senzing.com" in step5
        assert "sales@senzing.com" in step5
        assert "licenses/README.md" in step5

    def test_step5_evaluation_preference_recording(self) -> None:
        """**Validates: Requirements 3.4** — `license: evaluation` recording present."""
        step5 = _extract_step5(_read(_MODULE_02_FILE))
        assert "`license: evaluation`" in step5

    def test_step5_checkpoint_present(self) -> None:
        """**Validates: Requirements 3.4** — the Step 5 checkpoint is unchanged."""
        step5 = _extract_step5(_read(_MODULE_02_FILE))
        assert "**Checkpoint:** Write step 5 to `config/bootcamp_progress.json`." in step5


# ===========================================================================
# Module 1 Step 6b / 6d marker invariants (regions adjacent to the edit)
# **Validates: Requirements 3.4**
# ===========================================================================


class TestModule1SubstepMarkers:
    """Module 1 sub-steps 6b and 6d keep exactly one 👉 question and one 🛑 STOP.

    6b is hash-locked elsewhere; 6d is the edited region, so the fix must not add
    a second 👉 or 🛑. EXPECTED OUTCOME on UNFIXED code: PASS."""

    def test_6b_exactly_one_pointer_and_one_stop(self) -> None:
        """**Validates: Requirements 3.4** — 6b keeps one pointer and one stop marker."""
        section = _extract_m1_substep(_read(_MODULE_01_FILE), "6b")
        assert section is not None
        assert section.count(_POINTER) == 1, "Step 6b must keep exactly one pointer marker"
        assert section.count(_STOP_SIGN) == 1, "Step 6b must keep exactly one stop marker"

    def test_6d_exactly_one_pointer_and_one_stop(self) -> None:
        """**Validates: Requirements 3.4** — 6d keeps one pointer and one stop (no new marker)."""
        section = _extract_m1_substep(_read(_MODULE_01_FILE), "6d")
        assert section is not None
        assert section.count(_POINTER) == 1, (
            f"Step 6d must keep exactly one pointer marker; found {section.count(_POINTER)}"
        )
        assert section.count(_STOP_SIGN) == 1, (
            f"Step 6d must keep exactly one stop marker; found {section.count(_STOP_SIGN)}"
        )

    def test_6d_email_contact_and_checkpoint_present(self) -> None:
        """**Validates: Requirements 3.4** — 6d keeps support contact + checkpoint."""
        section = _extract_m1_substep(_read(_MODULE_01_FILE), "6d")
        assert section is not None
        assert "support@senzing.com" in section
        assert "**Checkpoint:** Write step 6d to `config/bootcamp_progress.json`." in section


# ===========================================================================
# Security preservation — no MCP URL, no external URL in edited regions
# **Validates: Requirements 3.5**
# ===========================================================================

_PROTO_RE = re.compile(r"htt" + r"ps?://")


def _edited_regions() -> dict[str, str]:
    """Return the three regions the fix edits (5a, 5c 'no license', 6d)."""
    m2 = _read(_MODULE_02_FILE)
    m1 = _read(_MODULE_01_FILE)
    regions = {
        "module2_5a": _extract_5a(m2),
        "module2_5c_no_license": _extract_5c_no_license(m2),
        "module1_6d": _extract_m1_substep(m1, "6d"),
    }
    assert all(v is not None for v in regions.values()), "Failed to extract an edited region"
    return {k: v for k, v in regions.items() if v is not None}


class TestSecurityPreservation:
    """The edited regions introduce no MCP server URL and no external URL.

    Holds on UNFIXED code (the regions have no URLs) and must remain true after
    the additive fix. EXPECTED OUTCOME on UNFIXED code: PASS."""

    def test_no_external_url_in_edited_regions(self) -> None:
        """**Validates: Requirements 3.5** — no http/https URL in edited regions."""
        for name, region in _edited_regions().items():
            assert _PROTO_RE.search(region) is None, (
                f"Edited region '{name}' must not contain an external URL"
            )

    def test_no_mcp_server_url_in_edited_regions(self) -> None:
        """**Validates: Requirements 3.5** — no MCP server URL/host in edited regions."""
        url = _mcp_server_url()
        host = _mcp_server_host()
        for name, region in _edited_regions().items():
            assert url not in region, f"Edited region '{name}' must not contain the MCP URL"
            assert host not in region, f"Edited region '{name}' must not contain the MCP host"

    def test_no_mcp_server_url_anywhere_in_steering_files(self) -> None:
        """**Validates: Requirements 3.5** — neither steering file contains the MCP URL."""
        host = _mcp_server_host()
        for path in (_MODULE_01_FILE, _MODULE_02_FILE):
            assert host not in _read(path), (
                f"{path.name} must not contain the MCP server host (mcp.json is the source)"
            )


# ===========================================================================
# Property-based preservation — non-bug situations leave invariants unchanged
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**
# ===========================================================================


class TestPreservationProperty:
    """For all NOT is_bug_condition(x) situations, the snapshotted invariants
    and sufficient-license paths are byte-identical to baseline (F(X) = F'(X)).

    EXPECTED OUTCOME on UNFIXED code: PASS."""

    @given(situation=st_license_situation())
    @settings(max_examples=20)
    def test_non_bug_situations_preserve_all_baselines(
        self, situation: LicenseSituation
    ) -> None:
        """**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.6**

        For any non-bug situation, every snapshotted preserved region matches
        baseline. (Preserved content does not vary by X — preservation is the
        invariant.) Bug-condition situations are out of scope for this property.
        """
        if is_bug_condition(situation):
            return

        for key, expected in _BASELINE_HASHES.items():
            actual = _sha256(_current_region(key))
            assert actual == expected, (
                f"Non-bug situation {situation} altered region '{key}'.\n"
                f"Expected: {expected}\nActual:   {actual}"
            )

    @given(situation=st_license_situation())
    @settings(max_examples=20)
    def test_sufficient_license_paths_specifically_preserved(
        self, situation: LicenseSituation
    ) -> None:
        """**Validates: Requirements 3.1, 3.2**

        When records <= 500, the Module 1 Step 6a skip path is preserved; when a
        sufficient license is present, the Module 2 Step 5c 'has license'
        branches are preserved.
        """
        if is_bug_condition(situation):
            return

        if situation.total_record_count <= 500:
            actual = _sha256(_current_region("m1_6a"))
            assert actual == _BASELINE_HASHES["m1_6a"], (
                "Module 1 Step 6a skip-to-Step-7 path must be preserved for <= 500 records"
            )

        if situation.has_sufficient_license:
            actual = _sha256(_current_region("m2_5c_has_license"))
            assert actual == _BASELINE_HASHES["m2_5c_has_license"], (
                "Module 2 Step 5c 'has license' branches must be preserved"
            )

    @given(situation=st_license_situation())
    @settings(max_examples=20)
    def test_security_invariant_holds_for_non_bug_situations(
        self, situation: LicenseSituation
    ) -> None:
        """**Validates: Requirements 3.5** — no MCP/external URL in edited regions."""
        if is_bug_condition(situation):
            return
        host = _mcp_server_host()
        for region in _edited_regions().values():
            assert _PROTO_RE.search(region) is None
            assert host not in region
