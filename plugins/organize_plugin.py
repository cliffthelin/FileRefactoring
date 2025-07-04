import os
import csv
import shutil
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from core.interfaces import ActionPlugin

class OrganizePlugin(ActionPlugin):
    """
    A plugin for organizing files into a folder structure
    based on a delimiter in their names.
    """
    def __init__(self, app_context):
        self.app = app_context
        self.source_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.delimiter_var = tk.StringVar(value="-")
        self.recursive_var = tk.BooleanVar(value=True)
        self.dry_run_var = tk.BooleanVar(value=False)

    def get_name(self) -> str:
        return "Organize"

    def get_value(self) -> str:
        return "organize"
    
    def is_rollbackable(self) -> bool:
        return True

    def create_gui(self, master) -> None:
        frame = ttk.LabelFrame(master, text="Organize Options", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(frame, text="Dry Run (Simulate changes)", variable=self.dry_run_var, bootstyle="round-toggle").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=(0,10))
        ttk.Label(frame, text="Source Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.source_folder_var).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=lambda: self._browse_folder(self.source_folder_var), bootstyle="outline").grid(row=1, column=2, padx=5)
        ttk.Label(frame, text="Output Folder:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.output_folder_var).grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=lambda: self._browse_folder(self.output_folder_var), bootstyle="outline").grid(row=2, column=2, padx=5)
        ttk.Label(frame, text="Delimiter:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.delimiter_var, width=5).grid(row=3, column=1, sticky="w", padx=5)
        ttk.Checkbutton(frame, text="Search in subfolders (Recursive)", variable=self.recursive_var, bootstyle="round-toggle").grid(row=4, column=0, columnspan=3, sticky='w', padx=5, pady=5)
    
    def validate(self) -> tuple[bool, str]:
        if not self.source_folder_var.get() or not os.path.isdir(self.source_folder_var.get()):
            return False, "A valid Source Folder is required."
        if not self.output_folder_var.get():
            self.output_folder_var.set(self.source_folder_var.get())
        if not self.delimiter_var.get():
            return False, "A Delimiter is required."
        return True, ""

    def execute(self) -> None:
        source_folder = self.source_folder_var.get()
        output_folder = self.output_folder_var.get()
        delimiter = self.delimiter_var.get()
        is_recursive = self.recursive_var.get()
        is_dry_run = self.dry_run_var.get()
        self.app.log(f"--- Starting Organize Action {'(Dry Run)' if is_dry_run else ''} ---")
        try:
            files_to_process = self._collect_files(source_folder, is_recursive)
            if not files_to_process:
                self.app.log("No files found to organize.")
                Messagebox.show_info("No Files", "No files were found in the source directory.")
                return
            log_path = os.path.join(source_folder, 'file_name_change_log.csv')
            success_count, failure_count = 0, 0
            for filepath in files_to_process:
                filename = os.path.basename(filepath)
                name_parts = os.path.splitext(filename)[0].split(delimiter)
                if len(name_parts) > 1:
                    dest_subdirs = name_parts[:-1]
                    new_filename = name_parts[-1] + os.path.splitext(filename)[1]
                    dest_dir_path = os.path.join(output_folder, *dest_subdirs)
                    dest_file_path = os.path.join(dest_dir_path, new_filename)
                    if is_dry_run:
                        self.app.log(f"DRY RUN: Would move '{filename}' to '{os.path.relpath(dest_file_path, output_folder)}'")
                        success_count += 1
                    else:
                        try:
                            os.makedirs(dest_dir_path, exist_ok=True)
                            shutil.move(filepath, dest_file_path)
                            self.app.log(f"SUCCESS: Moved '{filename}' to '{os.path.relpath(dest_dir_path, output_folder)}'")
                            self._log_action(log_path, filepath, dest_file_path, 'success', 'organize')
                            success_count += 1
                        except Exception as e:
                            self.app.log(f"FAILURE moving '{filename}'. Reason: {e}")
                            self._log_action(log_path, filepath, dest_file_path, f'failure - {e}', 'organize')
                            failure_count += 1
                else:
                    self.app.log(f"SKIPPING '{filename}': No delimiter found.")
            self.app.log(f"\n--- Organize Complete ---")
            self.app.log(f"Successful: {success_count} | Failed: {failure_count}")
            Messagebox.show_info("Organize Complete", f"Moved: {success_count}\nFailed/Skipped: {failure_count}")
        except Exception as e:
            self.app.log(f"[CRITICAL ERROR] An unexpected error occurred: {e}")
            Messagebox.show_error(f"An unexpected error occurred: {e}", "Critical Error")

    def _collect_files(self, source_folder, is_recursive):
        file_list = []
        if is_recursive:
            for root, _, files in os.walk(source_folder):
                for name in files:
                    file_list.append(os.path.join(root, name))
        else:
            for name in os.listdir(source_folder):
                path = os.path.join(source_folder, name)
                if os.path.isfile(path):
                    file_list.append(path)
        return file_list

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

    def _browse_folder(self, string_var):
        path = filedialog.askdirectory(title="Select Folder")
        if path:
            string_var.set(path)