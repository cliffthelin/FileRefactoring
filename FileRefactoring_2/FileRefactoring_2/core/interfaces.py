from abc import ABC, abstractmethod

class ActionPlugin(ABC):
    """
    Abstract Base Class for all action plugins.
    
    Each plugin must implement these methods to be successfully loaded
    and integrated into the main application.
    """
    @abstractmethod
    def __init__(self, app_context):
        """
        Initializes the plugin.
        
        Args:
            app_context: The main application instance (FileRefactoringGUI).
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Returns the display name of the action for the GUI.
        e.g., "Rename Files"
        """
        pass

    @abstractmethod
    def get_value(self) -> str:
        """
        Returns a unique, lowercase, and simple string value for the action.
        Used for internal mapping and for the radio button value.
        e.g., "rename"
        """
        pass

    @abstractmethod
    def is_rollbackable(self) -> bool:
        """
        Returns True if the action generates a log that can be rolled back.
        This will be used to display an indicator in the UI.
        """
        pass

    @abstractmethod
    def create_gui(self, master) -> None:
        """
        Creates the specific UI frame for the action's options.
        
        Args:
            master: The parent tk/ttk widget to build the UI upon.
        """
        pass

    @abstractmethod
    def execute(self) -> None:
        """
        Contains the core logic to perform the action.
        """
        pass
        
    @abstractmethod
    def validate(self) -> tuple[bool, str]:
        """
        Validates the user's input before execution.
        
        Returns:
            A tuple containing:
            - A boolean indicating if validation passed.
            - A message explaining the validation failure, or an empty string.
        """
        pass