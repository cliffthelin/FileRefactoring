import os
import csv
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from core.interfaces import ActionPlugin

class ListFilesPlugin(ActionPlugin):
    """
    A plugin to generate a .txt or .csv report of files in a directory,
    with various formatting options.
    """
    def __init__(self, app_context):
        self.app = app_context
        
        # UI Variables
        self.source_folder_var = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=True)
        self.prepend_path_var = tk.BooleanVar(value=False)
        self.full_path_var = tk.BooleanVar(value=False)
        self.output_format_var = tk.StringVar(value="txt")

    def get_name(self) -> str:
        return "List Files"

    def get_value(self) -> str:
        return "list_files"
    
    def is_rollbackable(self) -> bool:
        return False

    def create_gui(self, master) -> None:
        frame = ttk.LabelFrame(master, text="List Files Options", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Source Folder:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.source_folder_var).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(frame, text="Browse...", command=self._browse_folder, bootstyle="outline").grid(row=0, column=2, padx=5)
        ttk.Checkbutton(frame, text="Include Subfolders (Recursive)", variable=self.recursive_var, bootstyle="round-toggle").grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(frame, text="Prepend Subfolder Path to Name", variable=self.prepend_path_var, bootstyle="round-toggle").grid(row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(frame, text="Include Full Absolute Path", variable=self.full_path_var, bootstyle="round-toggle").grid(row=3, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        format_frame = ttk.Frame(frame)
        format_frame.grid(row=4, column=0, columnspan=3, sticky="w", padx=5, pady=(10,5))
        ttk.Label(format_frame, text="Output Format:").pack(side="left")
        ttk.Radiobutton(format_frame, text="Plain Text (.txt)", variable=self.output_format_var, value="txt", bootstyle="toolbutton").pack(side="left", padx=5)
        ttk.Radiobutton(format_frame, text="CSV (.csv)", variable=self.output_format_var, value="csv", bootstyle="toolbutton").pack(side="left", padx=5)

    def validate(self) -> tuple[bool, str]:
        if not self.source_folder_var.get() or not os.path.isdir(self.source_folder_var.get()):
            return False, "A valid Source Folder is required."
        return True, ""

    def execute(self) -> None:
        source_folder = self.source_folder_var.get()
        is_recursive = self.recursive_var.get()
        prepend_path = self.prepend_path_var.get()
        full_path = self.full_path_var.get()
        output_format = self.output_format_var.get()
        self.app.log("--- Starting List Files Action ---")
        try:
            file_list = []
            if is_recursive:
                for root, _, files in os.walk(source_folder):
                    for filename in files:
                        file_list.append((os.path.join(root, filename), root))
            else:
                for filename in os.listdir(source_folder):
                    path = os.path.join(source_folder, filename)
                    if os.path.isfile(path):
                        file_list.append((path, source_folder))
            if not file_list:
                self.app.log("No files found to list.")
                Messagebox.show_info("No Files", "No files were found in the source directory.")
                return
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_filename = f"file_list_{timestamp}.{output_format}"
            output_path = os.path.join(source_folder, output_filename)
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if output_format == 'csv':
                    writer = csv.writer(f)
                    writer.writerow(['filename', 'subfolder', 'full_path', 'size_bytes', 'modified_date'])
                    for filepath, root in file_list:
                        stat = os.stat(filepath)
                        row = self._format_file_info(filepath, root, source_folder, prepend_path, full_path)
                        writer.writerow([row, os.path.relpath(root, source_folder), filepath, stat.st_size, datetime.fromtimestamp(stat.st_mtime).isoformat()])
                else:
                    for filepath, root in file_list:
                        f.write(self._format_file_info(filepath, root, source_folder, prepend_path, full_path) + '\n')
            self.app.log(f"Successfully generated file list: {output_filename}")
            Messagebox.show_info("List Generated", f"File list has been saved as:\n{output_filename}")
        except Exception as e:
            self.app.log(f"[CRITICAL ERROR] An unexpected error occurred: {e}")
            Messagebox.show_error(f"An unexpected error occurred: {e}", "Critical Error")
            
    def _format_file_info(self, filepath, root, source_folder, prepend, full):
        filename = os.path.basename(filepath)
        if full:
            return filepath
        if prepend:
            sub_path = os.path.relpath(root, source_folder)
            if sub_path != '.':
                return os.path.join(sub_path, filename)
        return filename

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Select Source Folder")
        if path:
            self.source_folder_var.set(path)