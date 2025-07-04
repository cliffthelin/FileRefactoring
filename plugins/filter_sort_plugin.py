import os
import csv
import fnmatch
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets import DateEntry

from core.interfaces import ActionPlugin

class FilterSortPlugin(ActionPlugin):
    """
    A plugin to find and list files based on multiple criteria (name, size, date)
    and sort the results into a CSV report.
    """
    def __init__(self, app_context):
        self.app = app_context
        
        # UI Variables
        self.source_folder_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=True)
        self.filter_name_var = tk.StringVar(value="*.*")
        self.filter_size_op_var = tk.StringVar(value=">")
        self.filter_size_var = tk.IntVar(value=0)
        self.filter_date_op_var = tk.StringVar(value="after")
        self.sort_by_var = tk.StringVar(value="name")
        self.sort_order_var = tk.StringVar(value="asc")

    def get_name(self) -> str:
        return "Filter & Sort"

    def get_value(self) -> str:
        return "filter_sort"
    
    def is_rollbackable(self) -> bool:
        return False

    def create_gui(self, master) -> None:
        frame = ttk.LabelFrame(master, text="Filter & Sort Options", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Source Folder:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.source_folder_var).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=self._browse_folder, bootstyle="outline").grid(row=0, column=2, padx=5)
        ttk.Checkbutton(frame, text="Include Subfolders", variable=self.recursive_var, bootstyle="round-toggle").grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        filter_group = ttk.LabelFrame(frame, text="Filter Criteria", padding=10)
        filter_group.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        filter_group.columnconfigure(1, weight=1)
        ttk.Label(filter_group, text="Name (e.g., *.txt):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(filter_group, textvariable=self.filter_name_var).grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=2)
        ttk.Label(filter_group, text="Size is:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        size_op_combo = ttk.Combobox(filter_group, textvariable=self.filter_size_op_var, values=[">", "<", "=="], width=3, state="readonly")
        size_op_combo.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Entry(filter_group, textvariable=self.filter_size_var, width=10).grid(row=1, column=2, sticky="w", padx=5, pady=2)
        ttk.Label(filter_group, text="KB").grid(row=1, column=3, sticky="w", padx=5, pady=2)
        ttk.Label(filter_group, text="Modified date is:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        date_op_combo = ttk.Combobox(filter_group, textvariable=self.filter_date_op_var, values=["after", "before"], width=8, state="readonly")
        date_op_combo.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.filter_date_entry = DateEntry(filter_group, bootstyle="primary")
        self.filter_date_entry.grid(row=2, column=2, sticky="w", columnspan=2, padx=5, pady=2)
        sort_group = ttk.LabelFrame(frame, text="Sort Results", padding=10)
        sort_group.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        sort_group.columnconfigure(1, weight=1)
        ttk.Label(sort_group, text="Sort by:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        sort_by_combo = ttk.Combobox(sort_group, textvariable=self.sort_by_var, values=["name", "size", "date"], width=10, state="readonly")
        sort_by_combo.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(sort_group, text="Order:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        sort_order_combo = ttk.Combobox(sort_group, textvariable=self.sort_order_var, values=["asc", "desc"], width=10, state="readonly")
        sort_order_combo.grid(row=0, column=3, sticky="w", padx=5, pady=2)

    def validate(self) -> tuple[bool, str]:
        if not self.source_folder_var.get() or not os.path.isdir(self.source_folder_var.get()): return False, "A valid Source Folder is required."
        try: self.filter_size_var.get()
        except tk.TclError: return False, "File size must be a valid number."
        return True, ""

    def execute(self) -> None:
        self.app.log("--- Starting Filter & Sort Action ---")
        try:
            files_to_process = self._collect_files()
            filtered_files = self._apply_filters(files_to_process)
            sorted_files = self._sort_files(filtered_files)
            if not sorted_files:
                self.app.log("No files matched the specified criteria.")
                Messagebox.show_info("No Results", "No files were found matching your filter criteria.")
                return
            self._write_report(sorted_files)
        except Exception as e:
            self.app.log(f"[CRITICAL ERROR] An unexpected error occurred: {e}")

    def _collect_files(self):
        source_folder = self.source_folder_var.get()
        is_recursive = self.recursive_var.get()
        file_list = []
        iterator = os.walk(source_folder) if is_recursive else [(source_folder, [], os.listdir(source_folder))]
        for root, _, files in iterator:
            for name in files:
                path = os.path.join(root, name)
                if os.path.isfile(path):
                    try:
                        stat = os.stat(path)
                        file_list.append({'path': path, 'name': name, 'size': stat.st_size, 'mtime': stat.st_mtime})
                    except OSError: continue
        return file_list
        
    def _apply_filters(self, files):
        name_pattern = self.filter_name_var.get()
        size_op = self.filter_size_op_var.get()
        size_bytes = self.filter_size_var.get() * 1024
        date_op = self.filter_date_op_var.get()
        filter_date = self.filter_date_entry.entry.get_date()
        filter_timestamp = datetime.combine(filter_date, datetime.min.time()).timestamp()
        results = []
        for file_info in files:
            if not fnmatch.fnmatch(file_info['name'], name_pattern): continue
            if size_bytes > 0:
                if size_op == '>' and not file_info['size'] > size_bytes: continue
                if size_op == '<' and not file_info['size'] < size_bytes: continue
                if size_op == '==' and not file_info['size'] == size_bytes: continue
            if date_op == 'after' and not file_info['mtime'] > filter_timestamp: continue
            if date_op == 'before' and not file_info['mtime'] < filter_timestamp: continue
            results.append(file_info)
        return results

    def _sort_files(self, files):
        sort_key = self.sort_by_var.get()
        sort_order = self.sort_order_var.get()
        if sort_key == 'name': key_func = lambda x: x['name']
        elif sort_key == 'size': key_func = lambda x: x['size']
        else: key_func = lambda x: x['mtime']
        return sorted(files, key=key_func, reverse=(sort_order == 'desc'))

    def _write_report(self, files):
        source_folder = self.source_folder_var.get()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_filename = f"filtered_results_{timestamp}.csv"
        output_path = os.path.join(source_folder, output_filename)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'full_path', 'size_kb', 'modified_date'])
            for file_info in files:
                writer.writerow([file_info['name'], file_info['path'], f"{file_info['size'] / 1024:.2f}", datetime.fromtimestamp(file_info['mtime']).strftime('%Y-%m-%d %H:%M:%S')])
        self.app.log(f"Successfully generated filter/sort report: {output_filename}")
        Messagebox.show_info("Report Generated", f"Filtered results have been saved as:\n{output_filename}")

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Select Source Folder")
        if path: self.source_folder_var.set(path)