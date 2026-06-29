# Requirements Document

## Introduction

The `senzing-bootcamp` power ships a large pytest + Hypothesis test suite (~5,700 tests across ~349 files) split between two collection roots: `senzing-bootcamp/tests/` (power tests) and `tests/` (repo-level hook tests). Each root has its own `conftest.py`, and both already register an identically-named Hypothesis profile (`bootcamp`) that sets `deadline=None` and suppresses the `too_slow` health check — but neither profile controls `max_examples`. Property-based tests therefore rely on inline `@settings(max_examples=20)` decorators (the convention recorded in `.kiro/steering/python-conventions.md`) to control example counts.

There is currently no centralized way to dial Hypothesis example counts. The root `pyproject.toml` has a `[tool.ruff]` section but no `[tool.pytest.ini_options]` section and no registered profile hierarchy beyond the duplicated `bootcamp` definition. When a developer wants faster local runs, the only lever is hand-editing `max_examples` on individual tests — which recently happened (a test was lowered from 20 to 10 by hand). This is error-prone, does not scale, and risks committing reduced example counts that silently weaken CI coverage.

This feature introduces centralized Hypothesis configuration through registered profiles selected by an environment variable: a fast profile for local iteration (fewer examples) and a thorough profile for CI (example count at or above today's baseline). Profiles are registered once in a shared location and consumed by both `conftest.py` files without duplication. CI is wired to select the thorough profile so coverage is never weakened. Existing per-test `@settings` decorators continue to function as explicit overrides on top of the profile-supplied baseline. Documentation and the Python conventions steering file are reconciled with the new approach.

## Glossary

- **Hypothesis**: The property-based testing library used by the suite via `@given` and `@settings` decorators.
- **Profile**: A named Hypothesis settings bundle registered with `settings.register_profile(name, ...)` and activated with `settings.load_profile(name)`.
- **Profile_Registry**: The shared helper module (new) that registers all Hypothesis profiles and exposes a single function to select and load the active profile. Imported by both `conftest.py` files.
- **Power_Conftest**: The `conftest.py` file at `senzing-bootcamp/tests/conftest.py`.
- **Repo_Conftest**: The `conftest.py` file at `tests/conftest.py`.
- **Conftest**: Either `Power_Conftest` or `Repo_Conftest` when a statement applies to both.
- **Fast_Profile**: The registered profile intended for local iteration, using a reduced `max_examples` count for speed.
- **Thorough_Profile**: The registered profile intended for CI, using a `max_examples` count greater than or equal to the current baseline (20).
- **Profile_Env_Var**: The environment variable that selects which profile `Profile_Registry` loads.
- **Baseline_Example_Count**: The current convention value of `max_examples`, equal to 20.
- **Per_Test_Settings**: An inline `@settings(...)` decorator on an individual test that overrides specific settings keys for that test only.
- **CI_Pipeline**: The GitHub Actions workflow at `.github/workflows/validate-power.yml`, specifically its "Run tests" pytest step.
- **Test_Suite**: The combined pytest invocation `python -m pytest senzing-bootcamp/tests/ tests/`.
- **Python_Conventions**: The steering file `.kiro/steering/python-conventions.md`.

## Requirements

### Requirement 1: Centralized profile registration in a shared module

**User Story:** As a developer maintaining the test suite, I want all Hypothesis profiles registered in one shared module, so that example counts are controlled in a single place instead of being scattered across individual test files.

#### Acceptance Criteria

1. THE Profile_Registry SHALL register at least two named profiles: a Fast_Profile and a Thorough_Profile.
2. THE Profile_Registry SHALL set an explicit `max_examples` value on the Fast_Profile.
3. THE Profile_Registry SHALL set an explicit `max_examples` value on the Thorough_Profile.
4. THE Profile_Registry SHALL set the Thorough_Profile `max_examples` to a value greater than or equal to the Baseline_Example_Count.
5. THE Profile_Registry SHALL set the Fast_Profile `max_examples` to a value less than the Thorough_Profile `max_examples`.
6. THE Profile_Registry SHALL preserve the existing timing behavior on every registered profile by setting `deadline` to none and suppressing the `too_slow` health check.
7. THE Profile_Registry SHALL reside in a location importable by both Power_Conftest and Repo_Conftest.

### Requirement 2: Shared registration without duplication

**User Story:** As a developer, I want both conftest files to consume the same profile definitions, so that the two collection roots never drift apart in their Hypothesis configuration.

#### Acceptance Criteria

1. THE Power_Conftest SHALL obtain its Hypothesis profiles by importing Profile_Registry.
2. THE Repo_Conftest SHALL obtain its Hypothesis profiles by importing Profile_Registry.
3. THE Profile_Registry SHALL define each profile name exactly once across the codebase.
4. WHEN Profile_Registry is imported more than once within a single Test_Suite run, THE Profile_Registry SHALL register each profile without raising an error.
5. WHERE the previously duplicated `bootcamp` profile definitions existed in Power_Conftest and Repo_Conftest, THE feature SHALL remove the duplicated inline registrations in favor of Profile_Registry.

### Requirement 3: Environment-variable-based profile selection with a default

**User Story:** As a developer running tests locally, I want the active profile chosen by an environment variable with a sensible default, so that I can switch between fast and thorough runs without editing any test code.

#### Acceptance Criteria

1. WHEN Profile_Env_Var is set to the name of a registered profile, THE Profile_Registry SHALL load that profile.
2. WHEN Profile_Env_Var is unset, THE Profile_Registry SHALL load the default profile.
3. IF Profile_Env_Var is set to a value that does not match any registered profile, THEN THE Profile_Registry SHALL raise an error that names the unrecognized value.
4. THE Profile_Registry SHALL load exactly one profile per Test_Suite run.
5. WHEN both Conftest files import Profile_Registry within one Test_Suite run, THE Profile_Registry SHALL load the same profile for both collection roots.

### Requirement 4: CI selects the thorough profile

**User Story:** As a maintainer, I want CI to always run the thorough profile, so that merged changes are validated against the full example baseline and coverage is never weakened by a local fast setting.

#### Acceptance Criteria

1. THE CI_Pipeline SHALL set Profile_Env_Var to the Thorough_Profile name for the "Run tests" step.
2. WHEN the CI_Pipeline runs the Test_Suite, THE Profile_Registry SHALL load the Thorough_Profile.
3. THE CI_Pipeline SHALL apply the Thorough_Profile selection across the Python 3.11, 3.12, and 3.13 matrix entries.
4. THE CI_Pipeline SHALL continue to invoke the Test_Suite over both `senzing-bootcamp/tests/` and `tests/`.

### Requirement 5: Interaction with per-test settings overrides

**User Story:** As a test author, I want a profile to set the global baseline while still allowing a specific test to request more examples, so that high-value properties can run deeper without changing the global default.

#### Acceptance Criteria

1. THE active Profile SHALL supply the baseline `max_examples` for any property test that has no Per_Test_Settings `max_examples` value.
2. WHERE a property test declares a Per_Test_Settings `max_examples` value, THE Per_Test_Settings value SHALL take precedence over the active Profile `max_examples` for that test.
3. THE feature SHALL preserve the existing behavior in which Per_Test_Settings keys override the corresponding active Profile keys.

### Requirement 6: Preserve existing conftest behavior

**User Story:** As a developer, I want the existing test-harness behaviors to keep working after centralization, so that introducing profiles does not destabilize the suite.

#### Acceptance Criteria

1. THE Repo_Conftest SHALL continue to snap the current working directory to the project root before each repo-level test.
2. THE Power_Conftest SHALL continue to recover a stale or temp-directory working directory to the project root before each test.
3. THE Conftest files SHALL continue to make their respective scripts and helper directories importable via `sys.path`.
4. THE feature SHALL keep Hypothesis and pytest as the only added test dependencies and SHALL NOT introduce a non-stdlib runtime dependency for scripts.

### Requirement 7: Documentation and convention reconciliation

**User Story:** As a developer reading the project conventions, I want the documented guidance to match the centralized profile approach, so that I know profiles set the baseline and inline `@settings` are overrides.

#### Acceptance Criteria

1. THE feature SHALL update Python_Conventions to describe profile-based baseline example counts and environment-variable selection.
2. THE feature SHALL document in Python_Conventions that Per_Test_Settings act as overrides on top of the active Profile baseline.
3. THE feature SHALL document the registered profile names, the Profile_Env_Var name, and the default profile.
4. THE feature SHALL document the command or environment-variable setting a developer uses to run the Fast_Profile locally and the Thorough_Profile locally.
5. WHERE Python_Conventions currently prescribes a fixed inline `@settings(max_examples=20)`, THE updated Python_Conventions SHALL reconcile that guidance with the profile baseline.

### Requirement 8: Test and verification coverage

**User Story:** As a maintainer, I want automated tests for the centralization logic, so that profile registration and selection behavior is verified and does not regress.

#### Acceptance Criteria

1. THE feature SHALL include a test verifying that the Fast_Profile and Thorough_Profile are registered.
2. THE feature SHALL include a test verifying that the Thorough_Profile `max_examples` is greater than or equal to the Baseline_Example_Count.
3. THE feature SHALL include a test verifying that the Fast_Profile `max_examples` is less than the Thorough_Profile `max_examples`.
4. WHEN Profile_Env_Var is set to a registered profile name, THE corresponding test SHALL verify that Profile_Registry selects that profile.
5. WHEN Profile_Env_Var is unset, THE corresponding test SHALL verify that Profile_Registry selects the default profile.
6. IF Profile_Env_Var is set to an unrecognized value, THEN THE corresponding test SHALL verify that Profile_Registry raises an error.

## Open Design Decisions

These decisions are intentionally deferred to the design phase rather than guessed here:

1. **Exact profile names.** The requirements use `Fast_Profile` and `Thorough_Profile` as roles. Candidate concrete names include `dev`/`ci`, `fast`/`thorough`, or retaining `bootcamp` as one of them. The existing duplicated profile is literally named `bootcamp`; the design must decide whether to rename it, keep it as an alias, or layer the new names on top.
2. **Default profile for local runs.** The brief states the local default should be fast. The design must confirm whether the default (when `Profile_Env_Var` is unset) is the Fast_Profile, and whether any non-CI automation needs a different default.
3. **Exact example counts.** Thorough must be `>= 20` (the current baseline). The design must pick concrete values for both Fast (e.g., 5 or 10) and Thorough (e.g., 20, 50, or 100), balancing local speed against CI thoroughness.
4. **Environment variable name.** Hypothesis's own convention is `HYPOTHESIS_PROFILE`. The design must decide whether to adopt that built-in name (and whether to use Hypothesis's native profile-loading mechanism) or a project-specific variable.
5. **Shared module location and import mechanism.** The two conftests live in different roots that are not a single package. The design must choose where `Profile_Registry` lives (e.g., a small module under `tests/` or `senzing-bootcamp/tests/`, or a shared helpers location) and how each conftest imports it without breaking the existing `sys.path` and cwd-snapping behavior.
6. **`pyproject.toml` pytest section.** The design must decide whether to add a `[tool.pytest.ini_options]` section (and what it should contain) or keep all configuration in `conftest.py` and CI.
7. **Migration of existing inline `@settings(max_examples=20)` decorators.** The design must decide whether existing inline decorators are left as-is (now redundant with the Thorough baseline), removed in bulk, or kept only where a test genuinely needs a non-baseline count.
8. **Whether the recently hand-lowered test (20 → 10) should be restored** to rely on the profile baseline as part of this feature.
