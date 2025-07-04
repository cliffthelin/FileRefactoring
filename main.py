import sys
import tkinter as tk
import ttkbootstrap as ttk
from tkinterdnd2 import TkinterDnD

from core.app import FileRefactoringGUI

def main():
    """
    The main entry point for the application.
    Initializes the main window and the FileRefactoringGUI.
    Handles command-line arguments for automated testing.
    """
    # Use TkinterDnD.Tk for drag-and-drop support
    root = TkinterDnD.Tk()
    # It's better to set the style on the root Tk object if possible
    style = ttk.Style(theme="superhero")
    
    # Initialize the main application GUI
    app = FileRefactoringGUI(root)
    
    # Check for the --test startup flag
    if "--test" in sys.argv:
        # Schedule the test to run after the main window is fully initialized.
        # This prevents the test from blocking the UI from appearing.
        print("'--test' flag detected. Opening Test Center on startup.")
        root.after(250, app.open_test_center)
    
    # Start the Tkinter main loop
    root.mainloop()

if __name__ == '__main__':
    main()