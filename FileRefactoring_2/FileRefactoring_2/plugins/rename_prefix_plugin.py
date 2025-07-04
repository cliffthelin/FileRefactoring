import os
import csv
import shutil
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from core.interfaces import ActionPlugin

class RenamePrefixPlugin(ActionPlugin):
    """
    A plugin to rename files by prepending a prefix based on a CSV mapping.
    The CSV should contain two columns: base_filename,prefix
    """
    
    def __init__(self, app_context):
        """
        Initializes the RenamePrefixPlugin.

        Args:
            app_context: The main application instance (FileRefactoringGUI).
        """
        self.app = app_context
        
        self.target_directory_var = tk.StringVar()
        self.csv_path_var = tk.StringVar()
        self.dry_run_var = tk.BooleanVar(value=False)

    def get_name(self) -> str:
        """Returns the user-friendly name of the plugin."""
        return "Rename Prefix"

    def get_value(self) -> str:
        """Returns the internal identifier for the plugin."""
        return "rename_prefix"

    def is_rollbackable(self) -> bool:
        """Returns True as this action logs changes that can be reverted."""
        return True

    def create_gui(self, master) -> None:
        """
        Creates and packs the UI components for the Rename Prefix action.

        Args:
            master: The parent tk/ttk widget to build the UI upon.
        """
        frame = ttk.LabelFrame(master, text="Rename Prefix Options", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)

        ttk.Checkbutton(frame, text="Dry Run (Simulate changes)", variable=self.dry_run_var, bootstyle="round-toggle").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=(0,10))
        
        ttk.Label(frame, text="Target Directory:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.target_directory_var).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=self._browse_folder, bootstyle="outline").grid(row=1, column=2, padx=5)
        
        ttk.Label(frame, text="CSV File (base,prefix):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.csv_path_var).grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=self._browse_csv, bootstyle="outline").grid(row=2, column=2, padx=5)
    
    def validate(self) -> tuple[bool, str]:
        """
        Validates the user's input before execution.

        Returns:
            A tuple (bool, str) indicating success and an optional error message.
        """
        target_dir = self.target_directory_var.get()
        if not target_dir or not os.path.isdir(target_dir):
            return False, "A valid Target Directory is required."
        
        csv_path = self.csv_path_var.get()
        if not csv_path or not os.path.isfile(csv_path):
            return False, "A valid CSV File is required."
            
        return True, ""

    def execute(self) -> None:
        """Executes the core file renaming process."""
        target_directory = self.target_directory_var.get()
        csv_path = self.csv_path_var.get()
        is_dry_run = self.dry_run_var.get()

        self.app.log(f"--- Starting Rename Prefix Action {'(Dry Run)' if is_dry_run else ''} ---")

        try:
            prefix_map = self._read_prefix_map(csv_path)
            if not prefix_map:
                self.app.log("[ERROR] Could not read or process prefix map from CSV.")
                return

            log_path = os.path.join(target_directory, 'file_name_change_log.csv')
            success_count, failure_count = 0, 0

            for filename in os.listdir(target_directory):
                file_path = os.path.join(target_directory, filename)
                if os.path.isfile(file_path):
                    name_part, ext_part = os.path.splitext(filename)
                    
                    # Find the matching prefix key
                    for base_key, prefix in prefix_map.items():
                        if name_part.startswith(base_key):
                            if name_part.startswith(prefix + '_'): # Avoid re-prefixing
                                self.app.log(f"SKIPPING: '{filename}' already seems to have a prefix.")
                                break

                            new_name = f"{prefix}_{filename}"
                            new_path = os.path.join(target_directory, new_name)
                            
                            if is_dry_run:
                                self.app.log(f"DRY RUN: Would rename '{filename}' to '{new_name}'")
                                success_count += 1
                            else:
                                try:
                                    shutil.move(file_path, new_path)
                                    self.app.log(f"SUCCESS: Renamed '{filename}' to '{new_name}'")
                                    self._log_action(log_path, file_path, new_path, 'success', 'rename_prefix')
                                    success_count += 1
                                except Exception as e:
                                    self.app.log(f"FAILURE: Renaming '{filename}'. Reason: {e}")
                                    self._log_action(log_path, file_path, new_path, f'failure - {e}', 'rename_prefix')
                                    failure_count += 1
                            break # Move to the next file after finding a match
            
            self.app.log(f"\n--- Rename Prefix Complete ---")
            Messagebox.show_info("Complete", f"Files prefixed: {success_count}\nFailed or skipped: {failure_count}")

        except Exception as e:
            self.app.log(f"[CRITICAL ERROR] An unexpected error occurred: {e}")
            Messagebox.show_error(f"An unexpected error occurred: {e}", "Critical Error")

    def _read_prefix_map(self, csv_path):
        """Reads the prefix mapping from a CSV file."""
        prefix_map = {}
        try:
            with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if len(row) >= 2:
                        base_filename, prefix = row[0].strip(), row[1].strip()
                        if base_filename and prefix:
                            prefix_map[base_filename] = prefix
        except Exception as e:
            self.app.log(f"Error reading prefix CSV: {e}")
            return None
        return prefix_map

    def _log_action(self, log_path, old_path, new_path, status, action_type):
        """Logs a file operation to the rollback log file."""
        if self.dry_run_var.get():
            return
        
        file_exists = os.path.exists(log_path)
        try:
            with open(log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['timestamp', 'old_path', 'new_path', 'status', 'action_type', 'details'])
                writer.writerow([datetime.now().isoformat(), old_path, new_path, status, action_type, ''])
        except Exception as e:
            self.app.log(f"[ERROR] Could not write to log file '{log_path}'. Reason: {e}")

    def _browse_folder(self):
        """Opens a dialog to select the target directory."""
        path = filedialog.askdirectory(title="Select Target Directory")
        if path:
            self.target_directory_var.set(path)

    def _browse_csv(self):
        """Opens a dialog to select the CSV file."""
        path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if path:
            self.csv_path_var.set(path)