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

## Follow the Senzing Bootcamp

In Kiro's agentic chat, enter the following to begin the bootcamp:

```console
Start the bootcamp
```

Kiro's agentic chat will guide you through the Bootcamp.

Helpful prompts that can be entered any time:

```console
Where am I in the bootcamp?
```

```console
What's next?
```

```console
Why am I doing this?
```

```console
What was done?
```

```console
Why did you do that?
```

```console
What does ____ mean?
```

```console
Where did you put ____?
```

```console
Generate an HTML visualization
```

To report a bug or improvement:

```console
Bootcamp Feedback:  _____
```

## Save Bootcamp artifacts

After completing the bootcamp, save any artifacts of interest.
All artifacts created by the Senzing Bootcamp are in the Kiro project directory.

1. To save bootcamp artifacts into a single compressed file, prompt:

   ```console
   Backup the bootcamp
   ```

   Move the file to a location outside of the project directory.

1. To save all of your prompts:

   ```console
   Export all prompts and their effects into a markdown file
   ```

   Move the file to a location outside of the project directory.

## Clean up the Bootcamp

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
