import unittest
import os
import csv
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from pyfakefs.fake_filesystem_unittest import TestCase

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from plugins.filter_sort_plugin import FilterSortPlugin

@patch('ttkbootstrap.dialogs.Messagebox')
class TestFilterSortPlugin(TestCase):
    """Test suite for the FilterSortPlugin."""

    def setUp(self):
        """Set up the fake file system and test environment for each test."""
        self.setUpPyfakefs()
        self.source_dir = "/source"
        self.fs.create_dir(self.source_dir)
        
        self.mock_app = MagicMock()
        self.mock_app.log = MagicMock()
        
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        file_a_path = os.path.join(self.source_dir, "report_alpha.txt")
        self.fs.create_file(file_a_path, contents="a" * 1024)
        os.utime(file_a_path, (two_days_ago.timestamp(), two_days_ago.timestamp()))

        file_b_path = os.path.join(self.source_dir, "log_beta.txt")
        self.fs.create_file(file_b_path, contents="b" * 5 * 1024)
        os.utime(file_b_path, (now.timestamp(), now.timestamp()))

        file_c_path = os.path.join(self.source_dir, "config_gamma.log")
        self.fs.create_file(file_c_path, contents="c" * 2 * 1024)
        os.utime(file_c_path, (yesterday.timestamp(), yesterday.timestamp()))

    def _get_latest_report_content(self):
        """Helper function to find and read the most recently created report."""
        report_files = [f for f in os.listdir(self.source_dir) if f.startswith("filtered_results_")]
        self.assertGreater(len(report_files), 0, "Report file was not created.")
        
        latest_report = max(report_files, key=lambda f: os.path.getmtime(os.path.join(self.source_dir, f)))
        report_path = os.path.join(self.source_dir, latest_report)
        
        with open(report_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
        os.remove(report_path)
        return rows

    def test_all_filter_combinations(self, mock_messagebox):
        """Verify that combining name, size, and date filters works correctly."""
        plugin = FilterSortPlugin(self.mock_app)
        plugin.filter_date_entry = MagicMock()
        
        plugin.source_folder_var.set(self.source_dir)
        plugin.filter_name_var.set("*.txt")
        plugin.filter_size_op_var.set(">")
        plugin.filter_size_var.set(4)
        plugin.filter_date_op_var.set("after")
        plugin.filter_date_entry.entry.get_date.return_value = (datetime.now() - timedelta(days=1)).date()
        plugin.execute()

        report_rows = self._get_latest_report_content()
        self.assertEqual(len(report_rows), 1)
        self.assertEqual(report_rows[0][0], "log_beta.txt")

    def test_sorting_order(self, mock_messagebox):
        """Test both 'asc' and 'desc' sorting for all sortable fields."""
        
        def run_sort_test(sort_by, sort_order):
            plugin = FilterSortPlugin(self.mock_app)
            plugin.source_folder_var.set(self.source_dir)
            plugin.filter_date_entry = MagicMock()
            plugin.filter_date_entry.entry.get_date.return_value = (datetime.now() - timedelta(days=3)).date()
            plugin.filter_date_op_var.set("after")
            plugin.filter_name_var.set("*.*")
            plugin.sort_by_var.set(sort_by)
            plugin.sort_order_var.set(sort_order)
            plugin.execute()
            return self._get_latest_report_content()

        # Test name ascending
        rows = run_sort_test("name", "asc")
        self.assertEqual([row[0] for row in rows], ["config_gamma.log", "log_beta.txt", "report_alpha.txt"])

        # Test size descending
        rows = run_sort_test("size", "desc")
        self.assertEqual([row[0] for row in rows], ["log_beta.txt", "config_gamma.log", "report_alpha.txt"])
        
        # Test date ascending
        rows = run_sort_test("date", "asc")
        self.assertEqual([row[0] for row in rows], ["report_alpha.txt", "config_gamma.log", "log_beta.txt"])
