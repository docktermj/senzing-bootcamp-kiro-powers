# Install Kiro

## Prerequisites

- **macOS:** Intel or Apple silicon with latest security updates
- **Windows:** Windows 10 or 11 (64-bit only; ARM is not currently supported)
- **Linux:** glibc 2.39 or higher (e.g., Ubuntu 24+, Debian 13+, Fedora 40+, Arch Linux, Linux Mint 22+)

## Install

AWS instructions for installing Kiro is at
<https://catalog.workshops.aws/kiro-immersion/en-US/10-start-workshop/11-aws-event>.
Be sure to install Kiro, not Kiro-CLI.

TLDR:

   1. Download the installer for your operating system from [kiro.dev/downloads](https://kiro.dev/downloads/).
      1. Do not use the `curl` command as it installs the "Kiro CLI", which is not used in the Bootcamp.
   1. Open the downloaded file and follow the installation instructions for your operating system.
   1. Launch the Kiro IDE application.
      Example:

      ```console
      kiro
      ```

## Senzing-only

These instructions will not be advertized publicly.
They are for the Senzingers who are "scrubbing" the Bootcamp.

1. In kiro:
   1. Click "Sign in"
1. In web browser:
   1. In "Choose a way to sign in/up":
      1. Click "Your organization".
   1. In "Sign in with your organization":
      1. Click on the "Sign in via IAM Identity Center instead" link.
   1. In "Sign in with AWS IAM Identity Center":
      1. **Start URL:** <https://awssenzingsso.awsapps.com/start>
      1. **AWS Region:** US-EAST-1
      1. Click "Continue"
   1. In "Sign in to awssenzingsso":
      1. **Username:**  What Ant gave you.
      1. Click "Next"
      1. **Password:**  What Ant gave you.
      1. Click "Sign in"
   1. In "Additional verification required":
      1. **MFA code:**  You are on your own for this one!
      1. Click "Sign in"
   1. In "Allow Kiro IDE to access your data?":
      1. Click "Allow access"

## Configure

On first launch, Kiro walks through initial setup:

1. **Authenticate** — Sign in with GitHub, Google, AWS Builder ID, or AWS IAM Identity Center.
   No AWS account is required.
1. **Import editor settings** — Optionally import VS Code settings, themes, and extensions.
   Skip this step if migrating from a different editor.
   Depending on how many extensions are being imported, this may take a while.
1. **Choose a theme** — Select a preferred appearance.
1. **Enable shell integration** — Allow Kiro to set up shell integration so the agent can
   execute commands on your behalf.

Exit Kiro.

For more details, see the [Kiro documentation](https://kiro.dev/docs/getting-started/).
