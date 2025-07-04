import unittest
import os
from unittest.mock import MagicMock, patch
from pyfakefs.fake_filesystem_unittest import TestCase

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from plugins.organize_plugin import OrganizePlugin

@patch('ttkbootstrap.dialogs.Messagebox')
class TestOrganizePlugin(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.source_dir = "/source"
        self.output_dir = "/output"
        self.fs.create_dir(self.source_dir)
        self.fs.create_dir(self.output_dir)
        self.mock_app = MagicMock()
        self.mock_app.log = MagicMock()

    def test_organization_with_no_delimiter(self, mock_messagebox):
        self.fs.create_file(os.path.join(self.source_dir, "r-j-s.pdf"))
        self.fs.create_file(os.path.join(self.source_dir, "summary.txt"))
        plugin = OrganizePlugin(self.mock_app)
        plugin.source_folder_var.set(self.source_dir)
        plugin.output_folder_var.set(self.output_dir)
        plugin.delimiter_var.set("-")
        plugin.execute()
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "r", "j", "s.pdf")))
        self.assertTrue(os.path.exists(os.path.join(self.source_dir, "summary.txt")))
        self.mock_app.log.assert_any_call("SKIPPING 'summary.txt': No delimiter found.")

    def test_recursive_vs_non_recursive(self, mock_messagebox):
        sub_dir = os.path.join(self.source_dir, "sub")
        self.fs.create_dir(sub_dir)
        self.fs.create_file(os.path.join(self.source_dir, "root-f.txt"))
        self.fs.create_file(os.path.join(sub_dir, "sub-f.txt"))
        plugin = OrganizePlugin(self.mock_app)
        plugin.source_folder_var.set(self.source_dir)
        plugin.output_folder_var.set(self.output_dir)
        plugin.delimiter_var.set("-")
        plugin.recursive_var.set(False)
        plugin.execute()
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "root", "f.txt")))
        self.assertTrue(os.path.exists(os.path.join(sub_dir, "sub-f.txt")))
        self.fs.create_file(os.path.join(self.source_dir, "root-f.txt"))
        plugin.recursive_var.set(True)
        plugin.execute()
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "sub", "f.txt")))