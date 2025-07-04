import unittest
import os
import sys
import json
import io
from datetime import datetime

LOG_DIR = ".test_logs"

def get_test_suite():
    """Discovers all tests and returns them as a suite."""
    # Ensure the project root is on the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    test_dir = os.path.join(project_root, 'tests')
    
    loader = unittest.TestLoader()
    # ** THE FIX **: Explicitly setting top_level_dir to the project root is crucial
    # for resolving module imports correctly (e.g., 'from core.interfaces...').
    suite = loader.discover(start_dir=test_dir, pattern='test_*.py', top_level_dir=project_root)
    return suite

def list_all_tests(suite):
    """Recursively finds all test names within a test suite."""
    test_names = []
    if hasattr(suite, '__iter__'):
        for test in suite:
            test_names.extend(list_all_tests(test))
    else:
        test_names.append(str(suite.id()))
    return sorted(test_names)

def run_suite_and_get_output():
    """Runs the test suite and captures the raw text output."""
    suite = get_test_suite()
    if suite.countTestCases() == 0:
        return "No tests found to run.", True

    buffer = io.StringIO()
    runner = unittest.TextTestRunner(stream=buffer, verbosity=2)
    result = runner.run(suite)
    
    output = buffer.getvalue()
    buffer.close()
    
    return output, result.wasSuccessful()

def save_log_file(content):
    """Saves the given content to a new timestamped log file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"run_{timestamp}.log"
    log_path = os.path.join(LOG_DIR, log_filename)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Test results saved to {log_path}")


if __name__ == '__main__':
    """Discovers and runs all tests, intended for command-line execution."""
    print("Discovering and running all tests...")
    output, was_successful = run_suite_and_get_output()
    
    print("\n--- TEST RESULTS ---")
    print(output)
    
    save_log_file(output)
    
    if not was_successful:
        print("\nSome tests failed.")
        sys.exit(1)
    else:
        print("\nAll tests passed successfully.")
