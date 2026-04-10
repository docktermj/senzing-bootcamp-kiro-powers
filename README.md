# Senzing Kiro Power

This repository contains the Senzing Bootcamp Kiro Power and its development documentation.

## Prerequisites

1. [Install Kiro](docs/install-kiro.md)

## Start Kiro in a Senzing Bootcamp directory

1. From a terminal window, start Kiro in a new, empty directory.
   Example:

    ```console
    mkdir senzing-bootcamp
    cd senzing-bootcamp
    kiro .
    ```

## Choose the model

1. In Kiro's agentic chat, switch from "Auto" to "Claude Opus 4.6".

## Install the Senzing Bootcamp Power

1. In Kiro's left-hand icon bar, click on the **Powers** icon.
1. In the **Powers** panel, under **Installed**, click on "Add Custom Power".
1. Select "Import power from GitHub"
1. Enter the following GitHub repository URL:

   ```text
   https://github.com/docktermj/senzing-bootcamp-kiro-powers/tree/main/senzing-bootcamp
   ```

1. In Kiro's agentic chat, say **"Start the bootcamp"** to begin.

## Follow the Senzing Bootcamp

Kiro's agentic chat panel will guide you through the Bootcamp.

## Clean up the Bootcamp

After completing the bootcamp, save any artifacts of interest.
All artifacts created by the Senzing Bootcamp are in the Kiro project directory.

1. **(Optional) Remove the Senzing Bootcamp Power:**
   1. In Kiro's left-hand icon bar, click on the **Powers** icon.
   1. In the **Powers** panel, under **Installed**, find "Senzing Bootcamp".
   1. In the **Power: Senzing Bootcamp** panel, click the **Uninstall** button.

1. **Delete the Senzing Bootcamp project directory.**

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
