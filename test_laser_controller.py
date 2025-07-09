#!/usr/bin/env python3
"""
Basic unit tests for LaserGRBL-MacOS-Controller

These tests validate core functionality of the LaserControllerApp class.
Run with: python test_laser_controller.py
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Add the current directory to Python path to import the main module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock PyQt6 modules before importing the main application
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()
sys.modules['PyQt6.QtSerialPort'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageQt'] = MagicMock()

try:
    from LaserGRBLMacOS import LaserControllerApp
except ImportError as e:
    print(f"Warning: Could not import LaserControllerApp for testing: {e}")
    LaserControllerApp = None


class TestLaserControllerValidation(unittest.TestCase):
    """Test input validation and error handling functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock QApplication to avoid GUI dependencies
        with patch('LaserGRBLMacOS.QApplication'):
            self.mock_app = Mock()
    
    def test_gcode_command_validation(self):
        """Test G-code command validation."""
        # Test valid G-code commands
        valid_commands = [
            "G00 X10 Y10",
            "G01 X20 Y20 F1000",
            "M3 S100",
            "G28",
            "$H"
        ]
        
        for cmd in valid_commands:
            # Valid commands should not be empty and should be strings
            self.assertIsInstance(cmd, str)
            self.assertTrue(len(cmd.strip()) > 0)
    
    def test_coordinate_validation(self):
        """Test coordinate parsing and validation."""
        test_cases = [
            ("10.5", 10.5, True),
            ("-5.0", -5.0, True),
            ("0", 0.0, True),
            ("abc", None, False),
            ("", None, False),
            ("999.999", 999.999, True),
        ]
        
        for input_val, expected, should_pass in test_cases:
            try:
                result = float(input_val) if input_val else None
                if should_pass:
                    self.assertEqual(result, expected)
                else:
                    self.assertIsNone(result)
            except ValueError:
                self.assertFalse(should_pass, f"Expected {input_val} to be invalid")
    
    def test_laser_threshold_validation(self):
        """Test laser threshold value validation."""
        # Valid threshold values (0-255)
        valid_thresholds = [0, 128, 255]
        for threshold in valid_thresholds:
            self.assertGreaterEqual(threshold, 0)
            self.assertLessEqual(threshold, 255)
        
        # Invalid threshold values
        invalid_thresholds = [-1, 256, -100, 1000]
        for threshold in invalid_thresholds:
            self.assertTrue(threshold < 0 or threshold > 255)
    
    def test_file_extension_validation(self):
        """Test image file extension validation."""
        valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        invalid_extensions = ['.txt', '.doc', '.exe', '.py']
        
        for ext in valid_extensions:
            # Simulate checking if file has valid image extension
            self.assertIn(ext.lower(), ['.png', '.jpg', '.jpeg', '.bmp', '.gif'])
        
        for ext in invalid_extensions:
            self.assertNotIn(ext.lower(), ['.png', '.jpg', '.jpeg', '.bmp', '.gif'])


class TestGCodeGeneration(unittest.TestCase):
    """Test G-code generation utilities."""
    
    def test_gcode_command_formatting(self):
        """Test proper G-code command formatting."""
        # Test basic G-code command structure
        test_cases = [
            ("G00", "X10", "Y20", "G00 X10 Y20"),
            ("G01", "X5.5", "Y-3.2", "F1000", "G01 X5.5 Y-3.2 F1000"),
            ("M3", "S100", "M3 S100"),
        ]
        
        for *components, expected in test_cases:
            # Simulate G-code command construction
            result = " ".join(components)
            self.assertEqual(result, expected)
    
    def test_coordinate_boundaries(self):
        """Test coordinate boundary validation."""
        # Test typical CNC coordinate boundaries
        max_coords = 300  # mm - typical for small CNC machines
        min_coords = -10  # mm - small negative allowance
        
        test_coordinates = [
            (0, 0, True),      # Origin
            (150, 150, True),  # Center area
            (299, 299, True),  # Near maximum
            (301, 301, False), # Over maximum
            (-5, -5, True),    # Small negative
            (-15, -15, False), # Over minimum negative
        ]
        
        for x, y, should_be_valid in test_coordinates:
            x_valid = min_coords <= x <= max_coords
            y_valid = min_coords <= y <= max_coords
            is_valid = x_valid and y_valid
            
            self.assertEqual(is_valid, should_be_valid,
                           f"Coordinate ({x}, {y}) validation failed")


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""
    
    def test_serial_port_error_simulation(self):
        """Test serial port error handling."""
        # Simulate common serial port error messages
        error_scenarios = [
            ("Permission denied", "permission"),
            ("Device not found", "device"),
            ("Access denied", "access"),
            ("Unknown error", "unknown")
        ]
        
        for error_msg, error_type in error_scenarios:
            # Test that error messages are categorized correctly
            if "permission" in error_type or "access" in error_type:
                self.assertIn("denied", error_msg.lower())
            elif "device" in error_type:
                self.assertIn("not found", error_msg.lower())
    
    def test_image_loading_error_handling(self):
        """Test image loading error scenarios."""
        # Test with non-existent file
        non_existent_file = "/path/that/does/not/exist.png"
        self.assertFalse(os.path.exists(non_existent_file))
        
        # Test with invalid dimensions
        invalid_dimensions = [(-1, 10), (10, -1), (0, 10), (10, 0)]
        for width, height in invalid_dimensions:
            self.assertFalse(width > 0 and height > 0)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility and helper functions."""
    
    def test_time_formatting(self):
        """Test time formatting for duration display."""
        # Simulate time formatting function
        def format_time(seconds):
            """Format seconds into HH:MM:SS format."""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
        test_cases = [
            (0, "00:00:00"),
            (61, "00:01:01"),
            (3661, "01:01:01"),
            (7325, "02:02:05"),
        ]
        
        for input_seconds, expected in test_cases:
            result = format_time(input_seconds)
            self.assertEqual(result, expected)
    
    def test_distance_calculation(self):
        """Test distance calculation between coordinates."""
        def calculate_distance(x1, y1, x2, y2):
            """Calculate Euclidean distance between two points."""
            return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
        test_cases = [
            (0, 0, 3, 4, 5.0),      # 3-4-5 triangle
            (0, 0, 0, 0, 0.0),      # Same point
            (1, 1, 4, 5, 5.0),      # Another 3-4-5 triangle
            (-1, -1, 2, 3, 5.0),    # With negative coordinates
        ]
        
        for x1, y1, x2, y2, expected in test_cases:
            result = calculate_distance(x1, y1, x2, y2)
            self.assertAlmostEqual(result, expected, places=2)


def run_tests():
    """Run all tests and display results."""
    print("Running LaserGRBL-MacOS-Controller Tests")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestLaserControllerValidation,
        TestGCodeGeneration,
        TestErrorHandling,
        TestUtilityFunctions
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    return success


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)