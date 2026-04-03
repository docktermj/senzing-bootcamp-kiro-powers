# Senzing Kiro Power

This repository contains the Senzing Boot Camp Kiro Power and its development documentation.

## Prerequisites

1. [Install Kiro](docs/install-kiro.md)

## Install the Senzing Boot Camp Power

1. In Kiro's left-hand icon bar, click on the **Powers** icon.
1. In the **Powers** panel, under **Installed**, click on "Add Custom Power".
1. Select "Import power from GitHub"
1. Enter the following GitHub repository URL:

   ```text
   https://github.com/docktermj/senzing-bootcamp-kiro-powers/tree/main/senzing-bootcamp
   ```

## Start the Senzing Boot Camp

1. Start Kiro in a new, empty directory.
   Example:

    ```console
    mkdir senzing-bootcamp
    cd senzing-bootcamp
    kiro .
    ```

1. In Kiro's agentic chat, say **"Start the boot camp"** to begin.

## Clean up the Boot Camp

After completing the boot camp, save any artifacts of interest.
All artifacts created by the Senzing Boot Camp are in the Kiro project directory.

1. **(Optional) Remove the Senzing Boot Camp Power:**
   1. In Kiro's left-hand icon bar, click on the **Powers** icon.
   1. In the **Powers** panel, under **Installed**, find "Senzing Boot Camp".
   1. In the **Power: Senzing Boot Camp** panel, click the **Uninstall** button.

1. **Delete the Senzing Boot Camp project directory.**

   - **Linux / macOS:**

     ```console
     rm -rf senzing-bootcamp
     ```

   - **Windows (Command Prompt):**

     ```console
     rmdir /s /q senzing-bootcamp
     ```

   - **Windows (PowerShell):**

     ```powershell
     Remove-Item -Recurse -Force senzing-bootcamp
     ```
