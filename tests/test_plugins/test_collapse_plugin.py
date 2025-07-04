import os
import csv
import shutil
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from core.interfaces import ActionPlugin

class CollapsePlugin(ActionPlugin):
    """
    A plugin to move all files from all subdirectories into their 
    top-level parent folder.
    """
    def __init__(self, app_context):
        self.app = app_context
        self.collapse_folder_var = tk.StringVar()
        self.prepend_path_var = tk.BooleanVar(value=True)
        self.dry_run_var = tk.BooleanVar(value=False)

    def get_name(self) -> str:
        return "Collapse"

    def get_value(self) -> str:
        return "collapse"

    def is_rollbackable(self) -> bool:
        return True

    def create_gui(self, master) -> None:
        """Creates the UI for the Collapse action."""
        frame = ttk.LabelFrame(master, text="Collapse Options", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(frame, text="Dry Run (Simulate changes)", variable=self.dry_run_var, bootstyle="round-toggle").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=(0, 10))
        ttk.Label(frame, text="Parent Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.collapse_folder_var).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=self._browse_folder, bootstyle="outline").grid(row=1, column=2, padx=5)
        ttk.Checkbutton(frame, text="Prepend folder path to filename to avoid conflicts", variable=self.prepend_path_var, bootstyle="round-toggle").grid(row=2, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    
    def validate(self) -> tuple[bool, str]:
        """Validates the inputs for the action."""
        if not self.collapse_folder_var.get() or not os.path.isdir(self.collapse_folder_var.get()):
            return False, "A valid Parent Folder is required."
        return True, ""

    def execute(self) -> None:
        """Executes the collapse folder process."""
        parent_folder = self.collapse_folder_var.get()
        prepend_path = self.prepend_path_var.get()
        is_dry_run = self.dry_run_var.get()
        self.app.log(f"--- Starting Collapse Action {'(Dry Run)' if is_dry_run else ''} ---")
        try:
            log_path = os.path.join(parent_folder, 'file_name_change_log.csv')
            files_to_move = []
            for root, _, files in os.walk(parent_folder):
                if os.path.samefile(root, parent_folder):
                    continue
                for filename in files:
                    files_to_move.append((os.path.join(root, filename), root))
            if not files_to_move:
                self.app.log("No files found in subdirectories to collapse.")
                Messagebox.show_info("No Files Found", "No files were found in any subdirectories.")
                return
            success_count, failure_count = 0, 0
            for source_path, original_root in files_to_move:
                original_filename = os.path.basename(source_path)
                new_filename = original_filename
                if prepend_path:
                    sub_path = os.path.relpath(original_root, parent_folder)
                    safe_sub_path = sub_path.replace(os.sep, '_')
                    new_filename = f"{safe_sub_path}_{original_filename}"
                dest_path = os.path.join(parent_folder, new_filename)
                if not prepend_path and os.path.exists(dest_path):
                    self.app.log(f"FAILURE: Cannot move '{original_filename}'. A file with the same name already exists in the parent folder.")
                    failure_count += 1
                    continue
                if is_dry_run:
                    self.app.log(f"DRY RUN: Would move '{os.path.relpath(source_path, parent_folder)}' to '{new_filename}'")
                    success_count += 1
                else:
                    try:
                        shutil.move(source_path, dest_path)
                        self._log_action(log_path, source_path, dest_path, 'success', 'collapse')
                        success_count += 1
                    except Exception as e:
                        self.app.log(f"FAILURE moving '{original_filename}': {e}")
                        self._log_action(log_path, source_path, dest_path, f'failure - {e}', 'collapse')
                        failure_count += 1
            if not is_dry_run:
                for root, dirs, _ in os.walk(parent_folder, topdown=False):
                    for name in dirs:
                        dir_path = os.path.join(root, name)
                        try:
                            if not os.listdir(dir_path):
                                os.rmdir(dir_path)
                        except OSError as e:
                             self.app.log(f"Could not remove directory '{dir_path}': {e}")
            self.app.log(f"\n--- Collapse Complete ---")
            Messagebox.show_info("Collapse Complete", f"Files moved: {success_count}\nFailures: {failure_count}")
        except Exception as e:
            self.app.log(f"[CRITICAL ERROR] An unexpected error occurred: {e}")

    def _log_action(self, log_path, old_path, new_path, status, action_type):
        if self.dry_run_var.get(): return
        file_exists = os.path.exists(log_path)
        try:
            with open(log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists: writer.writerow(['timestamp', 'old_path', 'new_path', 'status', 'action_type', 'details'])
                writer.writerow([datetime.now().isoformat(), old_path, new_path, status, action_type, ''])
        except Exception as e:
            self.app.log(f"[ERROR] Could not write to log file '{log_path}'. Reason: {e}")

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Select Parent Folder")
        if path:
            self.collapse_folder_var.set(path)
