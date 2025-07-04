import unittest
import os
from unittest.mock import MagicMock, patch
from pyfakefs.fake_filesystem_unittest import TestCase

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from plugins.find_duplicates_plugin import FindDuplicatesPlugin

@patch('ttkbootstrap.dialogs.Messagebox')
class TestFindDuplicatesPlugin(TestCase):
    """Test suite for the FindDuplicatesPlugin."""

    def setUp(self):
        """Set up the fake file system and test environment for each test."""
        self.setUpPyfakefs()
        self.source_dir = "/source"
        self.fs.create_dir(self.source_dir)
        
        self.mock_app = MagicMock()
        self.mock_app.log = MagicMock()
        
    @patch('plugins.find_duplicates_plugin.FindDuplicatesPlugin._show_results_window')
    def test_hash_vs_name_method(self, mock_show_results, mock_messagebox):
        """
        Verify that the two different duplicate detection methods correctly
        identify the intended duplicate sets.
        """
        self.fs.create_file("/source/report.pdf", contents="content_version_1")
        self.fs.create_dir("/source/sub")
        self.fs.create_file("/source/sub/report.pdf", contents="content_version_2")
        self.fs.create_file("/source/monthly.dat", contents="shared_content")
        self.fs.create_file("/source/backup.dat", contents="shared_content")
        
        plugin = FindDuplicatesPlugin(self.mock_app)
        plugin.source_folder_var.set(self.source_dir)
        plugin.recursive_var.set(True)

        # --- Test "Size & Name" Method ---
        plugin.method_var.set("size_name")
        plugin.execute()
        
        self.assertEqual(mock_show_results.call_count, 1)
        dupes_name = mock_show_results.call_args[0][0]
        self.assertEqual(len(dupes_name), 1)
        self.assertIn("/source/report.pdf", list(dupes_name.values())[0])

        # --- Test "Size & Content Hash" Method ---
        mock_show_results.reset_mock()
        plugin.method_var.set("size_hash")
        plugin.execute()
        
        self.assertEqual(mock_show_results.call_count, 1)
        dupes_hash = mock_show_results.call_args[0][0]
        self.assertEqual(len(dupes_hash), 1)
        self.assertIn("/source/monthly.dat", list(dupes_hash.values())[0])
