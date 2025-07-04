import os
import csv
import re
import shutil
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from core.interfaces import ActionPlugin

class ReplacePlugin(ActionPlugin):
    """
    A plugin to find and replace a string in filenames or extensions,
    with optional support for regular expressions.
    """
    def __init__(self, app_context):
        self.app = app_context
        
        # UI Variables
        self.source_folder_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=True)
        self.use_regex_var = tk.BooleanVar(value=False)
        self.find_var = tk.StringVar()
        self.replace_with_var = tk.StringVar()
        self.target_var = tk.StringVar(value="name")
        self.dry_run_var = tk.BooleanVar(value=False)

    def get_name(self) -> str:
        return "Replace"

    def get_value(self) -> str:
        return "replace"
    
    def is_rollbackable(self) -> bool:
        return True

    def create_gui(self, master) -> None:
        frame = ttk.LabelFrame(master, text="Replace Options", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(frame, text="Dry Run (Simulate changes)", variable=self.dry_run_var, bootstyle="round-toggle").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=(0, 10))
        ttk.Label(frame, text="Source Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.source_folder_var).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=self._browse_folder, bootstyle="outline").grid(row=1, column=2, padx=5)
        ttk.Checkbutton(frame, text="Include Subfolders", variable=self.recursive_var, bootstyle="round-toggle").grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(frame, text="Use Regular Expressions (Regex)", variable=self.use_regex_var, bootstyle="round-toggle").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        ttk.Label(frame, text="Find this text:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.find_var).grid(row=3, column=1, columnspan=2, sticky="ew", padx=5)
        ttk.Label(frame, text="Replace with:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.replace_with_var).grid(row=4, column=1, columnspan=2, sticky="ew", padx=5)
        target_frame = ttk.Frame(frame)
        target_frame.grid(row=5, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        ttk.Label(target_frame, text="Apply to:").pack(side="left")
        ttk.Radiobutton(target_frame, text="File Name", variable=self.target_var, value="name", bootstyle="toolbutton").pack(side="left", padx=5)
        ttk.Radiobutton(target_frame, text="Extension only", variable=self.target_var, value="ext", bootstyle="toolbutton").pack(side="left", padx=5)

    def validate(self) -> tuple[bool, str]:
        if not self.source_folder_var.get() or not os.path.isdir(self.source_folder_var.get()):
            return False, "A valid Source Folder is required."
        if not self.find_var.get():
            return False, "The 'Find this text' field cannot be empty."
        if self.use_regex_var.get():
            try:
                re.compile(self.find_var.get())
            except re.error as e:
                return False, f"Invalid Regex pattern: {e}"
        return True, ""

    def execute(self) -> None:
        source_folder = self.source_folder_var.get()
        find_str = self.find_var.get()
        replace_str = self.replace_with_var.get()
        is_recursive = self.recursive_var.get()
        use_regex = self.use_regex_var.get()
        target = self.target_var.get()
        is_dry_run = self.dry_run_var.get()
        self.app.log(f"--- Starting Replace Action {'(Dry Run)' if is_dry_run else ''} ---")
        try:
            files_to_process = self._collect_files(source_folder, is_recursive)
            log_path = os.path.join(source_folder, 'file_name_change_log.csv')
            success_count, failure_count, skipped_count = 0, 0, 0
            for filepath in files_to_process:
                original_filename = os.path.basename(filepath)
                name, ext = os.path.splitext(original_filename)
                new_name, new_ext = name, ext
                if target == 'name':
                    if use_regex: new_name = re.sub(find_str, replace_str, name)
                    else: new_name = name.replace(find_str, replace_str)
                elif target == 'ext':
                    ext_no_dot = ext[1:] if ext.startswith('.') else ext
                    if use_regex: new_ext_no_dot = re.sub(find_str, replace_str, ext_no_dot)
                    else: new_ext_no_dot = ext_no_dot.replace(find_str, replace_str)
                    new_ext = f".{new_ext_no_dot}" if new_ext_no_dot else ""
                new_filename = new_name + new_ext
                if new_filename == original_filename:
                    skipped_count += 1
                    continue
                source_path = os.path.join(os.path.dirname(filepath), original_filename)
                dest_path = os.path.join(os.path.dirname(filepath), new_filename)
                if is_dry_run:
                    self.app.log(f"DRY RUN: Would rename '{original_filename}' to '{new_filename}'")
                    success_count += 1
                else:
                    try:
                        shutil.move(source_path, dest_path)
                        self._log_action(log_path, source_path, dest_path, 'success', 'replace')
                        success_count += 1
                    except Exception as e:
                        self.app.log(f"FAILURE renaming '{original_filename}': {e}")
                        self._log_action(log_path, source_path, dest_path, f'failure - {e}', 'replace')
                        failure_count += 1
            self.app.log(f"\n--- Replace Complete ---")
            Messagebox.show_info("Replace Complete", f"Files renamed: {success_count}\nFailures: {failure_count}\nUnchanged: {skipped_count}")
        except Exception as e:
            self.app.log(f"[CRITICAL ERROR] An unexpected error occurred: {e}")

    def _collect_files(self, source_folder, is_recursive):
        file_list = []
        if is_recursive:
            for root, _, files in os.walk(source_folder):
                for name in files: file_list.append(os.path.join(root, name))
        else:
            for name in os.listdir(source_folder):
                path = os.path.join(source_folder, name)
                if os.path.isfile(path): file_list.append(path)
        return file_list

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
        path = filedialog.askdirectory(title="Select Source Folder")
        if path: self.source_folder_var.set(path)