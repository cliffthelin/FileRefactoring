import unittest
import os
import re
from unittest.mock import MagicMock, patch
from pyfakefs.fake_filesystem_unittest import TestCase

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from plugins.replace_plugin import ReplacePlugin

@patch('ttkbootstrap.dialogs.Messagebox')
class TestReplacePlugin(TestCase):
    """Test suite for the ReplacePlugin."""

    def setUp(self):
        """Set up the fake file system and test environment."""
        self.setUpPyfakefs()
        self.source_dir = "/source"
        self.fs.create_dir(self.source_dir)
        
        self.mock_app = MagicMock()
        self.mock_app.log = MagicMock()

    def test_regex_functionality(self, mock_messagebox):
        """Verify the regular expression replacement logic."""
        self.fs.create_file(os.path.join(self.source_dir, "file-001.txt"))
        self.fs.create_file(os.path.join(self.source_dir, "file-002.txt"))
        
        plugin = ReplacePlugin(self.mock_app)
        plugin.source_folder_var.set(self.source_dir)
        plugin.find_var.set(r"file-(\d{3})")
        plugin.replace_with_var.set(r"document-\1")
        plugin.use_regex_var.set(True)
        plugin.target_var.set("name")
        plugin.dry_run_var.set(False)
        
        plugin.execute()

        self.assertFalse(os.path.exists(os.path.join(self.source_dir, "file-001.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.source_dir, "document-001.txt")))

    def test_replace_in_extension(self, mock_messagebox):
        """Test the 'Extension only' target option."""
        self.fs.create_file(os.path.join(self.source_dir, "photo.jpeg"))
        
        plugin = ReplacePlugin(self.mock_app)
        plugin.source_folder_var.set(self.source_dir)
        plugin.find_var.set("jpeg")
        plugin.replace_with_var.set("jpg")
        plugin.use_regex_var.set(False)
        plugin.target_var.set("ext")
        plugin.dry_run_var.set(False)
        
        plugin.execute()

        self.assertTrue(os.path.exists(os.path.join(self.source_dir, "photo.jpg")))
        
    def test_invalid_regex_validation(self, mock_messagebox):
        """Verify that the validation catches an invalid regex pattern."""
        plugin = ReplacePlugin(self.mock_app)
        plugin.source_folder_var.set(self.source_dir)
        plugin.find_var.set("(")
        plugin.use_regex_var.set(True)
        
        is_valid, msg = plugin.validate()
        
        self.assertFalse(is_valid)
        self.assertIn("Invalid Regex pattern", msg)