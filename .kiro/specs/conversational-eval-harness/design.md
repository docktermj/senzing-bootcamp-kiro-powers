# Design Document: Conversational Eval Harness

## Overview

The conversational-eval-harness adds a **runtime-transcript** verification layer to the
Senzing Bootcamp Power. The existing ~2,600 tests parse steering markdown and assert that
strings or markers are *present* ("does the file say X?"). They prove the instructions are
authored correctly; they do not prove that an agent *following* those instructions behaves
correctly at runtime. Behavioral regressions — the prose-only MCP licensing gap and the
Module 3 visualization skip escape-hatch, both fixed recently — can pass the entire existing
suite because the broken behavior only manifests in a live conversation.

This feature lets maintainers author **scripted transcripts** (fixtures) of an agent /
bootcamper exchange. Each agent turn carries declarative **behavioral assertions** describing
the moves the agent must make at decision points (👉 questions, ⛔ gates, module transitions,
licensing branches). A stdlib-only **checker** (`eval_conversations.py`) loads the fixtures and
evaluates the assertions against the recorded agent-turn text, then reports pass/fail with an
exit code CI can gate on.

The harness is **offline and deterministic**. It never calls an LLM or the Senzing MCP server.
It evaluates *recorded* transcripts authored by maintainers against declarative assertions.
Generating fresh transcripts from a live model is explicitly out of scope for the automated
suite; it is described only as an optional manual authoring step that produces a fixture which
is then version-controlled and evaluated (Requirement 8).

The feature ships entirely inside the power directory tree and consists of four parts:

1. **Fixture format** — a JSON scenario format under `senzing-bootcamp/tests/eval/` (Requirements 1, 2).
2. **Checker/runner** — `senzing-bootcamp/scripts/eval_conversations.py`, stdlib-only, `main(argv=None)`, argparse, exit 0/1 (Requirements 4–8, 11).
3. **Starter scenario set** — four shipped fixtures encoding expected behavior as the oracle (Requirement 10).
4. **Tests** — `senzing-bootcamp/tests/test_eval_conversations.py` (+ property strategies), pytest + Hypothesis (Requirement 12).

### Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Fixture serialization | **JSON** (`.json`) parsed with stdlib `json` | `json` is in the standard library, has zero ambiguity, and round-trips losslessly. YAML would require either PyYAML (banned for non-exception scripts per `tech.md`) or a hand-rolled minimal-YAML parser, which adds parsing risk and a maintenance burden the harness does not need. JSON fully satisfies "stdlib-parseable, no third-party dependency" (R1.1, R11.1). |
| Fixture directory | `senzing-bootcamp/tests/eval/` | Fixed by `structure.md` and Requirement 11.3 / 1.5; keeps fixtures with the test artifacts that ship with the power. |
| Script location | `senzing-bootcamp/scripts/eval_conversations.py` | `structure.md` places all Python CLI tools in `scripts/`; matches the `main(argv=None)` + argparse convention (R11.2). |
| Detection heuristics | **Reuse** `validate_behavior_rules.py` patterns (`CONJUNCTION_PATTERNS`, pointer detection, `is_compound_question`) and the `🛑 STOP` / "end your response" heuristics from `test_self_answering_questions_bug.py` | Requirement 9.3 forbids relocating, duplicating, or modifying enforcement logic. The harness *re-implements the same regex vocabulary* for transcript text (a different input domain than steering files) and documents the shared lineage, rather than importing the steering-file validator wholesale. The patterns themselves are copied as module constants so the two layers stay independently testable. |
| Assertion extensibility | `type` → predicate **registry dict** | Adding an assertion type is a one-line registry entry; unknown types raise a schema error (R4). |
| Failure handling | **Collect-all**, report every failure | A single run surfaces all behavioral regressions, not just the first (R6.1). |

## Architecture

The checker is a single-file pipeline: **load → validate schema → evaluate → report → exit**.

```mermaid
flowchart TD
    A["main(argv=None)"] --> B["argparse: --fixtures-dir / path"]
    B --> C["load_scenarios(target)"]
    C -->|"json.JSONDecodeError"| E1["ParseError -> stderr, exit 1"]
    C -->|"no fixtures found"| E2["EmptyDirError -> stderr, exit 1"]
    C --> D["parse_scenario(raw) -> Scenario"]
    D -->|"missing field / bad role /\nbootcamper has assertions /\nunknown assertion type"| E3["SchemaError -> stderr, exit 1"]
    D --> F["evaluate_scenario(scenario)"]
    F --> G["for each Agent_Turn:\nevaluate_turn(turn, context)"]
    G --> H["registry[type](turn, context, params)\n-> AssertionOutcome"]
    H --> I["collect EvalFailure list"]
    I --> J["print summary:\nscenarios / assertions / failures"]
    J -->|"0 failures"| K["exit 0"]
    J -->|">=1 failure"| L["failures -> stderr, exit 1"]
```

### Layered responsibilities

```mermaid
flowchart LR
    subgraph Layer1["String-presence tests (~2,600)"]
        S1["Parse steering markdown\nAssert marker PRESENT"]
    end
    subgraph Layer2["governance-rule-conformance (static)"]
        S2["Assert each rule is WIRED\nto its enforcement point"]
    end
    subgraph Layer3["conversational-eval-harness (this feature)"]
        S3["Assert a RECORDED conversation\nHONORS the behavioral rule"]
    end
    S1 -. complements .-> S3
    S2 -. complements .-> S3
```

