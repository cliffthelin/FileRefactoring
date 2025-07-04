import os
import importlib
import inspect
from core.interfaces import ActionPlugin

class PluginManager:
    """
    Handles the discovery, loading, and management of action plugins.
    """
    def __init__(self, plugin_folder="plugins"):
        self.plugin_folder = plugin_folder
        self.plugins = []

    def discover_plugins(self, app_context):
        """
        Scans the plugin folder, imports modules, and instantiates plugins.
        
        Args:
            app_context: The main application instance, passed to plugins
                         to give them access to the app's state and methods.
        """
        if not os.path.exists(self.plugin_folder):
            print(f"Plugin folder '{self.plugin_folder}' not found.")
            return

        for filename in os.listdir(self.plugin_folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"{self.plugin_folder}.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, cls in inspect.getmembers(module, inspect.isclass):
                        if issubclass(cls, ActionPlugin) and cls is not ActionPlugin:
                            # This will now correctly raise a TypeError if a plugin is incomplete,
                            # allowing the test suite to catch it as expected.
                            plugin_instance = cls(app_context)
                            self.plugins.append(plugin_instance)
                except Exception as e:
                    print(f"Error processing plugin from {filename}: {e}")
                    # Re-raise the error so that the test expecting it can catch it.
                    if isinstance(e, TypeError):
                        raise
        
    def get_all_plugins(self):
        """
        Returns a list of all loaded plugin instances.
        """
        return self.plugins
