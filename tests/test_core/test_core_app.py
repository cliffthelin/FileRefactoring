import unittest
import os
import tkinter as tk
from unittest.mock import MagicMock, patch
from pyfakefs.fake_filesystem_unittest import TestCase

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.app import FileRefactoringGUI
from core.plugin_manager import PluginManager

@patch('ttkbootstrap.dialogs.Messagebox')
class TestCoreApp(TestCase):
    """Test suite for the core application functionality."""
    def setUp(self):
        """Set up the fake file system for plugin discovery tests."""
        self.setUpPyfakefs()
        self.plugins_dir = "plugins"
        self.fs.create_dir(self.plugins_dir)

    def test_plugin_loading(self, mock_messagebox):
        """Verify the PluginManager correctly discovers and handles various plugin file scenarios."""
        self.fs.create_file(
            f"{self.plugins_dir}/incomplete_plugin.py",
            contents="from core.interfaces import ActionPlugin\\nclass IP(ActionPlugin): pass")
        
        mock_app = MagicMock()
        manager = PluginManager(plugin_folder=self.plugins_dir)
        
        with self.assertRaises(TypeError):
            manager.discover_plugins(mock_app)

    @patch('core.app.TestCenterWindow')
    def test_ui_action_switching(self, mock_test_center, mock_messagebox):
        """Integration test to ensure the GUI correctly switches between plugin frames."""
        mock_root = MagicMock()
        mock_root.winfo_exists.return_value = True
        
        mock_frame1 = MagicMock()
        mock_frame2 = MagicMock()
        
        app = FileRefactoringGUI(mock_root)
        app.plugins = {
            'Plugin 1': MagicMock(),
            'Plugin 2': MagicMock()
        }
        app.plugin_frames = {
            'Plugin 1': mock_frame1,
            'Plugin 2': mock_frame2
        }
        
        app.action_var.set('Plugin 1')
        app._on_action_change(None)
        
        mock_frame1.pack.assert_called_once()
        mock_frame2.pack_forget.assert_called_once()
        
        mock_frame1.reset_mock()
        mock_frame2.reset_mock()
        
        app.action_var.set('Plugin 2')
        app._on_action_change(None)
        
        mock_frame2.pack.assert_called_once()
        mock_frame1.pack_forget.assert_called_once()