The three layers are independent and non-overlapping (Requirement 9): string-presence tests
verify the steering *says* the rule, governance-rule-conformance verifies the rule is *wired*
to an enforcement point, and this harness verifies a recorded conversation *honors* the rule.
The harness reads only fixtures — it never reads, relocates, or mutates steering files, hooks,
or other scripts (R9.3).

### Control-flow notes

- **No network, no LLM, no MCP** (R8.1, R8.2). The checker imports only stdlib modules
  (`argparse`, `json`, `re`, `sys`, `pathlib`, `dataclasses`, `collections`). There is no
  socket, `urllib`, or subprocess use anywhere in the evaluation path.
- **Determinism** (R8.4, R3.10). Every predicate is a pure function of `(turn_text, prior_turns, params)`.
  No randomness, clock, filesystem, or environment reads occur during evaluation, so repeated
  runs over unchanged fixtures yield identical results and exit codes.
- **Collect-all** (R6.1, R6.5). `evaluate_scenario` evaluates every assertion on every agent
  turn before returning; the runner aggregates failures across all fixtures and prints a single
  summary line.

## Components and Interfaces

All components live in `senzing-bootcamp/scripts/eval_conversations.py` unless noted.

### Module layout

```text
senzing-bootcamp/
├── scripts/
│   └── eval_conversations.py        # The_Checker (stdlib-only)
└── tests/
    ├── eval/                        # Eval_Directory — shipped fixtures (R1.5, R11.3)
    │   ├── single_question_stop.json
    │   ├── module3_gate_not_bypassed.json
    │   ├── module_transition_completeness.json
    │   └── license_insufficient_search_docs.json
    └── test_eval_conversations.py   # pytest + Hypothesis (R12)
```

### 1. Detection heuristics (pure helpers)

These mirror the vocabulary already proven in `validate_behavior_rules.py` and
`test_self_answering_questions_bug.py`, re-expressed for free-form transcript text. They are
module-level constants + functions so the test layer can property-test each in isolation.

```python
POINTER = "\U0001f449"          # the pointer marker
HARD_STOP = re.compile(r"\U0001f6d1\s*STOP", re.IGNORECASE)  # hard-stop marker + STOP

# Reused verbatim from validate_behavior_rules.CONJUNCTION_PATTERNS (lineage documented).
CONJUNCTION_PATTERNS: list[str] = [
    r"\bor\b(?!\s*$)",
    r"\balternatively\b",
    r"\bor would you rather\b",
    r"\bor should we\b",
    r"\bor would you prefer\b",
    r"\bor if you prefer\b",
]

def count_pointers(text: str) -> int: ...
def pointer_question_line(text: str) -> str | None: ...      # first line containing pointer + "?"
def has_conjunction(text: str) -> bool: ...                  # any CONJUNCTION_PATTERNS match
def count_question_marks(text: str) -> int: ...
def text_after(text: str, marker_line: str) -> str: ...      # substantive content after a line
```

### 2. Assertion predicates

Each predicate has the signature
`Predicate = Callable[[Turn, EvalContext, dict[str, object]], AssertionOutcome]`
where `EvalContext` exposes the surrounding transcript (prior + later turns) for assertions
that need it (`gate_not_bypassed`). Each returns an `AssertionOutcome(passed: bool, message: str)`;
`message` is empty on pass and a specific human-readable reason on failure (R6.4).

| Assertion type | Param(s) | Passes when | Failure message (example) |
|---|---|---|---|
| `exactly_one_pointer` | — | `count_pointers(content) == 1` | `"expected exactly one pointer, found {n}"` |
| `ends_with_question_then_stop` | — | content contains a pointer question line AND nothing substantive follows it (only whitespace, a hard-stop block, or blank lines) AND no simulated bootcamper reply follows | `"substantive agent content follows the pointer question: {snippet!r}"` |
| `no_compound_question` | — | `count_question_marks(content) <= 1` AND `not has_conjunction(content)` | `"compound question detected (conjunction joins alternatives): {line!r}"` |
| `no_self_answer` | — | no agent-authored answer follows the pointer question in the same turn (no declarative sentence after the question line; reuses the hard-stop / "end your response" boundary heuristic) | `"agent appears to answer its own question: {snippet!r}"` |
| `contains_marker` | `marker: str` | `params["marker"] in content` | `"expected marker {marker!r} not found in turn"` |
| `absent_marker` | `marker: str` | `params["marker"] not in content` | `"prohibited marker {marker!r} present in turn"` |
| `mentions_tool` | `tool: str` | `params["tool"]` appears in content (word-boundary match) | `"expected tool {tool!r} not mentioned in turn"` |
| `transition_response_completeness` | — | content contains a banner marker, a journey-map marker, a before/after marker, a first-step marker, AND `len(content) > 50` | `"transition incomplete: missing {missing}; length={n}"` |
| `gate_not_bypassed` | `step: str` (e.g. `"3.9"`) | the turn shows the gate was executed (gate marker/checkpoint present) AND contains no skip/bypass offer for that gate | `"gate {step} bypassed: skip/bypass offer present"` / `"gate {step} not shown as executed"` |

