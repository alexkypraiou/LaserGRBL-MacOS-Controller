#!/usr/bin/env python3
"""
Simple script to run the LaserGRBL-MacOS-Controller application.

This script checks for dependencies and provides helpful error messages
if something is missing.
"""

import sys
import subprocess

def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    try:
        import PyQt6
        print("✓ PyQt6 is available")
    except ImportError:
        missing_deps.append("PyQt6")
        
    try:
        import PIL
        print("✓ PIL/Pillow is available")
    except ImportError:
        missing_deps.append("Pillow")
    
    return missing_deps

def install_dependencies():
    """Attempt to install missing dependencies."""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False
    except FileNotFoundError:
        print("✗ pip not found. Please install pip first.")
        return False

def main():
    """Main entry point."""
    print("LaserGRBL-MacOS-Controller Launcher")
    print("=" * 35)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        print(f"  Current version: {sys.version}")
        sys.exit(1)
    else:
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} is supported")
    
    # Check dependencies
    missing_deps = check_dependencies()
    
    if missing_deps:
        print(f"\n✗ Missing dependencies: {', '.join(missing_deps)}")
        print("\nWould you like to install them automatically? (y/n)")
        
        response = input().lower().strip()
        if response in ['y', 'yes']:
            if install_dependencies():
                missing_deps = check_dependencies()
            else:
                print("\nManual installation required:")
                print("pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("\nManual installation required:")
            print("pip install -r requirements.txt")
            sys.exit(1)
    
    if not missing_deps:
        print("\n✓ All dependencies are available")
        print("Starting LaserGRBL-MacOS-Controller...")
        
        try:
            from LaserGRBLMacOS import LaserControllerApp
            from PyQt6.QtWidgets import QApplication
            
            app = QApplication(sys.argv)
            controller = LaserControllerApp()
            controller.show()
            sys.exit(app.exec())
            
        except Exception as e:
            print(f"\n✗ Failed to start application: {e}")
            print("\nTroubleshooting:")
            print("1. Make sure you're on macOS or have X11 forwarding enabled")
            print("2. Check that all dependencies are properly installed")
            print("3. Try running: python3 LaserGRBLMacOS.py")
            sys.exit(1)

if __name__ == "__main__":
    main()