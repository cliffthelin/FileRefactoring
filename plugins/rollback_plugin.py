import os
import csv
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from core.interfaces import ActionPlugin

class RollbackPlugin(ActionPlugin):
    """
    A plugin to roll back file operations using a change log file.
    """
    def __init__(self, app_context):
        self.app = app_context
        self.source_folder_var = tk.StringVar()
        self.log_file = "file_name_change_log.csv"

    def get_name(self) -> str:
        return "Rollback"

    def get_value(self) -> str:
        return "rollback"

    def is_rollbackable(self) -> bool:
        return False

    def create_gui(self, master) -> None:
        """Creates the UI for the Rollback action."""
        frame = ttk.LabelFrame(master, text="Rollback Options", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)

        # Source Folder
        ttk.Label(frame, text="Folder with Log File:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.source_folder_var).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=self._browse_folder, bootstyle="outline").grid(row=0, column=2, padx=5)
        
        ttk.Label(frame, text=f"This action will look for '{self.log_file}' in the selected folder and revert the changes.", wraplength=300).grid(row=1, column=0, columnspan=3, pady=10)

    def validate(self) -> tuple[bool, str]:
        """Validates the inputs for the action."""
        source_folder = self.source_folder_var.get()
        if not source_folder or not os.path.isdir(source_folder):
            return False, "A valid folder is required."
        
        log_path = os.path.join(source_folder, self.log_file)
        if not os.path.isfile(log_path):
            return False, f"The log file '{self.log_file}' was not found in the selected folder."
        return True, ""

    def execute(self) -> None:
        """Executes the rollback process."""
        source_folder = self.source_folder_var.get()
        log_path = os.path.join(source_folder, self.log_file)
        
        if not Messagebox.yesno(
            f"Are you sure you want to roll back the changes recorded in '{log_path}'?\n\nThis cannot be undone.",
            "Confirm Rollback"
        ):
            self.app.log("Rollback cancelled by user.")
            return

        self.app.log(f"--- Starting Rollback Action ---")
        self.app.log(f"Reading log file: {log_path}")

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # Read all rows and reverse them to process last action first
                log_entries = list(reader)
                log_entries.reverse()

            success_count, failure_count = 0, 0
            for row in log_entries:
                if row.get('status') != 'success':
                    continue
                
                old_path = row.get('old_path')
                new_path = row.get('new_path')
                action_type = row.get('action_type')

                if action_type == 'delete_duplicate':
                    self.app.log(f"SKIPPING rollback for deleted file: '{old_path}'. This action cannot be undone.")
                    failure_count += 1
                    continue

                if not old_path or not new_path:
                    self.app.log(f"SKIPPING invalid log entry: {row}")
                    failure_count += 1
                    continue

                # Ensure parent directory of the old path exists
                old_parent_dir = os.path.dirname(old_path)
                if not os.path.exists(old_parent_dir):
                    os.makedirs(old_parent_dir, exist_ok=True)
                
                try:
                    shutil.move(new_path, old_path)
                    self.app.log(f"SUCCESS: Rolled back '{os.path.basename(new_path)}' to '{os.path.basename(old_path)}'")
                    success_count += 1
                except Exception as e:
                    self.app.log(f"FAILURE rolling back '{new_path}': {e}")
                    failure_count += 1
            
            # Rename the log file to prevent re-running the rollback
            rolled_back_log_path = log_path + f".rolled_back_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.rename(log_path, rolled_back_log_path)
            self.app.log(f"Renamed log file to: {os.path.basename(rolled_back_log_path)}")

            self.app.log(f"\n--- Rollback Complete ---")
            self.app.log(f"Reverted: {success_count} | Failed/Skipped: {failure_count}")
            Messagebox.show_info("Rollback Complete", f"Operations reverted: {success_count}\nFailures/Skipped: {failure_count}")

        except Exception as e:
            self.app.log(f"[CRITICAL ERROR] An unexpected error occurred: {e}")
            Messagebox.show_error(f"An unexpected error occurred: {e}", "Critical Error")

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Select Folder Containing Log File")
        if path:
            self.source_folder_var.set(path)