Parameters are supplied in the fixture under the assertion object's named fields (R2.6),
e.g. `{"type": "contains_marker", "marker": "..."}`. A predicate that requires a parameter and
does not find it raises a `SchemaError` during validation (not at evaluation time).

#### Predicate detail: `ends_with_question_then_stop` (R3.2)

1. Find the last line containing the pointer and a `?`. If none -> fail (`"no pointer question found"`).
2. Take everything after that line. Strip whitespace, the hard-stop directive block, and blank lines.
3. If the remainder is empty -> pass. If the remainder contains a `bootcamper:`-style simulated
   reply or any other prose -> fail. This encodes the "STOP after a pointer question and wait" rule
   and forbids the agent continuing past its own question within one turn.

#### Predicate detail: `no_self_answer` (R3.4)

Mirrors the self-answering anti-pattern in `conversation-protocol.md` (the agent asking
"Who will be working on this project?" then writing "I'll assume it's just you for now."). After
the pointer question line, if a declarative agent sentence (one that is not itself a pointer
question and not a hard-stop / "end your response" directive) appears, the turn self-answers ->
fail. The hard-stop + "end your response" directive is treated as a boundary, not as a
self-answer, matching the steering's CORRECT example.

#### Predicate detail: `gate_not_bypassed` (R3.9, R10.2)

Context-aware. For a turn that advances past the Module 3 Step 9 visualization gate:

- **Executed evidence**: the gate's own markers/checkpoints are present (e.g. the
  hard-stop guided-tour boundary, the `module_3_verification` checkpoint reference, or the
  "Your visualization is running" delivery line). At least one execution marker must be present.
- **No bypass offer**: the turn must contain no skip/bypass language framed as an *offer* for
  that gate (no "skip Phase 2", no "move on to Module 4" before the gate completes).

Both conditions must hold to pass.

### 3. Assertion registry (Requirement 4)

```python
REGISTRY: dict[str, Predicate] = {
    "exactly_one_pointer": _exactly_one_pointer,
    "ends_with_question_then_stop": _ends_with_question_then_stop,
    "no_compound_question": _no_compound_question,
    "no_self_answer": _no_self_answer,
    "contains_marker": _contains_marker,
    "absent_marker": _absent_marker,
    "mentions_tool": _mentions_tool,
    "transition_response_completeness": _transition_response_completeness,
    "gate_not_bypassed": _gate_not_bypassed,
}

REQUIRED_PARAMS: dict[str, tuple[str, ...]] = {
    "contains_marker": ("marker",),
    "absent_marker": ("marker",),
    "mentions_tool": ("tool",),
    "gate_not_bypassed": ("step",),
}
```

- `resolve(type_name)` looks up `REGISTRY`; a miss raises `SchemaError` naming the scenario,
  the turn index, and the unknown type (R4.2).
- A new assertion type is added by writing a predicate function and adding one `REGISTRY`
  entry (plus a `REQUIRED_PARAMS` entry if parameterized) — no change to existing predicate
  evaluation (R4.3).
- Each type's name, purpose, and parameters are documented in the module docstring and the
  table above (R4.4).

### 4. Loading and validation (Requirements 2, 5)

```python
def load_scenarios(target: Path) -> list[Scenario]:
    """Load and validate one fixture file or every *.json in a directory.

    Raises:
        ParseError: a fixture cannot be parsed by json (R5.3).
        EmptyDirError: a directory contains no fixtures (R5.4).
        SchemaError: a fixture violates the R1/R2 structure (R5.5, R2.4, R2.7, R4.2).
    """

def parse_scenario(raw: dict, source: Path) -> Scenario: ...
```

- No path arg -> load every `*.json` in the Eval_Directory (R5.1); a single path -> load only
  that file (R5.2).
- Each file is parsed with `json.loads`; a `json.JSONDecodeError` becomes a `ParseError` naming
  the file (R5.3).
- Validation runs *before* evaluation (R5.5): every turn must have `role` in {`agent`,
  `bootcamper`} and a string `content` (R2.1, R2.2, R2.7); a `bootcamper` turn carrying
  `assertions` is an error (R2.4); each assertion `type` must resolve in the registry (R4.1, R4.2);
  required params must be present (R2.6).

### 5. Evaluation and reporting (Requirements 6, 7)

```python
def evaluate_turn(turn: Turn, ctx: EvalContext) -> list[EvalFailure]: ...
def evaluate_scenario(scenario: Scenario) -> list[EvalFailure]: ...
def run(target: Path) -> int:          # returns exit code
    ...
def main(argv: list[str] | None = None) -> int: ...
```

- `evaluate_scenario` evaluates **every** assertion on **every** agent turn and accumulates
  `EvalFailure`s (R6.1); passing assertions are counted for the summary (R6.2).
- Each `EvalFailure` records `scenario_id`, `turn_index`, `assertion_type`, and `message`
  (R6.3, R6.4).
- After all fixtures, the runner prints a summary to stdout — scenarios evaluated, assertions
  evaluated, failures (R6.5) — and prints each failure to **stderr** (R6.3).
- Exit `0` when all pass (R7.1); exit `1` on any assertion failure (R7.2) or any
  parse/schema error (R7.3, R5.3, R5.4). `main` is argparse-driven with `main(argv=None)` (R7.4, R11.2).

### CLI

