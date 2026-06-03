"""Property-based tests for agent behavior rules validation functions.

Validates correctness properties of the detection and validation functions
in validate_behavior_rules.py using Hypothesis strategies.

Feature: agent-behavior-rules
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path setup — import validation script via sys.path manipulation
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from validate_behavior_rules import (  # noqa: E402
    CONTENT_FREE_PHRASES,
    CONTINUATION_PHRASES,
    contains_pause_language,
    has_pointer_prefix,
    is_compound_question,
    is_continuation_request,
    validate_acknowledgment,
)

# ---------------------------------------------------------------------------
# Constants for strategies
# ---------------------------------------------------------------------------

# Explicit pause phrases that match PAUSE_PATTERNS regexes
_PAUSE_PHRASES: list[str] = [
    "take a break",
    "pause",
    "stop here",
    "pick this up later",
    "continue later",
    "continue tomorrow",
    "continue next time",
    "continue in a new session",
    "call it a day",
    "wrap up for now",
    "save progress for later",
]

# Words that do NOT match any pause pattern — safe filler words
_SAFE_WORDS: list[str] = [
    "hello",
    "world",
    "the",
    "quick",
    "brown",
    "fox",
    "jumps",
    "over",
    "lazy",
    "dog",
    "senzing",
    "entity",
    "resolution",
    "module",
    "data",
    "record",
    "mapping",
    "loading",
    "query",
    "result",
    "python",
    "code",
    "function",
    "class",
    "test",
    "check",
    "run",
    "build",
    "deploy",
    "config",
]


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@st.composite
def st_pause_text(draw: st.DrawFn) -> str:
    """Generate text that contains at least one pause phrase embedded in surrounding text.

    The strategy picks a random pause phrase from the known list and embeds it
    within random surrounding safe words.

    Returns:
        A string guaranteed to contain at least one pause pattern match.
    """
    pause_phrase = draw(st.sampled_from(_PAUSE_PHRASES))
    prefix_words = draw(st.lists(st.sampled_from(_SAFE_WORDS), min_size=0, max_size=5))
    suffix_words = draw(st.lists(st.sampled_from(_SAFE_WORDS), min_size=0, max_size=5))

    prefix = " ".join(prefix_words)
    suffix = " ".join(suffix_words)

    parts = [p for p in [prefix, pause_phrase, suffix] if p]
    return " ".join(parts)


@st.composite
def st_non_pause_text(draw: st.DrawFn) -> str:
    """Generate text composed solely of safe words that do not match any pause pattern.

    Returns:
        A string guaranteed to NOT match any pause pattern.
    """
    words = draw(st.lists(st.sampled_from(_SAFE_WORDS), min_size=1, max_size=15))
    return " ".join(words)


# ---------------------------------------------------------------------------
# Property 2: Pause Language Detection
# ---------------------------------------------------------------------------


class TestPauseLanguageDetection:
    """Feature: agent-behavior-rules, Property 2: Pause Language Detection"""

    @given(text=st_pause_text())
    @settings(max_examples=100)
    def test_text_with_pause_phrase_detected(self, text: str) -> None:
        """For any text containing at least one pause pattern match,
        contains_pause_language SHALL return True.

        **Validates: Requirements 1.1, 1.2, 1.4**
        """
        assert contains_pause_language(text) is True, (
            f"Expected True for text containing pause language: {text!r}"
        )

    @given(text=st_non_pause_text())
    @settings(max_examples=100)
    def test_text_without_pause_phrase_not_detected(self, text: str) -> None:
        """For any text composed solely of words not matching any pause pattern,
        contains_pause_language SHALL return False.

        **Validates: Requirements 1.1, 1.2, 1.4**
        """
        assert contains_pause_language(text) is False, (
            f"Expected False for text without pause language: {text!r}"
        )


# ---------------------------------------------------------------------------
# Strategies — Continuation Request Classification
# ---------------------------------------------------------------------------

# Characters safe for surrounding text: letters, numbers, punctuation, spaces
_SAFE_TEXT_CHARS = st.characters(
    whitelist_categories=("L", "N", "P", "Z"),
    blacklist_characters="\x00\r",
)


@st.composite
def st_continuation_message(draw: st.DrawFn) -> str:
    """Generate a message that contains at least one continuation phrase.

    Embeds a randomly chosen continuation phrase within random surrounding text.

    Returns:
        A string guaranteed to contain at least one continuation phrase.
    """
    phrase = draw(st.sampled_from(CONTINUATION_PHRASES))

    # Optionally apply case variation to the phrase
    case_variant = draw(st.sampled_from(["lower", "upper", "title", "mixed"]))
    if case_variant == "lower":
        phrase = phrase.lower()
    elif case_variant == "upper":
        phrase = phrase.upper()
    elif case_variant == "title":
        phrase = phrase.title()
    else:
        # Mixed case: randomly capitalize each character
        phrase = "".join(
            ch.upper() if draw(st.booleans()) else ch.lower() for ch in phrase
        )

    # Generate surrounding text from safe words to avoid accidental phrase matches
    prefix_words = draw(st.lists(st.sampled_from(_SAFE_WORDS), min_size=0, max_size=5))
    suffix_words = draw(st.lists(st.sampled_from(_SAFE_WORDS), min_size=0, max_size=5))

    prefix = " ".join(prefix_words)
    suffix = " ".join(suffix_words)

    parts = [p for p in [prefix, phrase, suffix] if p]
    return " ".join(parts)


@st.composite
def st_non_continuation_message(draw: st.DrawFn) -> str:
    """Generate a message that does NOT contain any continuation phrase.

    Generates text from safe words and verifies no continuation phrase appears.

    Returns:
        A string guaranteed to contain no continuation phrase (case-insensitive).
    """
    words = draw(st.lists(st.sampled_from(_SAFE_WORDS), min_size=1, max_size=15))
    text = " ".join(words)
    lower_text = text.lower()
    # Reject if any continuation phrase appears in the text
    assume(not any(phrase in lower_text for phrase in CONTINUATION_PHRASES))
    return text


# ---------------------------------------------------------------------------
# Property 1: Continuation Request Classification Round-Trip
# ---------------------------------------------------------------------------


class TestContinuationRequestClassification:
    """Feature: agent-behavior-rules, Property 1: Continuation Request Classification Round-Trip"""

    @given(message=st_continuation_message())
    @settings(max_examples=100)
    def test_message_with_continuation_phrase_returns_true(self, message: str) -> None:
        """For any string containing at least one phrase from CONTINUATION_PHRASES
        (case-insensitive), is_continuation_request SHALL return True.

        **Validates: Requirements 1.1, 1.4, 1.5**
        """
        assert is_continuation_request(message) is True, (
            f"Expected True for message containing continuation phrase: {message!r}"
        )

    @given(message=st_non_continuation_message())
    @settings(max_examples=100)
    def test_message_without_continuation_phrase_returns_false(self, message: str) -> None:
        """For any string that contains none of the CONTINUATION_PHRASES,
        is_continuation_request SHALL return False.

        **Validates: Requirements 1.1, 1.4, 1.5**
        """
        assert is_continuation_request(message) is False, (
            f"Expected False for message without continuation phrase: {message!r}"
        )


# ---------------------------------------------------------------------------
# Strategies — Acknowledgment Length Constraint
# ---------------------------------------------------------------------------

# Substantive words that form meaningful acknowledgment content
_SUBSTANTIVE_WORDS: list[str] = [
    "Senzing",
    "entity",
    "resolution",
    "configured",
    "PostgreSQL",
    "database",
    "mapping",
    "records",
    "loaded",
    "successfully",
    "module",
    "completed",
    "integration",
    "deployment",
    "transform",
    "datasource",
    "features",
    "attributes",
    "matching",
    "threshold",
]


@st.composite
def st_short_acknowledgment(draw: st.DrawFn) -> str:
    """Generate substantive acknowledgment text with ≤2 sentences and ≤50 words.

    Produces text that is substantive (contains real content words, not just
    content-free phrases) and stays within both length limits.

    Returns:
        A string with ≤2 sentences, ≤50 words, and substantive content.
    """
    sentence_count = draw(st.integers(min_value=1, max_value=2))
    sentences: list[str] = []

    for _ in range(sentence_count):
        # Each sentence: 3-20 words to stay well within 50-word total limit
        max_words = min(20, 50 - sum(len(s.split()) for s in sentences))
        if max_words < 3:
            break
        word_count = draw(st.integers(min_value=3, max_value=max_words))
        words = draw(
            st.lists(
                st.sampled_from(_SUBSTANTIVE_WORDS),
                min_size=word_count,
                max_size=word_count,
            )
        )
        ending = draw(st.sampled_from([".", "!", "?"]))
        sentence = " ".join(words) + ending
        sentences.append(sentence)

    text = " ".join(sentences)

    # Verify constraints hold
    total_words = len(text.split())
    assume(total_words <= 50)
    assume(len(sentences) <= 2)

    return text


@st.composite
def st_too_many_sentences(draw: st.DrawFn) -> str:
    """Generate text with 3+ sentences (each ending with . or ! or ?).

    Returns:
        A string with at least 3 sentences, each terminated by sentence-ending
        punctuation.
    """
    sentence_count = draw(st.integers(min_value=3, max_value=6))
    sentences: list[str] = []

    for _ in range(sentence_count):
        word_count = draw(st.integers(min_value=2, max_value=8))
        words = draw(
            st.lists(
                st.sampled_from(_SUBSTANTIVE_WORDS),
                min_size=word_count,
                max_size=word_count,
            )
        )
        ending = draw(st.sampled_from([".", "!", "?"]))
        sentence = " ".join(words) + ending
        sentences.append(sentence)

    return " ".join(sentences)


@st.composite
def st_too_many_words(draw: st.DrawFn) -> str:
    """Generate text with 51+ words in ≤2 sentences.

    Returns:
        A string with at most 2 sentences but more than 50 words total.
    """
    sentence_count = draw(st.integers(min_value=1, max_value=2))
    # Distribute words: ensure total > 50
    total_target = draw(st.integers(min_value=51, max_value=80))

    sentences: list[str] = []
    words_remaining = total_target

    for i in range(sentence_count):
        if i == sentence_count - 1:
            # Last sentence gets all remaining words
            word_count = words_remaining
        else:
            # First sentence gets a portion
            word_count = draw(st.integers(min_value=3, max_value=words_remaining - 3))
            words_remaining -= word_count

        words = draw(
            st.lists(
                st.sampled_from(_SUBSTANTIVE_WORDS),
                min_size=word_count,
                max_size=word_count,
            )
        )
        ending = draw(st.sampled_from([".", "!", "?"]))
        sentence = " ".join(words) + ending
        sentences.append(sentence)

    text = " ".join(sentences)

    # Verify constraint: >50 words and ≤2 sentences
    assume(len(text.split()) > 50)

    return text


# ---------------------------------------------------------------------------
# Property 3: Acknowledgment Length Constraint
# ---------------------------------------------------------------------------


class TestAcknowledgmentLengthConstraint:
    """Feature: agent-behavior-rules, Property 3: Acknowledgment Length Constraint"""

    @given(text=st_too_many_sentences())
    @settings(max_examples=100)
    def test_too_many_sentences_is_invalid(self, text: str) -> None:
        """For any text exceeding 2 sentences, validate_acknowledgment SHALL
        report valid=False.

        **Validates: Requirements 2.1, 2.2**
        """
        result = validate_acknowledgment(text)
        assert result.valid is False, (
            f"Expected valid=False for text with >2 sentences: {text!r} "
            f"(sentence_count={result.sentence_count})"
        )

    @given(text=st_too_many_words())
    @settings(max_examples=100)
    def test_too_many_words_is_invalid(self, text: str) -> None:
        """For any text exceeding 50 words, validate_acknowledgment SHALL
        report valid=False.

        **Validates: Requirements 2.1, 2.2**
        """
        result = validate_acknowledgment(text)
        assert result.valid is False, (
            f"Expected valid=False for text with >50 words: {text!r} "
            f"(word_count={result.word_count})"
        )

    @given(text=st_short_acknowledgment())
    @settings(max_examples=100)
    def test_short_substantive_text_is_valid(self, text: str) -> None:
        """For any substantive text within both limits (≤2 sentences AND ≤50 words),
        validate_acknowledgment SHALL report valid=True.

        **Validates: Requirements 2.1, 2.2**
        """
        result = validate_acknowledgment(text)
        assert result.valid is True, (
            f"Expected valid=True for short substantive text: {text!r} "
            f"(sentence_count={result.sentence_count}, word_count={result.word_count}, "
            f"is_substantive={result.is_substantive})"
        )

# ---------------------------------------------------------------------------
# Strategies — Substantive Acknowledgment Rejection
# ---------------------------------------------------------------------------

# Punctuation that may appear between or after content-free phrases
_PHRASE_PUNCTUATION: list[str] = [".", "!", "?", ",", ""]


@st.composite
def st_content_free_text(draw: st.DrawFn) -> str:
    """Generate text composed entirely of content-free phrases with optional punctuation.

    Combines 1-3 content-free phrases with optional punctuation and whitespace
    between them. The resulting text should always be classified as non-substantive.

    Returns:
        A string composed entirely of content-free phrases (with optional punctuation/whitespace).
    """
    num_phrases = draw(st.integers(min_value=1, max_value=3))
    parts: list[str] = []

    for i in range(num_phrases):
        phrase = draw(st.sampled_from(CONTENT_FREE_PHRASES))

        # Optionally apply case variation
        case_variant = draw(st.sampled_from(["lower", "title", "upper"]))
        if case_variant == "lower":
            phrase = phrase.lower()
        elif case_variant == "title":
            phrase = phrase.title()
        else:
            phrase = phrase.upper()

        # Optionally append punctuation
        punctuation = draw(st.sampled_from(_PHRASE_PUNCTUATION))
        phrase = phrase + punctuation

        parts.append(phrase)

    # Join with whitespace (1-3 spaces)
    separator = draw(st.sampled_from([" ", "  ", " "]))
    return separator.join(parts)


# ---------------------------------------------------------------------------
# Property 4: Substantive Acknowledgment Rejection of Content-Free Phrases
# ---------------------------------------------------------------------------


class TestSubstantiveAcknowledgmentRejection:
    """Feature: agent-behavior-rules, Property 4: Substantive Acknowledgment Rejection of Content-Free Phrases"""

    @given(text=st_content_free_text())
    @settings(max_examples=100)
    def test_content_free_phrases_are_not_substantive(self, text: str) -> None:
        """For any string composed entirely of one or more CONTENT_FREE_PHRASES
        (with optional punctuation and whitespace), validate_acknowledgment
        SHALL report is_substantive=False.

        **Validates: Requirements 2.3**
        """
        result = validate_acknowledgment(text)
        assert result.is_substantive is False, (
            f"Expected is_substantive=False for content-free text: {text!r}, "
            f"got result: {result}"
        )


# ---------------------------------------------------------------------------
# Strategies — Compound Question Detection
# ---------------------------------------------------------------------------

# Conjunction phrases used to join alternatives in compound questions
_CONJUNCTION_PHRASES: list[str] = [
    "or",
    "alternatively",
    "or would you rather",
    "or should we",
    "or would you prefer",
    "or if you prefer",
]

# Question stems for building compound questions
_QUESTION_STEMS: list[str] = [
    "Would you like to use",
    "Should we configure",
    "Do you want to try",
    "Shall we set up",
    "Would you prefer to use",
    "Do you want me to create",
]

# Alternatives that can be joined by conjunctions
_ALTERNATIVES: list[str] = [
    "Python",
    "Java",
    "PostgreSQL",
    "SQLite",
    "Docker",
    "bare metal",
    "REST API",
    "SDK",
    "batch loading",
    "streaming",
    "cloud deployment",
    "local setup",
]

# Simple yes/no questions that do NOT contain conjunction patterns
_SIMPLE_QUESTIONS: list[str] = [
    "Ready to continue?",
    "Does that look correct?",
    "Shall we proceed?",
    "Is this configuration acceptable?",
    "Would you like to see the results?",
    "Are you ready to move to the next step?",
    "Do you want me to run the tests?",
    "Should I apply these changes?",
    "Is the database running?",
    "Have you installed the prerequisites?",
    "Can you confirm the file exists?",
    "Did the deployment succeed?",
]


@st.composite
def st_compound_question(draw: st.DrawFn) -> str:
    """Generate a question containing "?" AND at least one prose conjunction pattern.

    Builds a question with two alternatives joined by a conjunction, ending with "?".
    The resulting string is guaranteed to contain a "?" and match at least one
    CONJUNCTION_PATTERNS regex.

    Returns:
        A compound question string with alternatives joined by a prose conjunction.
    """
    stem = draw(st.sampled_from(_QUESTION_STEMS))
    conjunction = draw(st.sampled_from(_CONJUNCTION_PHRASES))
    alt1 = draw(st.sampled_from(_ALTERNATIVES))
    alt2 = draw(st.sampled_from(_ALTERNATIVES).filter(lambda x: x != alt1))

    # Build the compound question
    if conjunction == "or":
        question = f"{stem} {alt1} or {alt2}?"
    elif conjunction == "alternatively":
        question = f"{stem} {alt1}, alternatively {alt2}?"
    elif conjunction == "or would you rather":
        question = f"{stem} {alt1}, or would you rather use {alt2}?"
    elif conjunction == "or should we":
        question = f"{stem} {alt1}, or should we use {alt2}?"
    elif conjunction == "or would you prefer":
        question = f"{stem} {alt1}, or would you prefer {alt2}?"
    else:  # "or if you prefer"
        question = f"{stem} {alt1}, or if you prefer, {alt2}?"

    return question


@st.composite
def st_simple_question(draw: st.DrawFn) -> str:
    """Generate a simple yes/no question without any prose conjunction patterns.

    Selects from a curated list of simple questions that have exactly one
    unambiguous meaning for "yes" and "no". These questions do NOT contain
    any CONJUNCTION_PATTERNS match.

    Returns:
        A simple yes/no question string without prose conjunctions.
    """
    return draw(st.sampled_from(_SIMPLE_QUESTIONS))


# ---------------------------------------------------------------------------
# Property 5: Compound Question Detection
# ---------------------------------------------------------------------------


class TestCompoundQuestionDetection:
    """Feature: agent-behavior-rules, Property 5: Compound Question Detection"""

    @given(question=st_compound_question())
    @settings(max_examples=100)
    def test_compound_question_detected(self, question: str) -> None:
        """For any question string containing a "?" AND at least one prose conjunction
        (matching CONJUNCTION_PATTERNS), is_compound_question SHALL return True.

        **Validates: Requirements 3.1, 3.3, 3.5**
        """
        assert is_compound_question(question) is True, (
            f"Expected True for compound question: {question!r}"
        )

    @given(question=st_simple_question())
    @settings(max_examples=100)
    def test_simple_question_not_detected(self, question: str) -> None:
        """For any simple yes/no question without prose conjunctions joining
        alternatives, is_compound_question SHALL return False.

        **Validates: Requirements 3.1, 3.3, 3.5**
        """
        assert is_compound_question(question) is False, (
            f"Expected False for simple question: {question!r}"
        )


# ---------------------------------------------------------------------------
# Strategies — Numbered List Format Requirement
# ---------------------------------------------------------------------------

# Lead questions that introduce a set of alternatives
_LEAD_QUESTIONS: list[str] = [
    "Which language would you like to use?",
    "Which option do you prefer?",
    "What approach should we take?",
    "Which database would you like to configure?",
    "How would you like to proceed?",
    "Which module would you like to start with?",
    "What format do you want for the output?",
    "Which SDK would you like to use?",
    "What deployment target do you prefer?",
    "Which data source should we load first?",
]

# Alternative items that can appear in numbered lists
_ALTERNATIVES: list[str] = [
    "Python",
    "Java",
    "C#",
    "Rust",
    "TypeScript",
    "PostgreSQL",
    "SQLite",
    "Docker",
    "Kubernetes",
    "Local installation",
    "Cloud deployment",
    "JSON format",
    "CSV format",
    "Entity resolution",
    "Record matching",
    "Data mapping",
    "SDK integration",
    "REST API",
    "Direct database access",
    "Batch processing",
]

# Prose conjunction phrases used to join alternatives improperly
_PROSE_CONJUNCTIONS: list[str] = [
    "or",
    "or alternatively",
    "or would you rather",
    "or should we",
    "or would you prefer",
    "or if you prefer",
]


@st.composite
def st_numbered_list_question(draw: st.DrawFn) -> str:
    """Generate a properly formatted multi-alternative question with numbered list.

    Produces a lead question line followed by 2-5 numbered alternatives.
    These should NOT be detected as compound questions.

    Returns:
        A string with a lead question and numbered alternatives on separate lines.
    """
    lead = draw(st.sampled_from(_LEAD_QUESTIONS))
    num_alternatives = draw(st.integers(min_value=2, max_value=5))

    # Pick distinct alternatives
    alternatives = draw(
        st.lists(
            st.sampled_from(_ALTERNATIVES),
            min_size=num_alternatives,
            max_size=num_alternatives,
            unique=True,
        )
    )

    # Format as numbered list
    numbered_lines = [f"{i + 1}. {alt}" for i, alt in enumerate(alternatives)]

    return lead + "\n" + "\n".join(numbered_lines)


@st.composite
def st_prose_alternatives_question(draw: st.DrawFn) -> str:
    """Generate an improperly formatted question with alternatives joined by prose.

    Produces questions like "Would you like Python or Java?" or
    "Should we use Docker, or alternatively Kubernetes?" that join
    alternatives with prose conjunctions instead of numbered lists.

    These SHOULD be detected as compound questions.

    Returns:
        A string containing a question with alternatives joined by prose conjunctions.
    """
    # Pick 2-3 alternatives to join with prose
    num_alternatives = draw(st.integers(min_value=2, max_value=3))
    alternatives = draw(
        st.lists(
            st.sampled_from(_ALTERNATIVES),
            min_size=num_alternatives,
            max_size=num_alternatives,
            unique=True,
        )
    )

    conjunction = draw(st.sampled_from(_PROSE_CONJUNCTIONS))

    # Build the question with prose conjunctions
    question_starters = [
        "Would you like",
        "Should we use",
        "Do you want",
        "Would you prefer",
        "Should I set up",
    ]
    starter = draw(st.sampled_from(question_starters))

    if num_alternatives == 2:
        question = f"{starter} {alternatives[0]} {conjunction} {alternatives[1]}?"
    else:
        # Join first N-1 with commas, last with conjunction
        leading = ", ".join(alternatives[:-1])
        question = f"{starter} {leading}, {conjunction} {alternatives[-1]}?"

    return question


# ---------------------------------------------------------------------------
# Property 6: Numbered List Format Requirement
# ---------------------------------------------------------------------------


class TestNumberedListFormatRequirement:
    """Feature: agent-behavior-rules, Property 6: Numbered List Format Requirement"""

    @given(question=st_numbered_list_question())
    @settings(max_examples=100)
    def test_numbered_list_question_not_detected_as_compound(self, question: str) -> None:
        """For any question presenting 2 or more distinct alternatives formatted as a
        numbered choice list preceded by a single lead question, is_compound_question
        SHALL return False (properly formatted questions are not flagged).

        **Validates: Requirements 3.2**
        """
        assert is_compound_question(question) is False, (
            f"Expected False for properly formatted numbered list question: {question!r}"
        )

    @given(question=st_prose_alternatives_question())
    @settings(max_examples=100)
    def test_prose_alternatives_detected_as_compound(self, question: str) -> None:
        """For any question with alternatives joined by prose conjunctions
        (lacking numbered list format), is_compound_question SHALL return True
        (improperly formatted questions are flagged as violations).

        **Validates: Requirements 3.2**
        """
        assert is_compound_question(question) is True, (
            f"Expected True for prose-formatted alternatives question: {question!r}"
        )


# ---------------------------------------------------------------------------
# Strategies — Universal Pointer Indicator Presence
# ---------------------------------------------------------------------------

# Prompt texts that would follow the pointer indicator
_PROMPT_TEXTS: list[str] = [
    "Ready to continue?",
    "Choose your language:",
    "Which module would you like to start?",
    "Type 'continue' when ready.",
    "Select a data source:",
    "Would you like to see the results?",
    "Say 'next' to proceed.",
    "Pick an option below:",
    "Enter your database connection string:",
    "Confirm the configuration above.",
]

# Other emojis that are NOT the pointer indicator
_OTHER_EMOJIS: list[str] = [
    "\u2705",  # ✅
    "\u274c",  # ❌
    "\u26a0\ufe0f",  # ⚠️
    "\U0001f4a1",  # 💡
    "\U0001f680",  # 🚀
    "\U0001f4dd",  # 📝
    "\U0001f50d",  # 🔍
    "\u2139\ufe0f",  # ℹ️
]

# Regular text lines that don't start with pointer
_REGULAR_LINES: list[str] = [
    "This is a regular line of text.",
    "The entity resolution process completed.",
    "Here are the results of your query:",
    "Module 3 covers data loading.",
    "You can find more details in the documentation.",
    "The configuration file has been updated.",
    "Next, we will set up the database.",
    "Great work on completing this step!",
]


@st.composite
def st_pointer_prefixed_line(draw: st.DrawFn) -> str:
    """Generate a line that starts with the pointer indicator (after optional list markers).

    Optionally preceded by list markers ("- ", "* ", or nothing), followed by
    the pointer emoji and prompt text.

    Returns:
        A string guaranteed to start with pointer indicator after stripping
        optional list markers.
    """
    # Choose optional list marker prefix
    list_marker = draw(st.sampled_from(["", "- ", "* "]))

    # Optional leading whitespace
    leading_space = draw(st.sampled_from(["", " ", "  "]))

    # The pointer indicator
    pointer = "\U0001f449"

    # Optional space after pointer
    space_after = draw(st.sampled_from([" ", ""]))

    # Prompt text
    prompt_text = draw(st.sampled_from(_PROMPT_TEXTS))

    return f"{leading_space}{list_marker}{pointer}{space_after}{prompt_text}"


@st.composite
def st_non_pointer_line(draw: st.DrawFn) -> str:
    """Generate a line that does NOT start with the pointer indicator.

    Generates one of:
    - Regular text lines (no pointer at all)
    - Lines starting with other emojis
    - Lines with pointer in the middle (not at start after stripping markers)

    Returns:
        A string guaranteed to NOT start with pointer indicator after stripping
        optional list markers.
    """
    variant = draw(st.sampled_from(["regular", "other_emoji", "pointer_in_middle"]))

    if variant == "regular":
        # Plain text line without any pointer
        line = draw(st.sampled_from(_REGULAR_LINES))
        # Optionally add a list marker prefix
        list_marker = draw(st.sampled_from(["", "- ", "* "]))
        return f"{list_marker}{line}"

    elif variant == "other_emoji":
        # Line starting with a different emoji (not pointer)
        emoji = draw(st.sampled_from(_OTHER_EMOJIS))
        prompt_text = draw(st.sampled_from(_PROMPT_TEXTS))
        list_marker = draw(st.sampled_from(["", "- ", "* "]))
        return f"{list_marker}{emoji} {prompt_text}"

    else:
        # Line with pointer in the middle, not at start
        prefix_text = draw(st.sampled_from(_REGULAR_LINES))
        pointer = "\U0001f449"
        suffix_text = draw(st.sampled_from(_PROMPT_TEXTS))
        return f"{prefix_text} {pointer} {suffix_text}"


# ---------------------------------------------------------------------------
# Property 7: Universal Pointer Indicator Presence
# ---------------------------------------------------------------------------


class TestUniversalPointerIndicatorPresence:
    """Feature: agent-behavior-rules, Property 7: Universal Pointer Indicator Presence"""

    @given(line=st_pointer_prefixed_line())
    @settings(max_examples=100)
    def test_line_with_pointer_prefix_detected(self, line: str) -> None:
        """For any line that starts with the pointer indicator (after optional list
        markers like "- " or "* "), has_pointer_prefix SHALL return True.

        **Validates: Requirements 4.1, 4.3, 4.4, 4.5**
        """
        assert has_pointer_prefix(line) is True, (
            f"Expected True for line with pointer prefix: {line!r}"
        )

    @given(line=st_non_pointer_line())
    @settings(max_examples=100)
    def test_line_without_pointer_prefix_not_detected(self, line: str) -> None:
        """For any line that does NOT start with the pointer indicator (after
        stripping optional list markers), has_pointer_prefix SHALL return False.

        **Validates: Requirements 4.1, 4.3, 4.4, 4.5**
        """
        assert has_pointer_prefix(line) is False, (
            f"Expected False for line without pointer prefix: {line!r}"
        )
