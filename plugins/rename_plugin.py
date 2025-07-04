import os
import csv
import shutil
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from core.interfaces import ActionPlugin

class RenamePlugin(ActionPlugin):
    """A plugin for bulk renaming files based on a CSV mapping."""
    
    def __init__(self, app_context):
        self.app = app_context
        self.source_folder_var = tk.StringVar()
        self.csv_path_var = tk.StringVar()
        self.dry_run_var = tk.BooleanVar(value=False)

    def get_name(self) -> str:
        return "Rename"

    def get_value(self) -> str:
        return "rename"

    def is_rollbackable(self) -> bool:
        return True

    def create_gui(self, master) -> None:
        frame = ttk.LabelFrame(master, text="Rename Options", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(frame, text="Dry Run (Simulate changes)", variable=self.dry_run_var, bootstyle="round-toggle").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=(0,10))
        ttk.Label(frame, text="Source Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.source_folder_var).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=self._browse_source_folder, bootstyle="outline").grid(row=1, column=2, padx=5)
        ttk.Label(frame, text="CSV File:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.csv_path_var).grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=self._browse_csv, bootstyle="outline").grid(row=2, column=2, padx=5)
    
    def validate(self) -> tuple[bool, str]:
        source_folder = self.source_folder_var.get()
        if not source_folder or not os.path.isdir(source_folder):
            return False, "A valid Source Folder is required."
        csv_path = self.csv_path_var.get()
        if not csv_path or not os.path.isfile(csv_path):
            return False, "A valid CSV File is required."
        return True, ""

    def execute(self) -> None:
        source_folder = self.source_folder_var.get()
        csv_path = self.csv_path_var.get()
        is_dry_run = self.dry_run_var.get()
        self.app.log(f"--- Starting Rename Action {'(Dry Run)' if is_dry_run else ''} ---")
        try:
            file_mapping = self._read_csv_mapping(csv_path)
            if not file_mapping:
                Messagebox.show_error("Could not read or process the CSV file.", "CSV Error")
                return
            log_path = os.path.join(source_folder, 'file_name_change_log.csv')
            success_count, failure_count = 0, 0
            for index, row in enumerate(file_mapping):
                original_name = row.get('original_filename') or row.get('original_file_name')
                new_name = row.get('new_filename') or row.get('new_file_name')
                if not original_name or not new_name:
                    self.app.log(f"SKIPPING row {index+2}: Missing original or new filename.")
                    failure_count += 1
                    continue
                original_path = os.path.join(source_folder, original_name)
                if os.path.exists(original_path):
                    new_path = os.path.join(source_folder, new_name)
                    if is_dry_run:
                        self.app.log(f"DRY RUN: Would rename '{original_name}' to '{new_name}'")
                        success_count += 1
                    else:
                        try:
                            shutil.move(original_path, new_path)
                            self.app.log(f"SUCCESS: Renamed '{original_name}' to '{new_name}'")
                            self._log_action(log_path, original_path, new_path, 'success', 'rename')
                            success_count += 1
                        except Exception as e:
                            self.app.log(f"FAILURE: Renaming '{original_name}'. Reason: {e}")
                            self._log_action(log_path, original_path, new_path, f'failure - {e}', 'rename')
                            failure_count += 1
                else:
                    failure_count += 1
            self.app.log(f"\n--- Rename Complete ---")
            Messagebox.show_info("Rename Complete", f"Successful: {success_count}\nFailed: {failure_count}")
        except Exception as e:
            self.app.log(f"[CRITICAL ERROR] An unexpected error occurred: {e}")
            Messagebox.show_error(f"An unexpected error occurred: {e}", "Critical Error")

    def _read_csv_mapping(self, csv_path):
        try:
            with open(csv_path, mode='r', encoding='utf-8-sig') as infile:
                reader = csv.DictReader(infile)
                reader.fieldnames = [name.lower().replace(' ', '_') for name in reader.fieldnames]
                return list(reader)
        except Exception as e:
            self.app.log(f"Error reading CSV file: {e}")
            return None

    def _log_action(self, log_path, old_path, new_path, status, action_type):
        if self.dry_run_var.get(): return
        file_exists = os.path.exists(log_path)
        try:
            with open(log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['timestamp', 'old_path', 'new_path', 'status', 'action_type', 'details'])
                writer.writerow([datetime.now().isoformat(), old_path, new_path, status, action_type, ''])
        except Exception as e:
            self.app.log(f"[ERROR] Could not write to log file '{log_path}'. Reason: {e}")

    def _browse_source_folder(self):
        path = filedialog.askdirectory(title="Select Source Folder")
        if path: self.source_folder_var.set(path)

    def _browse_csv(self):
        path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if path: self.csv_path_var.set(path)