```text
usage: eval_conversations.py [-h] [--fixtures-dir DIR] [path]

positional arguments:
  path                  Optional single fixture file to evaluate (R5.2).

options:
  --fixtures-dir DIR    Directory of fixtures (default: senzing-bootcamp/tests/eval) (R5.1).
```

## Data Models

All structures are stdlib `@dataclass` instances (R11.2). Type hints use `X | None` and
`list[str]` forms (`python-conventions.md`).

```python
@dataclass(frozen=True)
class AssertionSpec:
    """One declarative behavioral assertion attached to an agent turn."""
    type: str                       # Assertion_Type name (R2.5)
    params: dict[str, object]       # named params, e.g. {"marker": "..."} (R2.6)

@dataclass(frozen=True)
class Turn:
    """A single transcript entry."""
    role: str                       # "agent" | "bootcamper" (R2.1)
    content: str                    # turn text (R2.2)
    assertions: list[AssertionSpec] # empty for bootcamper turns (R2.3, R2.4)

@dataclass(frozen=True)
class Scenario:
    """One conversational scenario loaded from a fixture file."""
    scenario: str                   # non-empty id (R1.2)
    description: str                # human-readable (R1.3)
    turns: list[Turn]               # ordered, >= 1 (R1.4)
    rule_ref: str | None            # governing rule/source, if referenced (R1.6)
    source: Path                    # originating file (for error messages)

@dataclass(frozen=True)
class AssertionOutcome:
    """Result of evaluating one predicate."""
    passed: bool
    message: str                    # "" on pass; reason on fail (R6.4)

@dataclass(frozen=True)
class EvalFailure:
    """A failed assertion, fully attributed for the Failure_Report (R6.3)."""
    scenario_id: str
    turn_index: int
    assertion_type: str
    message: str

class EvalError(Exception):
    """Base class for fixture-validity / parse errors (exit 1)."""

class ParseError(EvalError):    """Fixture not JSON-parseable (R5.3)."""
class EmptyDirError(EvalError): """No fixtures found (R5.4)."""
class SchemaError(EvalError):   """Structural / unknown-type violation (R2.4, R2.7, R4.2)."""
```

### Fixture schema (JSON)

```text
Scenario_Fixture (object)
├── scenario     : string (non-empty)            # R1.2
├── description  : string                          # R1.3
├── rule_ref     : string (optional)              # R1.6
└── turns        : array[Turn] (>= 1)             # R1.4
        Turn (object)
        ├── role        : "agent" | "bootcamper"  # R2.1
        ├── content     : string                   # R2.2
        └── assertions  : array[Assertion] (agent turns only; optional)  # R2.3, R2.4
                Assertion (object)
                ├── type   : string (registry name)   # R2.5
                └── <param fields> : e.g. "marker", "tool", "step"  # R2.6
```

The loader maps the JSON object to `Scenario`; any field other than `type` on an assertion
object is collected into `AssertionSpec.params`.

### Annotated example fixture — single-question / pointer / STOP / no-self-answer (R10.1)

`senzing-bootcamp/tests/eval/single_question_stop.json`

```json
{
  "scenario": "single_question_stop",
  "description": "Agent asks exactly one pointer question, stops, does not self-answer or compound. Exercises Rule 4 (pointer), One Question Rule, Question Stop Protocol, Self-Answering anti-pattern.",
  "rule_ref": "conversation-protocol.md#one-question-rule; agent-behavior-rules.md#rule-4",
  "turns": [
    {
      "role": "bootcamper",
      "content": "Tell me about the problem you're trying to solve."
    },
    {
      "role": "agent",
      "content": "Got it — let's capture your data sources.\n\n👉 How many distinct data sources or systems will we be working with?\n\n🛑 STOP — End your response here and wait for the bootcamper's real input.",
      "assertions": [
        {"type": "exactly_one_pointer"},
        {"type": "ends_with_question_then_stop"},
        {"type": "no_compound_question"},
        {"type": "no_self_answer"},
        {"type": "contains_marker", "marker": "🛑"}
      ]
    }
  ]
}
```

This fixture encodes the EXPECTED behavior as the oracle (R10.6): one pointer, a STOP boundary,
no second question mark, no conjunction, no self-answer. A regression that, say, appended
"I'll assume three for now." after the question would flip `ends_with_question_then_stop` and
`no_self_answer` to failing.

### Annotated example fixture — Module 3 Step 9 gate (R10.2)

`senzing-bootcamp/tests/eval/module3_gate_not_bypassed.json`

```json
{
  "scenario": "module3_step9_gate_not_bypassed",
  "description": "At Module 3 Step 9, the agent executes the mandatory visualization gate and never offers to skip it. Exercises Governing Rule 15 / NON_SKIPPABLE_GATES {'3.9'}.",
  "rule_ref": "module-03-phase2-visualization.md#step-9; validate_mandatory_gates.py NON_SKIPPABLE_GATES",
  "turns": [
    {
      "role": "bootcamper",
      "content": "Phase 1 verification all passed. What's next?"
    },
    {
      "role": "agent",
      "content": "Phase 2 visualization is mandatory, so I'll generate it now. Your visualization is running — open the local URL in your browser.\n\n🗺️ What You're Looking At — A Quick Tour ... (Entity Graph, Merge Statistics) ...\n\nCheckpoint written: module_3_verification.web_service = passed.\n\n👉 Take your time exploring the visualization. Let me know when you're ready and I'll continue with cleanup.\n\n🛑 STOP — End your response here and wait for the bootcamper to confirm they are done exploring.",
      "assertions": [
        {"type": "gate_not_bypassed", "step": "3.9"},
        {"type": "absent_marker", "marker": "skip Phase 2"},
        {"type": "exactly_one_pointer"},
        {"type": "ends_with_question_then_stop"}
      ]
    }
  ]
}
```

