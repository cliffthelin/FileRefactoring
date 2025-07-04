# FileRefactoring (Plugin-Based Architecture)

## Overview

This application provides a powerful and extensible graphical interface for performing complex file management tasks. Originally a monolithic script, it has been refactored into a modern, plugin-based architecture. This design allows for easy maintenance and enables developers to add new file manipulation features without altering the core application.

The core application is responsible for creating the main window, managing the user interface, and dynamically discovering and loading "Action" plugins from the `plugins/` directory. Each plugin is a self-contained module that provides a specific functionality, such as "Rename," "Organize," or "Find Duplicates."

## Tech Stack & Dependencies

The application is built entirely in Python and relies on the following key libraries:

-   **Tkinter:** The standard Python interface to the Tcl/Tk GUI toolkit, used for the basic windowing framework.
-   **ttkbootstrap:** A modern theme extension for tkinter that provides professional-looking and customizable widgets. It greatly simplifies the process of creating a visually appealing GUI.
-   **tkinterdnd2:** An extension that provides drag-and-drop support for tkinter widgets, allowing users to easily drop files and folders onto the application.
-   **pyfakefs:** (For testing only) A fake file system library used in the unit tests to simulate file operations in memory, avoiding any interaction with the real disk.

### Dependencies Installation

To run the application or its tests, you must install the required packages. You can do this using pip:

```bash
pip install ttkbootstrap tkinterdnd2 pyfakefs
```

## How to Run the Application

1.  Ensure all dependencies are installed.
2.  Navigate to the project's root directory in your terminal.
3.  Run the `main.py` script:
    ```bash
    python main.py
    ```

## Core Application Updates

The core application logic resides in the `core/` directory. Updates should be approached with caution to maintain backward compatibility with the plugin interface.

* **`core/app.py`**: Contains the main `FileRefactoringGUI` class. Changes to the UI or main window logic are made here.
* **`core/plugin_manager.py`**: Manages plugin discovery. This should only be modified if the fundamental discovery process needs to change.
* **`core/interfaces.py`**: **This is the most critical file for plugin compatibility.** The `ActionPlugin` abstract base class defines the contract all plugins must adhere to. Modifying this interface will likely require updating all existing plugins.

## Integrated Testing

The application includes a built-in, dynamic self-test suite.

* **Run from the GUI:** Launch the application and navigate to `Tools > Open Test Center`. You can view and run all discovered tests from this window.
* **Run from Command Line:** Execute the `run_tests.py` script from the root directory for a detailed console output. This is ideal for CI/CD or automated checks.
    ```bash
    python run_tests.py
    ```
* **Run on Startup:** Launch the application with the `--test` flag to automatically open the Test Center when the program starts.
    ```bash
    python main.py --test
    ```