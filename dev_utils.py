#!/usr/bin/env python3
"""
Development utility script for LaserGRBL-MacOS-Controller

This script provides common development tasks:
- Run tests
- Check dependencies
- Validate code structure
"""

import sys
import os
import subprocess
import importlib.util


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("Checking dependencies...")
    
    required_packages = {
        'PyQt6': 'PyQt6',
        'serial': 'PySerial', 
        'PIL': 'Pillow'
    }
    
    missing_packages = []
    
    for module, package_name in required_packages.items():
        try:
            importlib.import_module(module)
            print(f"✓ {package_name} is installed")
        except ImportError:
            print(f"✗ {package_name} is missing")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    else:
        print("✓ All dependencies are installed")
        return True


def run_tests():
    """Run the test suite."""
    print("Running test suite...")
    try:
        result = subprocess.run([sys.executable, 'test_laser_controller.py'], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def validate_structure():
    """Validate project structure and files."""
    print("Validating project structure...")
    
    required_files = [
        'LaserGRBLMacOS.py',
        'requirements.txt',
        'README.md',
        'LICENSE',
        'CONTRIBUTING.md',
        'test_laser_controller.py'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\nMissing files: {', '.join(missing_files)}")
        return False
    else:
        print("✓ All required files present")
        return True


def show_help():
    """Show available commands."""
    print("LaserGRBL-MacOS-Controller Development Utility")
    print("=" * 50)
    print("Available commands:")
    print("  deps     - Check dependencies")
    print("  test     - Run test suite")
    print("  validate - Validate project structure")
    print("  all      - Run all checks")
    print("  help     - Show this help")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'deps':
        success = check_dependencies()
    elif command == 'test':
        success = run_tests()
    elif command == 'validate':
        success = validate_structure()
    elif command == 'all':
        print("Running all checks...\n")
        success = (validate_structure() and 
                  check_dependencies() and 
                  run_tests())
        print("\n" + "=" * 50)
        print(f"Overall result: {'PASS' if success else 'FAIL'}")
    elif command == 'help':
        show_help()
        return
    else:
        print(f"Unknown command: {command}")
        show_help()
        return
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()