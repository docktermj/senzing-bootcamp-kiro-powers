# Install Kiro

## Prerequisites

- **macOS:** Intel or Apple silicon with latest security updates
- **Windows:** Windows 10 or 11 (64-bit only; ARM is not currently supported)
- **Linux:** glibc 2.39 or higher (e.g., Ubuntu 24+, Debian 13+, Fedora 40+, Arch Linux, Linux Mint 22+)

## Install

1. Download the installer for your operating system from [kiro.dev/downloads](https://kiro.dev/downloads/).
1. Open the downloaded file and follow the installation instructions for your operating system.
1. Launch the Kiro IDE application.

## Configure

On first launch, Kiro walks through initial setup:

1. **Authenticate** — Sign in with GitHub, Google, AWS Builder ID, or AWS IAM Identity Center.
   No AWS account is required.
1. **Import editor settings** — Optionally import VS Code settings, themes, and extensions.
   Skip this step if migrating from a different editor.
1. **Choose a theme** — Select a preferred appearance.
1. **Enable shell integration** — Allow Kiro to set up shell integration so the agent can
   execute commands on your behalf.

## How to run Kiro in a new directory

1. Create a new, empty directory.
1. In the new directory, open Kiro. Example:

    ```console
    kiro .
    ```

For more details, see the [Kiro documentation](https://kiro.dev/docs/getting-started/).
