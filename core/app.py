import os
import io
import sys
import tkinter as tk
from tkinter import Toplevel
import unittest
import glob
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledText

# Add the project's root directory to the system path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import run_tests
from core.plugin_manager import PluginManager

# --- Helper Classes ---
class CollapsiblePane(ttk.Frame):
    """A collapsible pane widget for tkinter."""
    def __init__(self, parent, text="", start_expanded=True):
        super().__init__(parent)
        self.columnconfigure(1, weight=1)
        self._is_expanded = tk.BooleanVar(value=start_expanded)
        self.header_frame = ttk.Frame(self)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.toggle_button = ttk.Button(self.header_frame, text="▼" if start_expanded else "►", width=2, command=self.toggle, bootstyle="outline-toolbutton")
        self.toggle_button.pack(side="left")
        ttk.Label(self.header_frame, text=text, font=("-weight bold")).pack(side="left", padx=5)
        self.sub_frame = ttk.Frame(self)
        if start_expanded:
            self.sub_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

    def toggle(self, collapse=None):
        if collapse is not None:
            self._is_expanded.set(not collapse)
        if self._is_expanded.get():
            self.sub_frame.grid_remove()
            self.toggle_button.config(text="►")
            self._is_expanded.set(False)
        else:
            self.sub_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
            self.toggle_button.config(text="▼")
            self._is_expanded.set(True)

class TestCenterWindow(Toplevel):
    """A dedicated window for viewing and running the application's test suite."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Test Center")
        self.geometry("1000x700")
        
        self._create_widgets()
        self._refresh_log_list()

    def _create_widgets(self):
        """Creates the layout and widgets for the Test Center."""
        top_controls = ttk.Frame(self, padding=(10, 10, 10, 0))
        top_controls.pack(fill=tk.X, side=tk.TOP)
        ttk.Button(top_controls, text="Run All Tests", command=self._run_all_tests, bootstyle="success").pack(side=tk.RIGHT)
        ttk.Button(top_controls, text="Refresh Logs", command=self._refresh_log_list).pack(side=tk.RIGHT, padx=5)

        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        list_frame = ttk.Frame(main_paned_window, padding=5)
        ttk.Label(list_frame, text="Test Run History", font="-weight bold").pack(pady=5, anchor="w")
        self.history_listbox = tk.Listbox(list_frame)
        self.history_listbox.pack(fill=tk.BOTH, expand=True)
        self.history_listbox.bind("<<ListboxSelect>>", self._on_history_select)
        main_paned_window.add(list_frame, weight=2)

        results_frame = ttk.Frame(main_paned_window, padding=5)
        ttk.Label(results_frame, text="Log Viewer", font="-weight bold").pack(pady=5, anchor="w")
        self.results_text = ScrolledText(results_frame, wrap=tk.WORD, state='disabled', font=('Consolas', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        main_paned_window.add(results_frame, weight=5)

    def _refresh_log_list(self):
        """Loads log files and populates the history listbox."""
        self.history_listbox.delete(0, tk.END)
        os.makedirs(run_tests.LOG_DIR, exist_ok=True)
        log_files = sorted(glob.glob(os.path.join(run_tests.LOG_DIR, "*.log")), reverse=True)
        for log_file in log_files:
            self.history_listbox.insert(tk.END, os.path.basename(log_file))
        
        if self.history_listbox.size() > 0:
            self.history_listbox.selection_set(0)
            self._on_history_select(None)

    def _on_history_select(self, event):
        """Handles selection of a specific test run from the history list."""
        if not self.history_listbox.curselection():
            return
        
        selected_file = self.history_listbox.get(self.history_listbox.curselection())
        log_path = os.path.join(run_tests.LOG_DIR, selected_file)

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.results_text.text.config(state='normal')
            self.results_text.text.delete('1.0', tk.END)
            self.results_text.text.insert('1.0', content)
            self.results_text.text.config(state='disabled')
        except Exception as e:
            self.results_text.text.config(state='normal')
            self.results_text.text.delete('1.0', tk.END)
            self.results_text.text.insert('1.0', f"Error reading log file:\n{e}")
            self.results_text.text.config(state='disabled')

    def _run_all_tests(self):
        """Runs the test suite, saves the log, and refreshes the view."""
        self.results_text.text.config(state='normal')
        self.results_text.text.delete('1.0', tk.END)
        self.results_text.text.insert('1.0', "Running tests, please wait...")
        self.results_text.text.config(state='disabled')
        self.update_idletasks()

        output, was_successful = run_tests.run_suite_and_get_output()
        run_tests.save_log_file(output)
        
        self.results_text.text.config(state='normal')
        self.results_text.text.delete('1.0', tk.END)
        self.results_text.text.insert('1.0', output)
        self.results_text.text.config(state='disabled')

        self._refresh_log_list()

class FileRefactoringGUI:
    """
    The main graphical user interface for the FileRefactoring application.
    """
    
    README_TEXT = """
# FileRefactoring (Plugin-Based Architecture)

This application provides a powerful and extensible graphical interface for performing complex file management tasks. This modular design allows for easy maintenance and enables developers to add new features without altering the core application.

## Functionality Overview

The application discovers and loads "Action" plugins from the `plugins/` directory. Each plugin is a self-contained module that provides a specific functionality.

