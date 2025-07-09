# Laser GRBL Controller for macOS



This project provides a desktop application for macOS to control GRBL-compatible CNC machines and laser engravers. Built with Python and PyQt6, it offers a user-friendly interface for serial communication, G-code sending, jogging, and even converting images to G-code for engraving.

# Features


Serial Port Connection: Easily connect and disconnect from available serial ports.

GRBL Status Monitoring: Displays real-time GRBL status (Idle, Run, Hold, etc.) and current Work Position (WPos).

Jogging Controls: Intuitive buttons for moving the X, Y, and Z axes with configurable step sizes.

Set Origin: Quickly set the current machine position as the work coordinate origin (0,0,0).

Laser & Feed Rate Control: Sliders to adjust laser power (S) and feed rate (F) on the fly.

Image to G-code Conversion: Convert grayscale images (PNG, JPG, BMP, GIF) into G-code paths suitable for laser engraving, with customizable resolution and laser intensity threshold.

G-code Console: Send custom G-code commands and view GRBL's responses in a dedicated console.

G-code Path Preview: Visualizes the generated or loaded G-code paths, including laser travel (G00) and engraving (G01) moves, along with an optional image overlay.

Dark Theme: A modern, eye-pleasing dark user interface.

Optimized Layout: Responsive design with a scrollable control panel for efficient use on various screen sizes.
