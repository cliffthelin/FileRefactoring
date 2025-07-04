import unittest
import os
import csv
from unittest.mock import MagicMock, patch
from pyfakefs.fake_filesystem_unittest import TestCase

# Add project root to path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from plugins.rename_prefix_plugin import RenamePrefixPlugin

@patch('ttkbootstrap.dialogs.Messagebox')
class TestRenamePrefixPlugin(TestCase):
    """Test suite for the RenamePrefixPlugin."""

    def setUp(self):
        """Set up the fake file system and test environment for each test."""
        self.setUpPyfakefs()
        self.source_dir = "/source"
        self.fs.create_dir(self.source_dir)
        
        # Create a mock application context
        self.mock_app = MagicMock()
        self.mock_app.log = MagicMock()

        # Create test files
        self.fs.create_file(os.path.join(self.source_dir, "report2024.pdf"))
        self.fs.create_file(os.path.join(self.source_dir, "report2023.txt"))
        self.fs.create_file(os.path.join(self.source_dir, "data_final_v2.csv"))
        
        # Create prefix map CSV
        self.csv_path = os.path.join(self.source_dir, "prefix_map.csv")
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['report', 'monthly'])
            writer.writerow(['data_final', 'annual'])

    def test_prefix_renaming_logic(self, mock_messagebox):
        """Test the core logic of finding and prepending prefixes."""
        plugin = RenamePrefixPlugin(self.mock_app)
        plugin.target_directory_var.set(self.source_dir)
        plugin.csv_path_var.set(self.csv_path)
        plugin.dry_run_var.set(False)

        plugin.execute()

        # Assertions
        # Check that files were correctly renamed
        self.assertTrue(os.path.exists(os.path.join(self.source_dir, "monthly_report2024.pdf")))
        self.assertTrue(os.path.exists(os.path.join(self.source_dir, "monthly_report2023.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.source_dir, "annual_data_final_v2.csv")))

        # Check that original files are gone
        self.assertFalse(os.path.exists(os.path.join(self.source_dir, "report2024.pdf")))
        self.assertFalse(os.path.exists(os.path.join(self.source_dir, "data_final_v2.csv")))
        
        # Check logs
        self.mock_app.log.assert_any_call("SUCCESS: Renamed 'report2024.pdf' to 'monthly_report2024.pdf'")

    def test_dry_run_functionality(self, mock_messagebox):
        """Ensure dry run simulates changes without renaming files."""
        plugin = RenamePrefixPlugin(self.mock_app)
        plugin.target_directory_var.set(self.source_dir)
        plugin.csv_path_var.set(self.csv_path)
        plugin.dry_run_var.set(True)

        plugin.execute()

        # Assert original files still exist
        self.assertTrue(os.path.exists(os.path.join(self.source_dir, "report2024.pdf")))
        self.assertTrue(os.path.exists(os.path.join(self.source_dir, "data_final_v2.csv")))

        # Assert new files were NOT created
        self.assertFalse(os.path.exists(os.path.join(self.source_dir, "monthly_report2024.pdf")))

        # Assert the log indicates a dry run
        self.mock_app.log.assert_any_call("DRY RUN: Would rename 'report2024.pdf' to 'monthly_report2024.pdf'")

    def test_validation(self, mock_messagebox):
        """Test the validation logic for required inputs."""
        plugin = RenamePrefixPlugin(self.mock_app)
        
        # Invalid directory
        plugin.target_directory_var.set("/nonexistent")
        plugin.csv_path_var.set(self.csv_path)
        is_valid, msg = plugin.validate()
        self.assertFalse(is_valid)
        self.assertIn("Target Directory is required", msg)
        
        # Invalid CSV
        plugin.target_directory_var.set(self.source_dir)
        plugin.csv_path_var.set("nonexistent.csv")
        is_valid, msg = plugin.validate()
        self.assertFalse(is_valid)
        self.assertIn("CSV File is required", msg)

        # Valid inputs
        plugin.target_directory_var.set(self.source_dir)
        plugin.csv_path_var.set(self.csv_path)
        is_valid, msg = plugin.validate()
        self.assertTrue(is_valid)