-   **Rename:** Bulk rename files using a CSV mapping.
-   **Rename Prefix:** Prepend a prefix to filenames based on a CSV.
-   **Organize:** Move files into a folder structure based on a delimiter in their names.
-   **Search & Organize:** Find files containing specific terms and move them into dedicated folders.
-   **Collapse:** Move all files from all subdirectories into their parent folder.
-   **Replace:** Find and replace a string in filenames or extensions, with Regex support.
-   **List Files:** Generate a report of files in a directory.
-   **Filter & Sort:** Find and list files based on multiple criteria.
-   **Find Duplicates:** Scan for duplicate files by size, name, or content hash.
-   **Rollback:** Revert changes made by other actions using the generated log file.
"""

    def __init__(self, root):
        self.root = root
        self.root.title("FileRefactoring (Plugin Architecture)")
        self.root.geometry("1100x800")
        self.active_plugin_frame = None
        self.plugin_frames = {}
        self.plugins = {}
        self.plugin_names = []
        self._create_widgets()
        self.log("Welcome! Application core loaded.")
        self._load_plugins()

    def _create_widgets(self):
        self._create_menu()
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.left_pane = ttk.Frame(self.paned_window, padding=10)
        self.right_pane = ttk.Frame(self.paned_window, padding=10)
        self.paned_window.add(self.left_pane, weight=1)
        self.paned_window.add(self.right_pane, weight=2)
        self.left_pane.rowconfigure(3, weight=1)
        self.left_pane.columnconfigure(0, weight=1)
        self.run_button = ttk.Button(self.left_pane, text="Run Action", command=self.run_action, bootstyle="primary")
        self.run_button.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.readme_pane = CollapsiblePane(self.left_pane, text="README", start_expanded=True)
        self.readme_pane.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        readme_text = tk.Text(self.readme_pane.sub_frame, wrap=tk.WORD, relief="flat", height=12, font=("", 10))
        readme_text.pack(fill="both", expand=True)
        readme_text.insert("1.0", self.README_TEXT)
        readme_text.config(state="disabled")
        action_selection_frame = ttk.Frame(self.left_pane)
        action_selection_frame.grid(row=2, column=0, sticky="ew", pady=5)
        ttk.Label(action_selection_frame, text="Action:", font="-weight bold").pack(side=tk.LEFT, padx=(0, 5))
        self.action_var = tk.StringVar()
        self.action_combobox = ttk.Combobox(action_selection_frame, textvariable=self.action_var, state="readonly")
        self.action_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.action_combobox.bind("<<ComboboxSelected>>", self._on_action_change)
        self.plugin_options_container = ttk.Frame(self.left_pane)
        self.plugin_options_container.grid(row=3, column=0, sticky="nsew")
        self.right_pane.rowconfigure(0, weight=1)
        self.right_pane.columnconfigure(0, weight=1)
        self.log_pane = ttk.LabelFrame(self.right_pane, text="Application Log", padding=10)
        self.log_pane.grid(row=0, column=0, sticky="nsew")
        self.log_text = ScrolledText(self.log_pane, wrap=tk.WORD, state='disabled', font=('Consolas', 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Open Test Center", command=self.open_test_center)
        menubar.add_cascade(label="Tools", menu=tools_menu)

    def open_test_center(self):
        TestCenterWindow(self.root)

    def _load_plugins(self):
        self.log("Searching for plugins...")
        manager = PluginManager()
        manager.discover_plugins(self) 
        loaded_plugins = manager.get_all_plugins()
        if not loaded_plugins:
            self.log("No plugins found. Place plugin files in the 'plugins' directory.")
            return
        self.log(f"Found {len(loaded_plugins)} plugin(s).")
        loaded_plugins.sort(key=lambda p: p.get_name())
        self.plugins.clear()
        self.plugin_names.clear()
        for plugin in loaded_plugins:
            plugin_name = plugin.get_name()
            if plugin.is_rollbackable(): plugin_name += " ⮌"
            self.plugins[plugin_name] = plugin
            self.plugin_names.append(plugin_name)
            frame = ttk.Frame(self.plugin_options_container)
            plugin.create_gui(frame)
            self.plugin_frames[plugin_name] = frame
        self.action_combobox['values'] = self.plugin_names
        if self.plugin_names:
            self.action_combobox.current(0)
            self._on_action_change(None)

    def _on_action_change(self, event):
        selected_action_name = self.action_var.get()
        if self.readme_pane._is_expanded.get():
            self.readme_pane.toggle(collapse=True)
        if self.active_plugin_frame:
            self.active_plugin_frame.pack_forget()
        new_frame = self.plugin_frames.get(selected_action_name)
        if new_frame:
            new_frame.pack(fill=tk.BOTH, expand=True)
            self.active_plugin_frame = new_frame
            
    def run_action(self):
        selected_action_name = self.action_var.get()
        plugin = self.plugins.get(selected_action_name)
        if not plugin:
            Messagebox.show_error("Could not find the selected plugin.", "Error")
            return
        is_valid, msg = plugin.validate()
        if not is_valid:
            Messagebox.show_error(msg, "Validation Error")
            return
        try:
            plugin.execute()
        except Exception as e:
            error_msg = f"A critical error occurred in plugin '{plugin.get_name()}': {e}"
            self.log(f"[CRITICAL] {error_msg}")
            Messagebox.show_error(error_msg, "Plugin Execution Error")

    def log(self, message):
        self.log_text.text.config(state='normal')
        self.log_text.text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.text.see(tk.END)
        self.log_text.text.config(state='disabled')