Here `gate_not_bypassed` passes because the turn shows the gate executed (the "visualization is
running" delivery line + the `module_3_verification` checkpoint reference) and contains no
skip/bypass offer. The `absent_marker` assertion guards against the exact "skip Phase 2"
escape-hatch that was the regression.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions
of a system — essentially, a formal statement about what the system should do. Properties serve
as the bridge between human-readable specifications and machine-verifiable correctness
guarantees.*

The harness is a strong fit for property-based testing: every assertion predicate is a **pure
function over text**, the loader/validator is a **pure function over JSON**, and the runner's
exit code is a **deterministic function of the collected failures**. The input space (arbitrary
turn text, arbitrary fixtures) is large and varied, so generated inputs reveal edge cases that
hand-written examples miss. The properties below were derived from the prework analysis and
consolidated to remove redundancy (e.g. `contains_marker`/`absent_marker` merged into one
marker-presence property; predicate-level and runner-level determinism merged into one).

### Property 1: Valid fixtures round-trip into a Scenario

*For any* JSON object that conforms to the fixture schema (non-empty `scenario`, string
`description`, `turns` list with at least one turn, each turn a valid role + string content,
agent turns optionally carrying registered assertions, optional `rule_ref`), `parse_scenario`
SHALL return a `Scenario` whose fields equal the input values and whose turns and assertions are
preserved in order.

**Validates: Requirements 1.2, 1.3, 1.4, 1.6, 2.1, 2.2, 2.3**

### Property 2: Structurally invalid fixtures are rejected with an attributed schema error

*For any* fixture that violates the structure — a turn missing `role` or `content`, a turn whose
`role` is neither `agent` nor `bootcamper`, a `bootcamper` turn carrying a non-empty `assertions`
list, or an assertion whose `type` is not in the registry — the checker SHALL raise a
`SchemaError` whose message names the scenario identifier, the offending turn index, and (for an
unknown type) the unknown `type` string, and SHALL NOT evaluate any assertion for that fixture.

**Validates: Requirements 2.4, 2.7, 4.1, 4.2, 5.5**

### Property 3: `exactly_one_pointer` soundness

*For any* agent-turn text, the `exactly_one_pointer` predicate SHALL pass if and only if the
count of pointer occurrences in the text equals exactly one.

**Validates: Requirements 3.1, 12.3**

### Property 4: `ends_with_question_then_stop` soundness

*For any* agent-turn text that ends with a pointer question (optionally followed only by
whitespace or a hard-stop directive block), the predicate SHALL pass; and *for any* such text to
which substantive agent prose or a simulated reply is appended after the question, the predicate
SHALL fail.

**Validates: Requirements 3.2**

### Property 5: `no_compound_question` soundness

*For any* agent-turn text containing at most one question mark and no prose conjunction joining
alternatives, the `no_compound_question` predicate SHALL pass; and *for any* text containing two
question alternatives joined by a prose conjunction (for example "or", "alternatively", "or would
you rather", "or should we"), it SHALL fail.

**Validates: Requirements 3.3, 12.4**

### Property 6: `no_self_answer` soundness

*For any* agent-turn text consisting of a pointer question followed only by a hard-stop /
"end your response" boundary, the `no_self_answer` predicate SHALL pass; and *for any* such text
to which a declarative agent sentence answering the question is appended after the question line,
it SHALL fail.

**Validates: Requirements 3.4**

### Property 7: Marker-presence soundness (`contains_marker` / `absent_marker`)

*For any* agent-turn text and *any* marker string, `contains_marker` SHALL pass if and only if
the marker is a substring of the text, and `absent_marker` SHALL pass if and only if the marker
is not a substring of the text (the two predicates are exact logical complements for the same
inputs).

**Validates: Requirements 3.5, 3.6**

### Property 8: `mentions_tool` soundness

*For any* agent-turn text and *any* tool name, the `mentions_tool` predicate SHALL pass if and
only if the tool name occurs as a token in the text.

**Validates: Requirements 3.7**

### Property 9: `transition_response_completeness` soundness

*For any* agent-turn text that contains all four required transition markers (module banner,
journey map, before/after framing, first-step content) and has length greater than 50 characters,
the predicate SHALL pass; and *for any* text missing at least one required marker or with length
at most 50 characters, it SHALL fail.

**Validates: Requirements 3.8**

### Property 10: `gate_not_bypassed` soundness

*For any* agent turn that advances past the named Gate step and shows the gate was executed
(an execution marker or checkpoint reference present) with no skip/bypass offer for that gate,
the predicate SHALL pass; and *for any* such turn to which a skip/bypass offer is added, or from
which all execution evidence is removed, it SHALL fail.

**Validates: Requirements 3.9**

### Property 11: Evaluation completeness

*For any* valid Scenario_Fixture, the checker SHALL evaluate exactly one assertion result for
every assertion attached to every agent turn — the total number of assertion results equals the
total number of assertions across all agent turns in the transcript.

**Validates: Requirements 6.1, 6.2**

### Property 12: Failure attribution

*For any* assertion that fails, the resulting `EvalFailure` SHALL carry the correct scenario
identifier, the correct turn index, the failing assertion type, and a non-empty human-readable
message.

**Validates: Requirements 6.3, 6.4**

### Property 13: Exit-code contract

*For any* set of loaded fixtures that parse and validate successfully, the checker SHALL exit
with code 0 if and only if zero assertions fail, and exit with code 1 if at least one assertion
fails.

**Validates: Requirements 7.1, 7.2**

### Property 14: Determinism

*For any* fixed set of Scenario_Fixtures, evaluating them more than once without changes SHALL
produce identical assertion results, an identical list of failures, and an identical exit code on
each run.

**Validates: Requirements 3.10, 8.4**

### Property 15: Shipped fixtures pass (self-consistency oracle)

*For any* fixture shipped in the starter set under `senzing-bootcamp/tests/eval/`, the checker
SHALL report all of its assertions as passing, and a full run over the starter set SHALL exit
with code 0.

**Validates: Requirements 10.5, 10.6, 12.1**

### Property 16: Malformed fixtures raise a parse error

*For any* fixture file whose bytes are not parseable by the stdlib JSON loader, the checker SHALL
raise a `ParseError` naming the file and SHALL exit with code 1.

**Validates: Requirements 5.3, 7.3, 12.6**

### Property 17: Fixtures contain no MCP URL or secrets

*For any* fixture shipped under `senzing-bootcamp/tests/eval/`, the fixture content SHALL contain
no MCP server URL and no secret/credential/PII pattern.

**Validates: Requirements 11.4**

## Starter Scenario Set (Requirement 10)

The harness ships four fixtures under `senzing-bootcamp/tests/eval/`, each encoding the EXPECTED
agent behavior as the oracle (R10.6). The first two are shown in full above (Data Models); the
remaining two are described here.

| Fixture | Rule exercised | Assertion types | Requirement |
|---|---|---|---|
| `single_question_stop.json` | one-question / pointer prefix / STOP-and-wait / no self-answer | `exactly_one_pointer`, `ends_with_question_then_stop`, `no_compound_question`, `no_self_answer`, `contains_marker` | R10.1 |
| `module3_gate_not_bypassed.json` | Module 3 Step 9 mandatory visualization gate not skipped | `gate_not_bypassed` (`step="3.9"`), `absent_marker`, `exactly_one_pointer`, `ends_with_question_then_stop` | R10.2 |
| `module_transition_completeness.json` | module-transition completeness (banner + journey + before/after + first step) | `transition_response_completeness` | R10.3 |
| `license_insufficient_search_docs.json` | license-insufficient path consults `search_docs` | `mentions_tool` (`tool="search_docs"`) | R10.4 |

### `module_transition_completeness.json` (R10.3)

Encodes the Module Transition Protocol from `conversation-protocol.md`: after a
Transition_Confirmation the agent MUST produce a banner, journey map, before/after framing, and
the first step — never a bare acknowledgment ("." or a single word).

```json
{
  "scenario": "module_transition_completeness",
  "description": "After the bootcamper confirms readiness, the transition turn produces a full module start (banner + journey map + before/after + first step), not a bare acknowledgment. Exercises the Module Transition Protocol minimum-content requirement.",
  "rule_ref": "conversation-protocol.md#module-transition-protocol; module-transitions.md",
  "turns": [
    {"role": "bootcamper", "content": "Yes, ready for Module 2."},
    {
      "role": "agent",
      "content": "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nMODULE 2: SDK Setup\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n| Module | Name | Status |\n|--------|------|--------|\n| 1 | Business Problem | done |\n| 2 | SDK Setup | in progress |\n\nBefore: you have a documented problem but no working SDK. After: the Senzing SDK is installed and verified in your chosen language.\n\nStep 1 — Detect existing SDK. I'll start by checking whether the Senzing SDK is already installed so we don't reinstall it.",
      "assertions": [
        {"type": "transition_response_completeness"}
      ]
    }
  ]
}
```

A regression that replied with only "." or "Okay." after the confirmation would fail
`transition_response_completeness` on both the missing-markers check and the length check.

### `license_insufficient_search_docs.json` (R10.4)

Encodes the Module 1 Step 6d / Module 2 Step 5a–5c rule: when the current license is
insufficient (record count exceeds the 500-record evaluation limit), the agent must consult the
Senzing MCP server via `search_docs` before falling back to the email path.

```json
{
  "scenario": "license_insufficient_search_docs",
  "description": "When the bootcamper has no license and the dataset exceeds the 500-record evaluation limit, the agent consults search_docs for current guidance rather than relying on prose alone. Exercises Module 1 Step 6d / Module 2 Step 5a-5c.",
  "rule_ref": "module-01-business-problem.md#step-6d; module-02-sdk-setup.md#step-5",
  "turns": [
    {"role": "bootcamper", "content": "No, I don't have a Senzing license, and I have about 50,000 records."},
    {
      "role": "agent",
      "content": "Because your total record count exceeds the 500-record evaluation limit, the built-in license is insufficient. Let me consult the Senzing documentation for current guidance — calling search_docs(query='temporary or larger evaluation license for more than 500 records') to retrieve the latest options before we go further.\n\nHere is what the current guidance recommends, followed by the email request path to support.\n\n👉 Would you like to defer license configuration and continue with Module 1 now?\n\n🛑 STOP — End your response here and wait for the bootcamper's real input.",
      "assertions": [
        {"type": "mentions_tool", "tool": "search_docs"},
        {"type": "exactly_one_pointer"},
        {"type": "ends_with_question_then_stop"}
      ]
    }
  ]
}
```

A regression that explained licensing in prose only — the exact gap that was fixed recently —
would omit the `search_docs` call and fail `mentions_tool`.

## Relationship to Existing Verification Layers (Requirement 9)

The harness is a third, distinct verification layer. It complements — and does not replace or
modify — the existing layers (R9.1, R9.2, R9.3). The harness reads only fixtures; it never reads,
relocates, duplicates, or mutates steering files, hooks, or other scripts.

| Dimension | String-presence tests (~2,600) | governance-rule-conformance (static) | conversational-eval-harness (this feature) |
|---|---|---|---|
| Question answered | "Does the steering text *contain* this marker/string?" | "Is each governing rule *wired* to its declared enforcement point (file/hook/marker)?" | "Does a *recorded conversation* HONOR the behavioral rule at runtime?" |
| Input | Steering markdown files | Steering files + a `governance-rules.yaml` registry | Recorded transcript fixtures (JSON) |
| What it proves | The instruction is authored | The rule has a live enforcement linkage that hasn't drifted | An agent following the steering actually behaves correctly |
| Catches the licensing/gate regressions? | No — the prose can be present and still mis-behave | Partially — only if the linkage breaks | **Yes** — the transcript shows the missing `search_docs` call or the skip offer |
| Reads steering files? | Yes | Yes | **No** — fixtures only |
| Example | `assert "pointer" in module_text` | `assert "3.9" in NON_SKIPPABLE_GATES` | `assert gate_not_bypassed(turn, step="3.9")` |

The shared detection vocabulary (conjunction patterns, pointer detection) is **re-implemented**
as harness module constants rather than imported from `validate_behavior_rules.py`, so the
harness adds no coupling to the steering-file validator and the two remain independently
testable (R9.3). The documentation in the checker module docstring states the
"steering SAYS the rule" vs "a conversation HONORS the rule" distinction explicitly (R9.4).

## Error Handling

The checker distinguishes **fixture-validity / parse errors** (operator authored a bad fixture)
from **assertion failures** (the recorded behavior is wrong). Both exit `1`, but they are
reported differently.

| Condition | Raised / detected | Reported | Exit |
|---|---|---|---|
| File is not valid JSON | `ParseError` (from `json.JSONDecodeError`) | stderr: file path + JSON error position | 1 (R5.3, R7.3) |
| No fixtures in directory (no path arg) | `EmptyDirError` | stderr: "no fixtures found in {dir}" | 1 (R5.4, R7.3) |
| Turn missing `role`/`content`, or invalid `role` | `SchemaError` | stderr: scenario id + turn index | 1 (R2.7, R7.3) |
| Bootcamper turn carries assertions | `SchemaError` | stderr: scenario id + turn index | 1 (R2.4, R7.3) |
| Unknown assertion `type` | `SchemaError` | stderr: scenario id + turn index + unknown type | 1 (R4.2, R7.3) |
| Required assertion param missing | `SchemaError` | stderr: scenario id + turn index + type + missing param | 1 (R2.6, R7.3) |
| One or more assertions fail | collected `EvalFailure`s | stderr: per-failure scenario id + turn index + type + message | 1 (R6.3, R7.2) |
| All assertions pass | — | stdout summary | 0 (R7.1) |

- **Validation precedes evaluation** (R5.5): a fixture that is both schema-invalid and would
  fail an assertion reports the schema error and never reaches evaluation.
- **Collect-all** (R6.1): assertion failures within a successfully-loaded fixture set do not
  short-circuit; every assertion is evaluated and every failure is reported before exit.
- All diagnostics go to **stderr**; the summary line goes to **stdout**, so CI logs separate
  signal from detail (R6.3, R6.5).

## Testing Strategy

Property-based testing **applies** to this feature: the assertion predicates, the loader, and
the exit-code logic are pure functions with universal properties over a large input space. The
tests use **pytest + Hypothesis** (repository convention), stdlib-only otherwise, and live at
`senzing-bootcamp/tests/test_eval_conversations.py` with strategies in the same file (R11.3,
R12.5). The checker is imported via `sys.path` manipulation since scripts are not packages
(`python-conventions.md`):

```python
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
import eval_conversations as ec
```

### Dual approach

- **Property tests** (Hypothesis) cover the universal predicate/loader/runner properties (P1–P17),
  one property test per design property, each with a comment tag referencing the design property.
- **Unit / example tests** cover specific scenarios and edge cases that do not vary with input:
  load-all vs single-path loading (R5.1/R5.2), empty-directory (R5.4), summary output (R6.5),
  the `main(argv=None)` entry point (R7.4), the shipped-fixture presence + assertion-type checks
  (R10.1–R10.4), and the stdlib-only import audit (R8.1/R8.2/R11.1).

### Conventions (R12.5)

- Class-based organization (`class TestExactlyOnePointer:`, `class TestSchemaRejection:`, ...).
- Hypothesis strategies prefixed `st_` (e.g. `st_agent_turn_text`, `st_single_pointer_text`,
  `st_compound_question`, `st_valid_fixture`, `st_marker`).
- `from __future__ import annotations`; type hints use `X | None` and `list[str]` forms.
- `@settings(max_examples=20)` on every property test (R12.2) — note this is below the usual
  100-iteration default; it follows the explicit repository/requirements convention for this
  power.
- Each property test tagged: **Feature: conversational-eval-harness, Property {n}: {property text}**.

### Property to test mapping

| Property | Test focus | Key strategy | Requirements |
|---|---|---|---|
| P1 | valid fixture parses | `st_valid_fixture` | 1.2–1.6, 2.1–2.3 |
| P2 | schema rejection family | `st_invalid_fixture` (missing field / bad role / bootcamper-with-assertions / unknown type) | 2.4, 2.7, 4.1, 4.2, 5.5 |
| P3 | `exactly_one_pointer` (R12.3) | `st_text_with_n_pointers` | 3.1, 12.3 |
| P4 | `ends_with_question_then_stop` | `st_question_then_optional_suffix` | 3.2 |
| P5 | `no_compound_question` (R12.4) | `st_single_question`, `st_compound_question` | 3.3, 12.4 |
| P6 | `no_self_answer` | `st_question_then_optional_answer` | 3.4 |
| P7 | marker presence (contains/absent) | `st_text`, `st_marker` | 3.5, 3.6 |
| P8 | `mentions_tool` | `st_text`, `st_tool` | 3.7 |
| P9 | `transition_response_completeness` | `st_transition_turn` (drop-one-marker variants) | 3.8 |
| P10 | `gate_not_bypassed` | `st_gate_turn` (+ skip-offer / drop-evidence variants) | 3.9 |
| P11 | evaluate-all completeness | `st_fixture_with_known_count` | 6.1, 6.2 |
| P12 | failure attribution | `st_failing_turn` | 6.3, 6.4 |
| P13 | exit-code contract | `st_mixed_fixture_set` | 7.1, 7.2 |
| P14 | determinism | `st_fixture_set` (run twice) | 3.10, 8.4 |
| P15 | shipped fixtures pass (oracle) | enumerate `tests/eval/*.json` | 10.5, 10.6, 12.1 |
| P16 | malformed -> ParseError + exit 1 | `st_non_json_bytes` | 5.3, 7.3, 12.6 |
| P17 | fixtures: no MCP URL/secrets | enumerate `tests/eval/*.json` | 11.4 |

### Required negative tests (R12.6)

`TestSchemaRejection` and `TestParseError` include explicit cases that an unknown assertion type
and a malformed (non-JSON) fixture each cause the checker to report an error and exit `1`,
satisfying R12.6 directly (in addition to the P2 and P16 properties).

### Out of scope

No test calls an LLM, the MCP server, or any network resource (R8.1, R8.2). There is no test for
"live transcript generation" — that is explicitly out of scope for the automated suite (R8.3).
Performance (R11.5, "a few seconds") is not asserted as a hard timing test; the stdlib-only,
in-memory design makes it inherent, and a coarse smoke check may be added if desired.

## Requirements Mapping

| Req | Summary | Design coverage |
|---|---|---|
| 1 | Scenario fixture format (stdlib-parseable JSON) | Overview decision table; Data Models (fixture schema); P1 |
| 2 | Turn structure + assertion attachment | Data Models (`Turn`, `AssertionSpec`); loading/validation; P1, P2 |
| 3 | Starter assertion vocabulary | Components §2 (predicate table + details); P3–P10, P14 |
| 4 | Assertion extensibility (registry) | Components §3 (registry + `REQUIRED_PARAMS`); P2 |
| 5 | Checker loading behavior | Components §4; Error Handling; P16; example tests (5.1/5.2/5.4) |
| 6 | Assertion evaluation + reporting | Components §5; Error Handling; P11, P12; summary example test |
| 7 | Exit codes + `main(argv=None)` | Components §5 + CLI; P13; `main` example test |
| 8 | Offline + deterministic | Overview control-flow notes; P14; import-audit smoke test |
| 9 | Relationship to existing layers | Architecture (layer diagram) + Relationship table |
| 10 | Starter scenario set | Data Models (2 fixtures) + Starter Scenario Set (2 fixtures); P15 |
| 11 | Non-functional (stdlib, convention, placement, no secrets, fast) | Overview decisions; Module layout; P17; convention smoke tests |
| 12 | Test coverage (pytest + Hypothesis) | Testing Strategy (property to test mapping, conventions, R12.6 negatives) |

## CI Wiring (Recommended, Optional)

CI wiring is an optional concern (Requirement 8 / Introduction "optional fifth concern"). The
recommended integration adds one step to `.github/workflows/validate-power.yml`, alongside the
existing `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, and
`sync_hook_registry.py --verify` steps, before pytest:

```yaml
- name: Conversational eval harness
  run: python senzing-bootcamp/scripts/eval_conversations.py
```

Because the checker exits `0` only when all shipped fixtures pass (Property 15) and `1` on any
behavioral regression or fixture error, the CI job gates on behavioral conformance. The step is
fully offline and deterministic, so it adds no flakiness and no network dependency. The same
behavior is also exercised by the pytest layer (P15), so teams that prefer a single test entry
point can rely on pytest alone and treat the dedicated CI step as optional.
