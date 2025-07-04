import unittest
import os
from unittest.mock import MagicMock, patch
from pyfakefs.fake_filesystem_unittest import TestCase

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from plugins.search_organize_plugin import SearchOrganizePlugin

@patch('ttkbootstrap.dialogs.Messagebox')
class TestSearchOrganizePlugin(TestCase):
    """Test suite for the SearchOrganizePlugin."""

    def setUp(self):
        """Set up the fake file system and test environment."""
        self.setUpPyfakefs()
        self.source_dir = "/source"
        self.output_dir = "/output"
        self.fs.create_dir(self.source_dir)
        self.fs.create_dir(self.output_dir)
        self.mock_app = MagicMock()
        self.mock_app.log = MagicMock()

    def test_case_insensitivity(self, mock_messagebox):
        """Ensure the file search is case-insensitive."""
        self.fs.create_file(os.path.join(self.source_dir, "Report-JAN.pdf"))
        
        plugin = SearchOrganizePlugin(self.mock_app)
        plugin.search_terms_text = MagicMock()
        
        plugin.source_folder_var.set(self.source_dir)
        plugin.output_folder_var.set(self.output_dir)
        plugin.dry_run_var.set(False)
        plugin.search_terms_text.get.return_value = "report-jan"
        
        plugin.execute()

        expected_dir = os.path.join(self.output_dir, "report-jan")
        expected_file = os.path.join(expected_dir, "Report-JAN.pdf")
        
        self.assertTrue(os.path.exists(expected_dir), "Directory 'report-jan' should have been created.")
        self.assertTrue(os.path.exists(expected_file), "The file was not moved to the correct directory.")

    def test_overlapping_search_terms(self, mock_messagebox):
        """
        Verify how the plugin handles a file that matches multiple search terms.
        """
        self.fs.create_file(os.path.join(self.source_dir, "Project-Alpha-Report.docx"))

        plugin = SearchOrganizePlugin(self.mock_app)
        plugin.search_terms_text = MagicMock()

        plugin.source_folder_var.set(self.source_dir)
        plugin.output_folder_var.set(self.output_dir)
        plugin.dry_run_var.set(False)
        
        plugin.search_terms_text.get.return_value = "Report\nProject"

        plugin.execute()

        expected_dir_report = os.path.join(self.output_dir, "Report")
        expected_file_report = os.path.join(expected_dir_report, "Project-Alpha-Report.docx")
        self.assertTrue(os.path.exists(expected_file_report))

        expected_dir_project = os.path.join(self.output_dir, "Project")
        self.assertFalse(os.path.exists(expected_dir_project), "Directory 'Project' should not be created as the file was already moved.")
