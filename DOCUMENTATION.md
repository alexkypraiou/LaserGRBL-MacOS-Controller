# LaserGRBL-MacOS-Controller Documentation

## Overview

LaserGRBL-MacOS-Controller is a desktop application for macOS designed to control GRBL-compatible CNC machines and laser engravers. This document provides detailed information about the application's features and usage.

## System Requirements

- macOS 10.14 or later
- Python 3.8 or higher
- PyQt6
- Pillow (PIL)
- USB port for serial communication

## Hardware Setup

### GRBL Configuration

Before using this application, ensure your Arduino or compatible controller is flashed with GRBL firmware:

1. **Download GRBL firmware** from [https://github.com/grbl/grbl](https://github.com/grbl/grbl)
2. **Flash the firmware** to your Arduino using Arduino IDE
3. **Configure GRBL settings** using commands like `$$` to view current settings

### Connection

1. Connect your CNC/laser controller to your Mac via USB
2. Note the device path (usually `/dev/cu.usbmodem*` or `/dev/cu.usbserial*`)
3. Launch the application and select the correct serial port

## Application Features

### Serial Communication

- **Auto-detection** of available serial ports
- **Real-time connection status** with GRBL detection
- **Automatic reconnection** handling
- **Command history** and response logging

### Control Interface

#### Jogging Controls
- **X/Y/Z axis movement** with configurable step sizes
- **Home command** (`$H`) for machine homing
- **Feed rate control** via slider
- **Set origin** functionality (`G92` command)

#### Laser Control
- **Laser power adjustment** (S0-S1000)
- **Real-time power control** via slider
- **Laser on/off** commands (`M3`/`M5`)

### G-code Operations

#### Manual G-code
- **Custom command input** via console
- **Real-time command execution**
- **Progress tracking** with line highlighting
- **Error handling** and reporting

#### File Operations
- **G-code file loading** from disk
- **Batch command execution**
- **Progress bar** with time estimation
- **Pause/resume functionality**

### Image to G-code Conversion

#### Supported Formats
- PNG, JPG, BMP, GIF
- Automatic grayscale conversion
- Customizable output dimensions

#### Conversion Settings
- **Resolution**: 1-50 pixels per millimeter
- **Laser threshold**: 0-255 intensity level
- **Zig-zag scanning** for efficiency
- **Preview generation**

#### Process
1. Load image file
2. Set target dimensions (width/height in mm)
3. Adjust resolution and threshold
4. Convert to G-code
5. Preview generated path
6. Send to machine

### Visual Preview

#### Path Visualization
- **G-code path preview** with different colors for travel/cut moves
- **Real-time position tracking**
- **Image overlay** support
- **Zoom and pan** functionality
- **Grid reference** lines

#### Status Display
- **Machine status** (Idle, Run, Hold, Alarm, etc.)
- **Current position** (WPos coordinates)
- **Feed rate and spindle speed**
- **Progress indicators**

## Usage Guide

### Getting Started

1. **Launch the application**
   ```bash
   python3 LaserGRBLMacOS.py
   ```

2. **Connect to your device**
   - Select serial port from dropdown
   - Click "Connect"
   - Wait for GRBL detection confirmation

3. **Test basic functionality**
   - Use jog controls to move axes
   - Check position feedback
   - Test laser on/off (carefully!)

### Image Engraving Workflow

1. **Prepare your image**
   - Use high contrast images for best results
   - Ensure image is properly sized
   - Save in supported format

2. **Load and configure**
   - Click "Browse" to select image
   - Set target dimensions in millimeters
   - Adjust resolution (higher = more detail, longer job)
   - Set laser threshold (lower = more laser activation)

3. **Generate G-code**
   - Click "Convert to G-code"
   - Review the generated path in preview
   - Check estimated job time

4. **Execute the job**
   - Position your material
   - Set work origin with "Set Origin"
   - Click "Send G-code"
   - Monitor progress and machine status

### Safety Considerations

- **Always wear safety glasses** when operating laser equipment
- **Ensure proper ventilation** for laser cutting/engraving
- **Keep fire extinguisher nearby** when using laser
- **Test on scrap material** before final pieces
- **Monitor the machine** throughout operation
- **Use emergency stop** if needed (disconnect power)

## Troubleshooting

### Connection Issues

**Problem**: Can't find serial port
- **Solution**: Check USB cable and driver installation
- **macOS**: May need to install CH340/CP2102 drivers

**Problem**: GRBL not detected
- **Solution**: Verify GRBL firmware is properly flashed
- **Check**: Baud rate (usually 115200 for GRBL)

### G-code Issues

**Problem**: Commands not executing
- **Solution**: Check GRBL status (must be Idle for most commands)
- **Check**: Machine limits and soft limits configuration

**Problem**: Unexpected movement
- **Solution**: Verify work coordinate system (G54)
- **Check**: Machine coordinates vs. work coordinates

### Image Conversion Issues

**Problem**: Poor quality output
- **Solution**: Adjust laser threshold and resolution
- **Try**: Higher contrast source images

**Problem**: Job takes too long
- **Solution**: Lower resolution or reduce image size
- **Optimize**: Remove unnecessary detail from source image

## Advanced Configuration

### GRBL Settings

Common GRBL parameters to configure:
- `$100`, `$101`, `$102`: Steps per mm for X, Y, Z
- `$110`, `$111`, `$112`: Max rates for X, Y, Z
- `$120`, `$121`, `$122`: Acceleration for X, Y, Z
- `$130`, `$131`, `$132`: Max travel for X, Y, Z

### Application Customization

The application supports various customizations:
- **Dark theme** is enabled by default
- **Window size** adapts to screen resolution
- **Serial timeout** settings in source code
- **Default feed rates** and laser power limits

## Technical Details

### Communication Protocol
- **Baud rate**: 115200 (GRBL default)
- **Data bits**: 8
- **Parity**: None
- **Stop bits**: 1
- **Flow control**: None

### G-code Commands Used
- `G21`: Millimeter units
- `G90`: Absolute positioning
- `G91`: Relative positioning (for jogging)
- `G92`: Set work coordinates
- `$J`: Jogging command
- `M3`/`M5`: Spindle/laser on/off
- `?`: Status query

## Support and Contributing

For support, bug reports, or feature requests:
- **GitHub Issues**: [Repository Issues](https://github.com/alexkypraiou/LaserGRBL-MacOS-Controller/issues)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **License**: MIT License (see [LICENSE](LICENSE))

## References

- [GRBL GitHub Repository](https://github.com/grbl/grbl)
- [GRBL Configuration Guide](https://github.com/grbl/grbl/wiki/Grbl-Configuration)
- [G-code Reference](https://linuxcnc.org/docs/html/gcode.html)