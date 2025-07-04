import unittest
import os
import csv
from unittest.mock import MagicMock, patch
from pyfakefs.fake_filesystem_unittest import TestCase

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from plugins.rename_plugin import RenamePlugin

@patch('ttkbootstrap.dialogs.Messagebox')
class TestRenamePlugin(TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.test_dir = "/test_data"
        self.fs.create_dir(self.test_dir)
        self.mock_app = MagicMock()
        self.mock_app.log = MagicMock()

    def test_validation_logic(self, mock_messagebox):
        plugin = RenamePlugin(self.mock_app)
        plugin.source_folder_var.set("/non_existent_dir")
        self.assertFalse(plugin.validate()[0])
        plugin.source_folder_var.set(self.test_dir)
        plugin.csv_path_var.set("/non_existent.csv")
        self.assertFalse(plugin.validate()[0])
        csv_path = os.path.join(self.test_dir, "d.csv")
        self.fs.create_file(csv_path)
        plugin.csv_path_var.set(csv_path)
        self.assertTrue(plugin.validate()[0])

    def test_csv_with_bad_data(self, mock_messagebox):
        self.fs.create_file(os.path.join(self.test_dir, "good.txt"))
        csv_path = os.path.join(self.test_dir, "bad.csv")
        with open(csv_path, 'w', newline='') as f:
            w=csv.writer(f); w.writerow(['original_filename','new_filename']); w.writerow(['','n']); w.writerow(['good.txt','r.txt']); w.writerow(['a.txt',''])
        plugin = RenamePlugin(self.mock_app)
        plugin.source_folder_var.set(self.test_dir)
        plugin.csv_path_var.set(csv_path)
        plugin.execute()
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "r.txt")))
        self.mock_app.log.assert_any_call("SKIPPING row 2: Missing original or new filename.")
        self.mock_app.log.assert_any_call("SKIPPING row 4: Missing original or new filename.")