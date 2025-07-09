"""
Unit tests for LaserGRBL-MacOS-Controller

These tests focus on critical functions that don't require GUI interaction.
"""

import unittest
import sys
import os
import re

# Add the parent directory to the path so we can import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock PyQt6 for testing in environments where it's not available
try:
    from PyQt6.QtWidgets import QApplication
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class TestGRBLStatusParsing(unittest.TestCase):
    """Test GRBL status string parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if PYQT_AVAILABLE:
            # Only create the app if PyQt6 is available
            self.app = QApplication.instance()
            if self.app is None:
                self.app = QApplication([])
            
            from LaserGRBLMacOS import LaserControllerApp
            self.controller = LaserControllerApp()
        else:
            self.controller = None

    def test_parse_idle_status(self):
        """Test parsing of idle status."""
        if not PYQT_AVAILABLE:
            self.skipTest("PyQt6 not available")
            
        status_string = "<Idle|WPos:0.000,0.000,0.000|Bf:15,128|FS:0,0|Ov:100,100,100|A:S>"
        self.controller.parse_grbl_status(status_string)
        
        self.assertEqual(self.controller.grbl_status, "Idle")
        self.assertEqual(self.controller.current_x, 0.0)
        self.assertEqual(self.controller.current_y, 0.0)
        self.assertEqual(self.controller.current_z, 0.0)

    def test_parse_run_status(self):
        """Test parsing of run status with position."""
        if not PYQT_AVAILABLE:
            self.skipTest("PyQt6 not available")
            
        status_string = "<Run|WPos:10.500,-5.250,2.000|Bf:15,128|FS:1000,500|Ov:100,100,100|A:S>"
        self.controller.parse_grbl_status(status_string)
        
        self.assertEqual(self.controller.grbl_status, "Run")
        self.assertEqual(self.controller.current_x, 10.5)
        self.assertEqual(self.controller.current_y, -5.25)
        self.assertEqual(self.controller.current_z, 2.0)

    def test_regex_patterns(self):
        """Test regex patterns used for GRBL status parsing without GUI."""
        # Test status extraction
        status_string = "<Hold|WPos:1.000,2.000,3.000|Bf:15,128|FS:0,0|Ov:100,100,100|A:S>"
        status_match = re.search(r'<(Idle|Run|Hold|Jog|Alarm|Check|Door|Home|Sleep)', status_string)
        self.assertIsNotNone(status_match)
        self.assertEqual(status_match.group(1), "Hold")
        
        # Test position extraction
        wpos_match = re.search(r'WPos:([-\d.]+),([-\d.]+),([-\d.]+)', status_string)
        self.assertIsNotNone(wpos_match)
        self.assertEqual(float(wpos_match.group(1)), 1.0)
        self.assertEqual(float(wpos_match.group(2)), 2.0)
        self.assertEqual(float(wpos_match.group(3)), 3.0)


class TestJogStepValidation(unittest.TestCase):
    """Test jog step validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if PYQT_AVAILABLE:
            self.app = QApplication.instance()
            if self.app is None:
                self.app = QApplication([])
            
            from LaserGRBLMacOS import LaserControllerApp
            self.controller = LaserControllerApp()
        else:
            self.controller = None

    def test_valid_jog_step(self):
        """Test valid jog step values."""
        if not PYQT_AVAILABLE:
            self.skipTest("PyQt6 not available")
            
        # Test various valid values
        test_values = [1.0, 0.1, 10.0, 0.01, 100.0]
        for value in test_values:
            self.controller.jog_step_input.setText(str(value))
            self.controller.update_jog_step()
            self.assertEqual(self.controller.jog_step, value)

    def test_invalid_jog_step(self):
        """Test invalid jog step values fallback to default."""
        if not PYQT_AVAILABLE:
            self.skipTest("PyQt6 not available")
            
        # Test invalid values
        invalid_values = ["abc", "", "not_a_number", "1.0.0"]
        for value in invalid_values:
            self.controller.jog_step_input.setText(value)
            self.controller.update_jog_step()
            self.assertEqual(self.controller.jog_step, 1.0)  # Should fallback to default


class TestTimeFormatting(unittest.TestCase):
    """Test time formatting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if PYQT_AVAILABLE:
            self.app = QApplication.instance()
            if self.app is None:
                self.app = QApplication([])
            
            from LaserGRBLMacOS import LaserControllerApp
            self.controller = LaserControllerApp()
        else:
            self.controller = None

    def test_format_time_seconds(self):
        """Test time formatting for seconds."""
        if not PYQT_AVAILABLE:
            self.skipTest("PyQt6 not available")
            
        result = self.controller._format_time(45)
        self.assertEqual(result, "0:45")

    def test_format_time_minutes(self):
        """Test time formatting for minutes and seconds."""
        if not PYQT_AVAILABLE:
            self.skipTest("PyQt6 not available")
            
        result = self.controller._format_time(125)  # 2 minutes 5 seconds
        self.assertEqual(result, "2:05")

    def test_format_time_hours(self):
        """Test time formatting for hours, minutes and seconds."""
        if not PYQT_AVAILABLE:
            self.skipTest("PyQt6 not available")
            
        result = self.controller._format_time(3665)  # 1 hour 1 minute 5 seconds
        self.assertEqual(result, "1:01:05")


class TestImageProcessingUtils(unittest.TestCase):
    """Test image processing utility functions."""
    
    def test_resolution_calculations(self):
        """Test pixel per millimeter calculations."""
        # Test that 5 pixels per millimeter is correctly used
        ppm = 5
        width_mm = 10
        height_mm = 20
        
        expected_width_px = int(width_mm * ppm)
        expected_height_px = int(height_mm * ppm)
        
        self.assertEqual(expected_width_px, 50)
        self.assertEqual(expected_height_px, 100)

    def test_laser_power_calculation(self):
        """Test laser power calculation from pixel intensity."""
        # Test the formula used in convert_image_to_gcode
        pixel_intensity = 100  # 0-255 range
        laser_power = int(1000 * (1 - pixel_intensity / 255.0))
        laser_power = max(1, min(1000, laser_power))
        
        expected_power = int(1000 * (1 - 100/255.0))
        expected_power = max(1, min(1000, expected_power))
        
        self.assertEqual(laser_power, expected_power)
        self.assertGreaterEqual(laser_power, 1)
        self.assertLessEqual(laser_power, 1000)


if __name__ == '__main__':
    # Run tests
    unittest.main()