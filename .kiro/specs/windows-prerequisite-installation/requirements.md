# Requirements Document

## Introduction

During onboarding (Module 0), the `preflight.py` script checks the bootcamper's environment and reports a verdict. On Windows, when key prerequisites like Java or the Scoop package manager are missing, the current behavior is to emit a WARN verdict and defer installation to Module 2 (SDK Setup). This means the bootcamper may spend significant time in Module 1 before discovering their environment cannot run anything. This feature adds proactive installation offers during the prerequisite check on Windows, catching blockers early and giving the bootcamper confidence that their environment will work.

## Glossary

- **Agent**: The AI assistant executing the bootcamp steering files.
- **Bootcamper**: A user going through the Senzing Bootcamp.
- **Preflight_Script**: The environment verification script at `senzing-bootcamp/scripts/preflight.py` that checks runtimes, tools, disk space, network, and project structure.
- **Preflight_Report**: The structured output of the Preflight_Script containing check results and a verdict (PASS, WARN, or FAIL).
- **Scoop**: The recommended Windows package manager for the bootcamp, used to install Java, .NET SDK, Rust, Node.js, and the Senzing SDK on Windows.
- **Package_Manager**: A tool that automates software installation. On Windows, this is Scoop. On macOS, this is Homebrew. On Linux, this is the system package manager (apt, dnf, etc.).
- **Language_Runtime**: A supported programming language runtime (Python, Java, .NET SDK, Rust, Node.js) required to run Senzing SDK code.
- **Installation_Offer**: A prompt presented by the Agent asking the Bootcamper whether they want to install a missing prerequisite immediately during onboarding.
- **Onboarding_Step_3**: The prerequisite check step in the onboarding flow (`onboarding-flow.md` Step 3) where the Preflight_Script runs and results are acted upon.

## Requirements

### Requirement 1: Detect Scoop Package Manager on Windows

**User Story:** As a Bootcamper on Windows, I want the prerequisite check to detect whether Scoop is installed, so that the Agent knows whether it can offer automated installation of other prerequisites.

#### Acceptance Criteria

1. WHEN the Preflight_Script runs on Windows, THE Preflight_Script SHALL check whether the `scoop` command is available on the system PATH.
2. WHEN Scoop is found on Windows, THE Preflight_Script SHALL report a passing check with the Scoop version.
3. WHEN Scoop is not found on Windows, THE Preflight_Script SHALL report a warning check with a fix message referencing the Scoop installation command.
4. WHEN the Preflight_Script runs on a non-Windows platform, THE Preflight_Script SHALL skip the Scoop check entirely.

### Requirement 2: Offer Scoop Installation During Onboarding on Windows

**User Story:** As a Bootcamper on Windows without Scoop installed, I want to be offered Scoop installation during the prerequisite check, so that I can set up the package manager needed for all other Windows installations without waiting until Module 2.

#### Acceptance Criteria

1. WHEN the Preflight_Report indicates Scoop is missing on Windows, THE Agent SHALL offer to install Scoop immediately with a clear explanation of what Scoop is and why it is needed.
2. WHEN the Bootcamper accepts the Scoop installation offer, THE Agent SHALL execute the official Scoop installation command using PowerShell: `irm get.scoop.sh | iex`.
3. WHEN Scoop installation completes successfully, THE Agent SHALL verify the installation by running `scoop --version` and report the result to the Bootcamper.
4. WHEN the Bootcamper declines the Scoop installation offer, THE Agent SHALL proceed with the existing WARN behavior and note that Module 2 will handle installation.
5. IF Scoop installation fails, THEN THE Agent SHALL display the error output, suggest manual installation steps, and proceed with the WARN verdict without blocking onboarding.

### Requirement 3: Offer Language Runtime Installation via Scoop on Windows

**User Story:** As a Bootcamper on Windows whose chosen language runtime is missing, I want to be offered installation of that runtime via Scoop during the prerequisite check, so that I can verify my environment works before investing time in Module 1.

#### Acceptance Criteria

1. WHEN Scoop is available on Windows AND the Bootcamper's chosen Language_Runtime is not found, THE Agent SHALL offer to install the missing runtime via Scoop.
2. WHEN the Bootcamper accepts the runtime installation offer, THE Agent SHALL execute the appropriate Scoop install command for the chosen language (e.g., `scoop install java/temurin-lts-jdk` for Java, `scoop install dotnet-sdk` for .NET, `scoop install rustup` for Rust, `scoop install nodejs-lts` for Node.js).
3. WHEN runtime installation completes successfully, THE Agent SHALL verify the installation by running the runtime's version command and report the result to the Bootcamper.
4. WHEN the Bootcamper declines the runtime installation offer, THE Agent SHALL proceed with the existing WARN behavior and note that Module 2 will handle installation.
5. IF runtime installation via Scoop fails, THEN THE Agent SHALL display the error output, suggest alternative installation methods, and proceed without blocking onboarding.
6. WHEN Scoop is not available on Windows AND the Bootcamper declined Scoop installation, THE Agent SHALL skip the runtime installation offer and defer to Module 2.

### Requirement 4: Preserve Non-Blocking Onboarding Flow

**User Story:** As a Bootcamper, I want prerequisite installation to be optional and non-blocking, so that I can always proceed with onboarding even if installation fails or I choose to defer.

#### Acceptance Criteria

1. THE Agent SHALL present all installation offers as optional choices with clear "install now" and "skip for later" options.
2. WHEN any installation attempt fails, THE Agent SHALL NOT change the Preflight_Report verdict to FAIL solely due to the installation failure.
3. WHEN the Bootcamper declines all installation offers, THE Agent SHALL proceed with the same WARN behavior as the current implementation (noting Module 2 will handle setup).
4. THE Agent SHALL NOT attempt any installation without explicit Bootcamper confirmation.
5. WHEN installations are completed successfully during onboarding, THE Agent SHALL re-run the relevant Preflight_Script checks to update the report verdict before proceeding.

### Requirement 5: Record Installation Actions in Preferences

**User Story:** As a Bootcamper, I want my installation choices during onboarding to be recorded, so that Module 2 knows what was already installed and can skip redundant steps.

#### Acceptance Criteria

1. WHEN the Bootcamper accepts and completes a Scoop installation during onboarding, THE Agent SHALL record `scoop_installed_during_onboarding: true` in `config/bootcamp_preferences.yaml`.
2. WHEN the Bootcamper accepts and completes a runtime installation during onboarding, THE Agent SHALL record the installed runtime under `runtimes_installed_during_onboarding` in `config/bootcamp_preferences.yaml` with the runtime name and version.
3. WHEN Module 2 begins, THE Agent SHALL check `config/bootcamp_preferences.yaml` for previously installed prerequisites and skip re-installation of those items.
4. WHEN the Bootcamper declines installation during onboarding, THE Agent SHALL record `prerequisite_installation_deferred: true` in `config/bootcamp_preferences.yaml`.

### Requirement 6: Support Scoop Bucket Addition for Java

**User Story:** As a Bootcamper who chose Java, I want the Agent to add the required Scoop bucket before attempting Java installation, so that the Java package is available for installation.

#### Acceptance Criteria

1. WHEN the Agent prepares to install Java via Scoop, THE Agent SHALL first run `scoop bucket add java` to ensure the Java bucket is available.
2. WHEN the bucket addition succeeds or the bucket already exists, THE Agent SHALL proceed with the Java installation command.
3. IF the bucket addition fails, THEN THE Agent SHALL report the error and suggest manual installation of Java from the Adoptium website as an alternative.
