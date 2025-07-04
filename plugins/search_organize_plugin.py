import os
import csv
import shutil
import tkinter as tk
from tkinter import filedialog, scrolledtext
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from core.interfaces import ActionPlugin

class SearchOrganizePlugin(ActionPlugin):
    """
    A plugin to find files containing specific search terms and
    move them into folders named after those terms.
    """
    def __init__(self, app_context):
        self.app = app_context
        self.source_folder_var = tk.StringVar()
        self.output_folder_var = tk.StringVar()
        self.search_terms_file_var = tk.StringVar()
        self.dry_run_var = tk.BooleanVar(value=False)

    def get_name(self) -> str:
        return "Search & Organize"

    def get_value(self) -> str:
        return "search_organize"

    def is_rollbackable(self) -> bool:
        return True

    def create_gui(self, master) -> None:
        frame = ttk.LabelFrame(master, text="Search & Organize Options", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(frame, text="Dry Run (Simulate changes)", variable=self.dry_run_var, bootstyle="round-toggle").grid(row=0, column=0, columnspan=3, sticky='w', padx=5, pady=(0, 10))
        ttk.Label(frame, text="Source Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.source_folder_var).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=lambda: self._browse_folder(self.source_folder_var), bootstyle="outline").grid(row=1, column=2, padx=5)
        ttk.Label(frame, text="Output Directory:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.output_folder_var).grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=lambda: self._browse_folder(self.output_folder_var), bootstyle="outline").grid(row=2, column=2, padx=5)
        ttk.Label(frame, text="Search Terms (one per line):").grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 2))
        self.search_terms_text = scrolledtext.ScrolledText(frame, height=5, wrap=tk.WORD)
        self.search_terms_text.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5)
        ttk.Label(frame, text="Or load from file (.txt or .csv):").grid(row=5, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 2))
        ttk.Entry(frame, textvariable=self.search_terms_file_var, state="readonly").grid(row=6, column=0, columnspan=2, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=self._browse_search_terms_file, bootstyle="outline").grid(row=6, column=2, padx=5)
    
    def validate(self) -> tuple[bool, str]:
        if not self.source_folder_var.get() or not os.path.isdir(self.source_folder_var.get()):
            return False, "A valid Source Folder is required."
        if not self.output_folder_var.get():
            self.output_folder_var.set(self.source_folder_var.get())
        if not self._get_search_terms():
            return False, "At least one search term is required, either in the text box or from a file."
        return True, ""

    def execute(self) -> None:
        source_folder = self.source_folder_var.get()
        output_folder = self.output_folder_var.get()
        search_terms = self._get_search_terms()
        is_dry_run = self.dry_run_var.get()
        self.app.log(f"--- Starting Search & Organize {'(Dry Run)' if is_dry_run else ''} ---")
        try:
            log_path = os.path.join(source_folder, 'file_name_change_log.csv')
            
            moved_files = set()
            all_files = [f for f in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, f))]
            
            success_count, failure_count = 0, 0
            for term in search_terms:
                files_to_move_for_this_term = []
                for filename in all_files:
                    if filename not in moved_files and term.lower() in filename.lower():
                        files_to_move_for_this_term.append(filename)

                if not files_to_move_for_this_term:
                    continue

                dest_dir = os.path.join(output_folder, term)
                if not is_dry_run:
                    os.makedirs(dest_dir, exist_ok=True)
                
                for filename in files_to_move_for_this_term:
                    source_path = os.path.join(source_folder, filename)
                    dest_path = os.path.join(dest_dir, filename)
                    if is_dry_run:
                        self.app.log(f"  - DRY RUN: Would move '{filename}' to folder '{term}'")
                        success_count += 1
                    else:
                        try:
                            shutil.move(source_path, dest_path)
                            self._log_action(log_path, source_path, dest_path, 'success', 'search_organize')
                            success_count += 1
                        except Exception as e:
                            self.app.log(f"  - FAILURE moving '{filename}': {e}")
                            self._log_action(log_path, source_path, dest_path, f'failure - {e}', 'search_organize')
                            failure_count += 1
                    moved_files.add(filename)

            self.app.log(f"\n--- Search & Organize Complete ---")
            Messagebox.show_info("Complete", f"Files moved successfully: {success_count}\nFailures: {failure_count}")
        except Exception as e:
            self.app.log(f"[CRITICAL ERROR] An unexpected error occurred: {e}")
            Messagebox.show_error(f"An unexpected error occurred: {e}", "Critical Error")

    def _get_search_terms(self):
        terms = []
        filepath = self.search_terms_file_var.get()
        if filepath and os.path.isfile(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    if filepath.lower().endswith('.csv'):
                        reader = csv.reader(f)
                        for row in reader:
                            if row: terms.append(row[0].strip())
                    else:
                        terms = [line.strip() for line in f if line.strip()]
            except Exception as e:
                self.app.log(f"Error reading search terms from file: {e}")
        else:
            text_content = self.search_terms_text.get("1.0", tk.END)
            terms = [line.strip() for line in text_content.splitlines() if line.strip()]
        return list(set(terms))

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
        if path: string_var.set(path)
    
    def _browse_search_terms_file(self):
        path = filedialog.askopenfilename(title="Select Search Terms File", filetypes=[("Text Files", "*.txt"), ("CSV Files", "*.csv"), ("All Files", "*.*")])
        if path: self.search_terms_file_var.set(path)