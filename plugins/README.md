# Plugin Developer's Guide

This guide provides all the information you need to create, test, and integrate new "Action" plugins into the FileRefactoring application.

## The Plugin Architecture

The application's power comes from its modular design. The core application discovers and loads any valid Python module from this `plugins/` directory that contains a class inheriting from `ActionPlugin`. Each plugin is responsible for its own UI, validation, and execution logic.

## The `ActionPlugin` Interface

To be recognized as a valid plugin, your class must inherit from `core.interfaces.ActionPlugin` and implement all of its abstract methods.

```python
from core.interfaces import ActionPlugin

class MyNewPlugin(ActionPlugin):
    # ... implementation ...
```

### Required Methods

Your plugin class **must** implement the following methods:

-   **`__init__(self, app_context)`**
    The constructor for your plugin. It receives one argument:
    -   `app_context`: An instance of the main `FileRefactoringGUI` class. This is your gateway to interacting with the core application. **Store this as `self.app` or `self.context`.**

-   **`get_name(self) -> str`**
    Return the user-friendly display name for your plugin's radio button.
    *Example:* `"My Awesome Feature"`

-   **`get_value(self) -> str`**
    Return a unique, simple, lowercase string that acts as an internal ID for your plugin.
    *Example:* `"my_awesome_feature"`

-   **`is_rollbackable(self) -> bool`**
    Return `True` if your action modifies files *and* logs its changes to the `file_name_change_log.csv`. If it's a non-destructive action (like listing files) or cannot be safely rolled back, return `False`. This controls the display of the "⮌" symbol in the UI.

-   **`create_gui(self, master)`**
    This is where you build the UI for your plugin.
    -   `master`: A `ttk.Frame` widget provided by the core app. Build all your UI elements (labels, entries, buttons) inside this `master` frame.

-   **`validate(self) -> tuple[bool, str]`**
    This method is called before `execute()`. It should check all user inputs.
    -   If validation passes, return `(True, "")`.
    -   If validation fails, return `(False, "Your error message here")`. The error message will be shown to the user in a popup.

-   **`execute(self)`**
    This is the heart of your plugin. Place all your core file processing and business logic here.

## Connecting to the Core App: Logging and More

Your plugin is not an island. It communicates with the core application through the `app_context` object passed to its `__init__` method.

### Centralized Logging

**All logging must be done through the application context.** This ensures your plugin's messages appear in the main application log window consistently with all other plugins.

To log a message from within your plugin's `execute` method (or any other method):

```python
# Assuming you stored the context in __init__: self.app = app_context
self.app.log("This is a message from my plugin!")
self.app.log(f"Processing file: {filename}")
```