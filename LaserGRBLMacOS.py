import sys
import re
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QTextEdit, QFileDialog, QLineEdit, QSlider, QFrame,
    QSizePolicy, QGridLayout, QCheckBox, QGraphicsView, QGraphicsScene,
    QGraphicsLineItem, QGraphicsRectItem, QGraphicsTextItem, QGroupBox, QScrollArea,
    QProgressBar
)
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt6.QtCore import QIODevice, QTimer, Qt, QByteArray, QRectF
from PyQt6.QtGui import (
    QPixmap, QColor, QPen, QTransform, QPainterPath, QDoubleValidator, QPainter, QFont,
    QTextCharFormat, QTextCursor
)
from PIL import Image, ImageQt # type: ignore

class LaserControllerApp(QWidget):
    """
    Main application class for the Laser GRBL Controller.
    
    This class provides a PyQt6-based GUI application for controlling GRBL-compatible
    CNC machines and laser engravers. It supports serial communication, G-code sending,
    jogging controls, image-to-G-code conversion, and real-time status monitoring.
    
    Attributes:
        serial_port (QSerialPort): Serial port connection to the GRBL device
        image_path (str): Path to the currently selected image file
        current_x, current_y, current_z (float): Current machine coordinates
        grbl_status (str): Current GRBL status string
        jog_step (float): Step size for jogging movements in mm
        preview_image_resolution_ppm (int): Pixels per millimeter for image conversion
        laser_threshold (int): Pixel intensity threshold (0-255) for laser activation
        gcode_to_send_queue (list): Queue of G-code commands to send sequentially
    """
    
    def __init__(self):
        """
        Initialize the LaserControllerApp.
        
        Sets up the main window, initializes all instance variables, creates timers
        for GRBL communication, and builds the user interface.
        """
        super().__init__()
        self.serial_port = QSerialPort()
        self.image_path = None
        
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_z = 0.0
        self.grbl_status = "Disconnected"
        
        self.jog_step = 1.0 
        self.preview_image_resolution_ppm = 5 # Pixels per Millimeter for image conversion
        self.laser_threshold = 200 # Pixel intensity threshold for laser ON (0-255)
        
        self.grbl_detect_timer = QTimer(self)
        self.grbl_detect_timer.setSingleShot(True)
        self.grbl_detect_timer.timeout.connect(self._check_grbl_response)
        self.grbl_response_buffer = ""

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.request_grbl_status)
        
        # List to hold G-code commands for sequential sending
        self.gcode_to_send_queue = []
        self.total_gcode_lines = 0
        self.gcode_lines_sent = 0
        self.gcode_current_line_index = -1 # Index for highlighting
        self.gcode_start_time = 0 # To track execution time
        
        self.gcode_send_timer = QTimer(self)
        self.gcode_send_timer.setSingleShot(True) # Send one command at a time
        self.gcode_send_timer.timeout.connect(self._send_next_gcode_command)

        self.initUI()
        self.apply_styles() # Apply custom styles
        self.populate_serial_ports()

    def initUI(self):
        """
        Initialize and set up the user interface.
        
        Creates the main window layout with left control panel (serial connection,
        GRBL status, jogging controls, laser settings, image conversion) and right
        panel (G-code preview). Uses a scrollable design for smaller screens.
        """
        self.setWindowTitle('Laser GRBL Controller - Precision')
        self.setMinimumSize(1000, 700)
        self.setGeometry(100, 100, 1400, 900)

        # Main window layout: horizontal split between controls (left) and preview (right)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # --- Left Panel (Controls) - Wrapped in QScrollArea for small screens ---
        # Scrollable area ensures usability on smaller displays
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        left_panel_container = QWidget(self)
        left_panel_layout = QVBoxLayout(left_panel_container)
        left_panel_layout.setSpacing(12)
        left_panel_layout.setContentsMargins(0, 0, 0, 0)

        # --- Serial Port Connection Group ---
        port_connection_group = QGroupBox('Serial Port Connection', self)
        port_connection_layout = QVBoxLayout(port_connection_group)
        port_connection_layout.setSpacing(8)
        port_connection_layout.setContentsMargins(10, 20, 10, 10)

        port_selection_layout = QHBoxLayout()
        port_selection_layout.addWidget(QLabel('Port:'))
        self.port_combo = QComboBox(self)
        self.port_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        port_selection_layout.addWidget(self.port_combo)
        self.refresh_ports_button = QPushButton('Refresh Ports', self)
        self.refresh_ports_button.clicked.connect(self.populate_serial_ports)
        port_selection_layout.addWidget(self.refresh_ports_button)
        port_connection_layout.addLayout(port_selection_layout)

        self.connect_button = QPushButton('Connect', self)
        self.connect_button.clicked.connect(self.toggle_connection)
        port_connection_layout.addWidget(self.connect_button)
        
        self.status_label = QLabel('Status: Disconnected', self)
        self.status_label.setObjectName("statusLabel")
        port_connection_layout.addWidget(self.status_label)
        
        self.pos_label = QLabel('Position (WPos): X: 0.00 Y: 0.00 Z: 0.00', self)
        self.pos_label.setObjectName("posLabel")
        port_connection_layout.addWidget(self.pos_label)
        left_panel_layout.addWidget(port_connection_group)

        # --- Jogging Controls Group ---
        jog_group = QGroupBox('Jogging Controls', self)
        jog_layout = QVBoxLayout(jog_group)
        jog_layout.setSpacing(8)
        jog_layout.setContentsMargins(10, 20, 10, 10)

        jog_step_layout = QHBoxLayout()
        jog_step_layout.addWidget(QLabel('Step (mm):'))
        self.jog_step_input = QLineEdit(str(self.jog_step), self)
        self.jog_step_input.setValidator(QDoubleValidator(0.01, 999.0, 3))
        self.jog_step_input.editingFinished.connect(self.update_jog_step)
        jog_step_layout.addWidget(self.jog_step_input)
        jog_layout.addLayout(jog_step_layout)

        jog_buttons_grid = QGridLayout()
        jog_buttons_grid.setSpacing(5)

        self.jog_btn_z_plus = QPushButton('Z+', self)
        self.jog_btn_z_plus.clicked.connect(lambda: self.send_jog_command_z(self.jog_step))
        jog_buttons_grid.addWidget(self.jog_btn_z_plus, 0, 3)

        self.jog_btn_y_plus = QPushButton('Y+', self)
        self.jog_btn_y_plus.clicked.connect(lambda: self.send_jog_command(0, self.jog_step))
        jog_buttons_grid.addWidget(self.jog_btn_y_plus, 1, 1)

        self.jog_btn_x_minus = QPushButton('X-', self)
        self.jog_btn_x_minus.clicked.connect(lambda: self.send_jog_command(-self.jog_step, 0))
        jog_buttons_grid.addWidget(self.jog_btn_x_minus, 2, 0)
        
        self.jog_btn_home = QPushButton('Home ($H)', self)
        self.jog_btn_home.clicked.connect(lambda: self.send_command('$H'))
        jog_buttons_grid.addWidget(self.jog_btn_home, 2, 1)
        
        self.jog_btn_x_plus = QPushButton('X+', self)
        self.jog_btn_x_plus.clicked.connect(lambda: self.send_jog_command(self.jog_step, 0))
        jog_buttons_grid.addWidget(self.jog_btn_x_plus, 2, 2)

        self.jog_btn_y_minus = QPushButton('Y-', self)
        self.jog_btn_y_minus.clicked.connect(lambda: self.send_jog_command(0, -self.jog_step))
        jog_buttons_grid.addWidget(self.jog_btn_y_minus, 3, 1)
        
        self.jog_btn_z_minus = QPushButton('Z-', self)
        self.jog_btn_z_minus.clicked.connect(lambda: self.send_jog_command_z(-self.jog_step))
        jog_buttons_grid.addWidget(self.jog_btn_z_minus, 4, 3)

        jog_layout.addLayout(jog_buttons_grid)
        
        control_buttons_layout = QHBoxLayout()
        control_buttons_layout.setSpacing(5)

        self.jog_btn_set_origin = QPushButton('Set Origin', self)
        self.jog_btn_set_origin.clicked.connect(self.set_origin)
        control_buttons_layout.addWidget(self.jog_btn_set_origin)

        self.jog_btn_unlock = QPushButton('Unlock ($X)', self)
        self.jog_btn_unlock.clicked.connect(lambda: self.send_command('$X'))
        control_buttons_layout.addWidget(self.jog_btn_unlock)
        
        self.jog_btn_soft_reset = QPushButton('Soft Reset', self)
        self.jog_btn_soft_reset.clicked.connect(lambda: self.send_command('\x18'))
        control_buttons_layout.addWidget(self.jog_btn_soft_reset)
        jog_layout.addLayout(control_buttons_layout)
        
        left_panel_layout.addWidget(jog_group)
        
        # --- Quick Commands/Macros Group ---
        quick_commands_group = QGroupBox('Quick Commands (Macros)', self)
        quick_commands_layout = QGridLayout(quick_commands_group)
        quick_commands_layout.setSpacing(8)
        quick_commands_layout.setContentsMargins(10, 20, 10, 10)

        self.btn_home_macro = QPushButton('Home ($H)', self)
        self.btn_home_macro.clicked.connect(lambda: self.send_command('$H'))
        quick_commands_layout.addWidget(self.btn_home_macro, 0, 0)

        self.btn_goto_zero = QPushButton('Go to Zero (G0 X0Y0Z0)', self)
        self.btn_goto_zero.clicked.connect(lambda: self.send_command('G0 X0 Y0 Z0'))
        quick_commands_layout.addWidget(self.btn_goto_zero, 0, 1)

        self.btn_soft_reset_macro = QPushButton('Soft Reset (Ctrl-X)', self)
        self.btn_soft_reset_macro.clicked.connect(lambda: self.send_command('\x18'))
        quick_commands_layout.addWidget(self.btn_soft_reset_macro, 1, 0)
        
        self.btn_unlock_macro = QPushButton('Unlock ($X)', self)
        self.btn_unlock_macro.clicked.connect(lambda: self.send_command('$X'))
        quick_commands_layout.addWidget(self.btn_unlock_macro, 1, 1)

        self.btn_grbl_settings = QPushButton('GRBL Settings ($$)', self)
        self.btn_grbl_settings.clicked.connect(lambda: self.send_command('$$'))
        quick_commands_layout.addWidget(self.btn_grbl_settings, 2, 0)

        self.btn_grbl_parser_state = QPushButton('Parser State ($G)', self)
        self.btn_grbl_parser_state.clicked.connect(lambda: self.send_command('$G'))
        quick_commands_layout.addWidget(self.btn_grbl_parser_state, 2, 1)

        self.btn_laser_test_on = QPushButton('Laser Test ON (S10)', self)
        self.btn_laser_test_on.clicked.connect(lambda: self.send_command('M3 S10'))
        quick_commands_layout.addWidget(self.btn_laser_test_on, 3, 0)

        self.btn_laser_test_off = QPushButton('Laser Test OFF (M5)', self)
        self.btn_laser_test_off.clicked.connect(lambda: self.send_command('M5 S0'))
        quick_commands_layout.addWidget(self.btn_laser_test_off, 3, 1)

        left_panel_layout.addWidget(quick_commands_group)


        # --- Laser/Feed Rate Sliders Group ---
        sliders_group = QGroupBox('Laser & Movement Settings', self)
        sliders_layout = QVBoxLayout(sliders_group)
        sliders_layout.setSpacing(8)
        sliders_layout.setContentsMargins(10, 20, 10, 10)

        laser_power_layout = QHBoxLayout()
        laser_power_layout.addWidget(QLabel('Laser Power (S):'))
        self.laser_power_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.laser_power_slider.setRange(0, 1000)
        self.laser_power_slider.setValue(0)
        self.laser_power_slider.setTickInterval(100)
        self.laser_power_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.laser_power_slider.valueChanged.connect(self.update_laser_power_label)
        self.laser_power_slider.sliderReleased.connect(self.send_laser_power_command)
        laser_power_layout.addWidget(self.laser_power_slider)
        self.laser_power_label = QLabel('S: 0', self)
        self.laser_power_label.setFixedWidth(50)
        laser_power_layout.addWidget(self.laser_power_label)
        sliders_layout.addLayout(laser_power_layout)

        feed_rate_layout = QHBoxLayout()
        feed_rate_layout.addWidget(QLabel('Feed Rate (F):'))
        self.feed_rate_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.feed_rate_slider.setRange(100, 5000)
        self.feed_rate_slider.setValue(1000)
        self.feed_rate_slider.setTickInterval(500)
        self.feed_rate_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.feed_rate_slider.valueChanged.connect(self.update_feed_rate_label)
        self.feed_rate_slider.sliderReleased.connect(self.send_feed_rate_command)
        feed_rate_layout.addWidget(self.feed_rate_slider)
        self.feed_rate_label = QLabel('F: 1000', self)
        self.feed_rate_label.setFixedWidth(60)
        feed_rate_layout.addWidget(self.feed_rate_label)
        sliders_layout.addLayout(feed_rate_layout)
        left_panel_layout.addWidget(sliders_group)

        # --- Image Conversion Group ---
        image_convert_group = QGroupBox('Image to G-code Conversion', self)
        image_convert_layout = QVBoxLayout(image_convert_group)
        image_convert_layout.setSpacing(8)
        image_convert_layout.setContentsMargins(10, 20, 10, 10)
        
        image_selection_layout = QHBoxLayout()
        self.select_image_button = QPushButton('Select Image', self)
        self.select_image_button.clicked.connect(self.select_image)
        image_selection_layout.addWidget(self.select_image_button)
        self.image_path_label = QLabel('No image selected.', self)
        self.image_path_label.setWordWrap(True)
        image_selection_layout.addWidget(self.image_path_label)
        image_convert_layout.addLayout(image_selection_layout)

        settings_layout = QGridLayout()
        settings_layout.setSpacing(5)

        settings_layout.addWidget(QLabel("Width (mm):"), 0, 0)
        self.width_input = QLineEdit("50", self)
        self.width_input.setValidator(QDoubleValidator(0.1, 999.0, 3))
        settings_layout.addWidget(self.width_input, 0, 1)

        settings_layout.addWidget(QLabel("Height (mm):"), 1, 0)
        self.height_input = QLineEdit("50", self)
        self.height_input.setValidator(QDoubleValidator(0.1, 999.0, 3))
        settings_layout.addWidget(self.height_input, 1, 1)

        settings_layout.addWidget(QLabel('Laser Threshold (0-255):'), 0, 2)
        self.laser_threshold_input = QLineEdit(str(self.laser_threshold), self)
        self.laser_threshold_input.setValidator(QDoubleValidator(0.0, 255.0, 0))
        self.laser_threshold_input.editingFinished.connect(self.update_laser_threshold)
        settings_layout.addWidget(self.laser_threshold_input, 0, 3)
        
        settings_layout.addWidget(QLabel('Resolution (PPM):'), 1, 2)
        self.preview_resolution_input = QLineEdit(str(self.preview_image_resolution_ppm), self)
        self.preview_resolution_input.setValidator(QDoubleValidator(1.0, 50.0, 0))
        self.preview_resolution_input.editingFinished.connect(self.update_preview_resolution)
        settings_layout.addWidget(self.preview_resolution_input, 1, 3)
        
        image_convert_layout.addLayout(settings_layout)

        self.convert_to_gcode_button = QPushButton('Convert & Preview', self)
        self.convert_to_gcode_button.clicked.connect(self.convert_image_to_gcode)
        self.convert_to_gcode_button.setEnabled(False)
        image_convert_layout.addWidget(self.convert_to_gcode_button)
        left_panel_layout.addWidget(image_convert_group)

        # --- G-code Console & GRBL Output Group ---
        gcode_console_group = QGroupBox('G-code Console & GRBL Output', self)
        gcode_console_layout = QVBoxLayout(gcode_console_group)
        gcode_console_layout.setSpacing(8)
        gcode_console_layout.setContentsMargins(10, 20, 10, 10)
        
        gcode_console_layout.addWidget(QLabel('G-code to Send:'))
        self.gcode_input = QTextEdit(self)
        self.gcode_input.setPlaceholderText("Type or paste G-code commands here / G-code from image will appear here.")
        self.gcode_input.setMinimumHeight(100)
        gcode_console_layout.addWidget(self.gcode_input)
        
        # Progress and Estimated Time
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.estimated_time_label = QLabel("Estimated Time: --:--:--", self)
        self.estimated_time_label.setFixedWidth(200)
        progress_layout.addWidget(self.estimated_time_label)
        
        gcode_console_layout.addLayout(progress_layout)

        self.send_gcode_button = QPushButton('Send G-code', self)
        self.send_gcode_button.clicked.connect(self.send_gcode)
        self.send_gcode_button.setEnabled(False)
        gcode_console_layout.addWidget(self.send_gcode_button)
        
        self.grbl_output_text = QTextEdit(self)
        self.grbl_output_text.setReadOnly(True)
        self.grbl_output_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.grbl_output_text.setObjectName("grblOutputText")
        self.grbl_output_text.setMinimumHeight(100)
        gcode_console_layout.addWidget(QLabel('GRBL Output (Console):'))
        gcode_console_layout.addWidget(self.grbl_output_text)
        
        left_panel_layout.addWidget(gcode_console_group)
        left_panel_layout.addStretch(1)

        scroll_area.setWidget(left_panel_container)
        main_layout.addWidget(scroll_area, 1)

        # --- Right Panel (G-code Preview) ---
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_group = QGroupBox('Laser Path Preview', self)
        preview_layout = QVBoxLayout(self.preview_group)
        preview_layout.setContentsMargins(10, 20, 10, 10)
        
        self.graphics_scene = QGraphicsScene(self)
        self.graphics_scene.setSceneRect(0, 0, 150, 150)
        
        self.graphics_view = QGraphicsView(self.graphics_scene, self)
        self.graphics_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.graphics_view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.graphics_view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.graphics_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.graphics_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.graphics_view.wheelEvent = self.graphics_view_wheelEvent
        self.graphics_view.setMinimumSize(400, 400)

        preview_layout.addWidget(self.graphics_view)
        right_panel_layout.addWidget(self.preview_group)

        main_layout.addLayout(right_panel_layout, 2)
        self.setLayout(main_layout)

        self.update_ui_state(False)
        self.preview_gcode([]) # Draw initial empty grid

    def apply_styles(self):
        """Applies a dark, professional QSS theme to the application."""
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e; /* Dark background */
                color: #e0e0e0; /* Light grey text */
                font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px; /* Slightly smaller base font */
            }

            QGroupBox {
                background-color: #3b3b3b; /* Slightly lighter group background */
                border: 1px solid #505050;
                border-radius: 6px; /* Slightly more rounded corners */
                margin-top: 1.5ex; /* Space for title */
                font-weight: bold;
                color: #f0f0f0; /* Group title color */
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #a0a0a0; /* Subtler title color */
                font-size: 14px;
                font-weight: bold;
            }

            QLabel {
                color: #d0d0d0;
            }
            QLabel#statusLabel { /* Specific style for status label */
                font-weight: bold;
                color: #cccccc; /* Default neutral color */
            }
            QLabel#posLabel { /* Specific style for position label */
                font-family: 'Consolas', 'Courier New', monospace; /* Monospaced for coordinates */
                font-size: 13px;
                color: #90ee90; /* Light green for position */
            }

            QPushButton {
                background-color: #555555;
                color: #ffffff;
                border: 1px solid #777777;
                border-radius: 4px;
                padding: 7px 14px; /* Slightly more padding */
                min-height: 30px; /* Consistent height */
                font-size: 13px;
                outline: none; /* Remove focus outline */
            }
            QPushButton:hover {
                background-color: #666666;
                border-color: #999999;
            }
            QPushButton:pressed {
                background-color: #444444;
                border-color: #aaaaaa;
            }
            QPushButton:disabled {
                background-color: #383838;
                color: #777777;
                border-color: #555555;
            }

            QComboBox {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px; /* More padding */
                selection-background-color: #007acc; /* Highlight for selected item */
                min-height: 30px; /* Consistent height */
            }
            QComboBox::drop-down {
                border: 0px; /* No border for the arrow button */
                width: 20px; /* Make dropdown arrow area larger */
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgdmlld0JveD0iMCAwIDE2IDE2Ij48cGF0aCBmaWxsPSIjRTBFMEUwIiBkPSJNNi42IDExLjZMMyAxMmwxLTIuNmEzIDMgMCAwIDAgMCAuNiAxIDEgMCAwIDAgLjguMiA2IDYgMCAwIDEtNiAxMC42IDYgNiAwIDAgMS02IDZhMSAxIDAgMCAwLS44LS4xIDMgMyAwIDAgMC0uMS0uNyAzIDMgMCAwIDAgLjctLjEgMSAxIDAgMCAwLS41LS43djExLjZ6IiB0cmFuc2Zvcm09InJvdGF0ZSgxODBIDEg4IDgpIiAvPjwvc3ZnPg==); /* Simple white down arrow */
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView { /* Styling for dropdown list items */
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                selection-background-color: #007acc;
            }

            QLineEdit {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px; /* More padding */
                min-height: 30px; /* Consistent height */
            }
            QLineEdit:focus {
                border: 1px solid #0099ff; /* Brighter highlight on focus */
                background-color: #424242; /* Slightly brighter when focused */
            }

            QTextEdit {
                background-color: #222222; /* Even darker for console/code */
                color: #f0f0f0; /* Default text color for general input */
                border: 1px solid #444;
                border-radius: 3px;
                padding: 8px; /* More padding */
                font-family: 'Consolas', 'Fira Code', 'Roboto Mono', monospace; /* Monospaced font for code */
                font-size: 13px;
            }
            QTextEdit::placeholder {
                color: #888888;
            }
            QTextEdit#grblOutputText { /* Specific style for GRBL output */
                color: #00e6e6; /* Cyan for GRBL responses */
            }

            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 6px; /* thinner groove */
                background: #4a4a4a;
                margin: 2px 0;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #0099ff; /* Professional blue accent color */
                border: 1px solid #006bb3;
                width: 16px; /* smaller handle */
                margin: -5px 0; 
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #00b3ff;
            }
            QSlider::add-page:horizontal {
                background: #555;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #007acc; /* Slightly darker blue for filled part */
                border-radius: 3px;
            }
            QSlider::tick-mark {
                background: #777;
                width: 1px;
                height: 6px; /* vertical tick marks */
                margin-top: 0px; /* center vertical axis */
            }

            QGraphicsView {
                background-color: #1c1c1c; /* Very dark background for the drawing area */
                border: 1px solid #444;
                border-radius: 5px;
            }
            
            QScrollArea {
                border: none; /* No border for the scroll area itself */
            }
            QScrollArea > QWidget > QWidget { /* Targeting the inner widget of scroll area */
                background-color: #2e2e2e; /* Match main background */
            }
            
            /* Scrollbar styling for a cleaner look */
            QScrollBar:vertical {
                border: 1px solid #3a3a3a;
                background: #2a2a2a;
                width: 12px;
                margin: 0px 0px 0px 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #505050;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #606060;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QProgressBar {
                border: 1px solid #505050;
                border-radius: 5px;
                text-align: center;
                color: #e0e0e0;
                background-color: #4a4a4a;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 4px;
            }

        """)
        
    def update_ui_state(self, connected):
        """
        Updates the enabled/disabled state of UI elements based on connection status.
        
        This method manages the UI state to ensure that only appropriate controls
        are available based on the current connection status and selected image.
        
        Args:
            connected (bool): True if connected to GRBL device, False otherwise
        """
        is_image_selected = (self.image_path is not None)

        self.send_gcode_button.setEnabled(connected)
        
        jogging_allowed = connected and (self.grbl_status in ["Idle", "Jog"]) 
        self.jog_btn_x_minus.setEnabled(jogging_allowed)
        self.jog_btn_x_plus.setEnabled(jogging_allowed)
        self.jog_btn_y_minus.setEnabled(jogging_allowed)
        self.jog_btn_y_plus.setEnabled(jogging_allowed)
        self.jog_btn_z_minus.setEnabled(jogging_allowed)
        self.jog_btn_z_plus.setEnabled(jogging_allowed)
        self.jog_btn_home.setEnabled(connected)
        self.jog_btn_set_origin.setEnabled(connected)
        
        self.jog_btn_unlock.setEnabled(connected)
        self.jog_btn_soft_reset.setEnabled(connected)
        # Quick Command Macros
        self.btn_home_macro.setEnabled(connected)
        self.btn_goto_zero.setEnabled(connected)
        self.btn_soft_reset_macro.setEnabled(connected)
        self.btn_unlock_macro.setEnabled(connected)
        self.btn_grbl_settings.setEnabled(connected)
        self.btn_grbl_parser_state.setEnabled(connected)
        self.btn_laser_test_on.setEnabled(connected)
        self.btn_laser_test_off.setEnabled(connected)

        self.laser_power_slider.setEnabled(connected)
        self.feed_rate_slider.setEnabled(connected)
        self.jog_step_input.setEnabled(connected)
        self.laser_threshold_input.setEnabled(connected)
        self.preview_resolution_input.setEnabled(connected)
        
        self.convert_to_gcode_button.setEnabled(connected and is_image_selected)
        
        if connected:
            self.connect_button.setText('Disconnect')
            self.status_label.setStyleSheet("font-weight: bold; color: #90ee90;")
        else:
            self.connect_button.setText('Connect')
            self.status_label.setStyleSheet("font-weight: bold; color: #ff6347;")

    def populate_serial_ports(self):
        """
        Populates the serial port combo box with available ports.
        
        Scans the system for available serial ports and adds them to the
        port selection combo box. If no ports are found, disables the
        connect button and shows appropriate message.
        """
        self.port_combo.clear()
        available_ports = QSerialPortInfo.availablePorts()
        if not available_ports:
            self.port_combo.addItem("No ports found")
            self.connect_button.setEnabled(False)
            self.update_ui_state(False)
        else:
            for port in available_ports:
                self.port_combo.addItem(f"{port.portName()} ({port.description()})", port.systemLocation())
            self.connect_button.setEnabled(True)
            self.update_ui_state(False)

    def toggle_connection(self):
        """
        Toggles the serial port connection state.
        
        If currently connected, disconnects from the serial port.
        If currently disconnected, attempts to connect to the selected port.
        """
        if self.serial_port.isOpen():
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        """
        Attempts to connect to the selected serial port.
        
        Configures the serial port with GRBL-standard settings (115200 baud, 8N1),
        attempts to open the connection, and initiates GRBL detection by sending
        a wake-up command. Provides user feedback through status updates and
        error dialogs.
        
        Returns:
            None
            
        Raises:
            No exceptions are raised; errors are handled gracefully with user notifications.
        """
        selected_port_path = self.port_combo.currentData()
        if not selected_port_path:
            QMessageBox.warning(self, "Connection Error", "Please select a serial port.")
            return

        # Configure serial port with GRBL standard settings
        try:
            self.serial_port.setPortName(selected_port_path)
            self.serial_port.setBaudRate(115200)
            self.serial_port.setDataBits(QSerialPort.DataBits.Data8)
            self.serial_port.setParity(QSerialPort.Parity.NoParity)
            self.serial_port.setStopBits(QSerialPort.StopBits.OneStop)
            self.serial_port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)

            if self.serial_port.open(QIODevice.OpenModeFlag.ReadWrite):
                self.status_label.setText(f'Status: Attempting to connect to: {self.port_combo.currentText()}...')
                self.connect_button.setEnabled(False)
                self.grbl_response_buffer = ""
                self.serial_port.readyRead.connect(self._read_grbl_detection_data)
                self.serial_port.write(b'\n')  # Send newline to wake up GRBL
                self.grbl_detect_timer.start(2000)  # Wait 2 seconds for GRBL response
            else:
                error_msg = self.serial_port.errorString()
                self.status_label.setText(f'Status: Connection failed: {error_msg}')
                self.connect_button.setEnabled(True)
                self.update_ui_state(False)
                
                # Provide more specific error messages based on common issues
                if "Permission denied" in error_msg or "Access denied" in error_msg:
                    error_detail = f"Permission denied. Try:\n• Closing other applications using this port\n• Running as administrator\n• Checking if the device is properly connected"
                elif "Device not found" in error_msg or "No such file" in error_msg:
                    error_detail = f"Device not found. Please:\n• Check if the device is connected\n• Verify the correct port is selected\n• Try refreshing the port list"
                else:
                    error_detail = f"Failed to connect to {self.port_combo.currentText()}:\n{error_msg}"
                    
                QMessageBox.critical(self, "Connection Error", error_detail)
                
        except Exception as e:
            # Handle any unexpected exceptions during port configuration
            error_msg = f"Unexpected error during connection setup: {str(e)}"
            self.status_label.setText(f'Status: Configuration error')
            self.connect_button.setEnabled(True)
            self.update_ui_state(False)
            QMessageBox.critical(self, "Connection Error", error_msg)

    def _read_grbl_detection_data(self):
        """Reads data specifically for GRBL detection during connection."""
        while self.serial_port.bytesAvailable():
            data = self.serial_port.readAll().data().decode('utf-8', errors='ignore')
            self.grbl_response_buffer += data
            self.grbl_output_text.append(f"<span style='color: #88dd88;'>[INFO] Waiting for GRBL: {data.strip()}</span>")

    def _check_grbl_response(self):
        """Checks the buffered response for GRBL signature after timer expires."""
        try:
            self.serial_port.readyRead.disconnect(self._read_grbl_detection_data)
        except TypeError: # Handle case where disconnect is called twice
            pass
        
        if "Grbl" in self.grbl_response_buffer:
            grbl_version_match = re.search(r"Grbl ([0-9.]+)", self.grbl_response_buffer)
            grbl_version = grbl_version_match.group(1) if grbl_version_match else "N/A"
            self.status_label.setText(f'Status: Connected to: {self.serial_port.portName()} (GRBL v{grbl_version})')
            self.connect_button.setText('Disconnect')
            self.update_ui_state(True)
            self.serial_port.readyRead.connect(self.read_data) # Connect to regular data reading
            self.status_timer.start(200) # Start requesting status updates
            QMessageBox.information(self, "Connection Successful", "GRBL Controller detected and connected successfully!")
            self.send_command("$$") # Request GRBL settings
            self.send_command("$G") # Request G-code parser state
        else:
            self.serial_port.close()
            self.status_label.setText(f'Status: Disconnected (GRBL not found)')
            self.connect_button.setText('Connect')
            self.connect_button.setEnabled(True)
            self.update_ui_state(False)
            QMessageBox.critical(self, "Detection Failed", "No GRBL Controller detected on this port. Please check port or GRBL power.")

    def disconnect_serial(self):
        """Disconnects from the serial port."""
        if self.serial_port.isOpen():
            self.serial_port.close()
            self.status_label.setText('Status: Disconnected')
            self.connect_button.setText('Connect')
            self.update_ui_state(False)
            self.status_timer.stop()
            self.gcode_send_timer.stop()
            self.gcode_to_send_queue = [] # Clear any pending commands
            self.gcode_lines_sent = 0
            self.gcode_current_line_index = -1
            self.total_gcode_lines = 0
            self.progress_bar.setValue(0)
            self.estimated_time_label.setText("Estimated Time: --:--:--")
            self._highlight_gcode_line(-1) # Clear highlighting
            try:
                self.serial_port.readyRead.disconnect(self.read_data)
            except TypeError:
                pass 
            try:
                self.serial_port.readyRead.disconnect(self._read_grbl_detection_data)
            except TypeError:
                pass 
            self.grbl_detect_timer.stop()
            QMessageBox.information(self, "Disconnected", "Connection terminated.")

    def read_data(self):
        """
        Reads data from the serial port, displays it, parses GRBL status,
        and triggers the sending of the next G-code command if 'ok' or 'error' is received.
        """
        while self.serial_port.bytesAvailable():
            data = self.serial_port.readAll().data().decode('utf-8', errors='ignore').strip()
            
            if data.startswith('<'):
                # GRBL real-time status report
                self.grbl_output_text.append(f"<span style='color: #00ffff;'>GRBL Status: {data}</span>")
                self.parse_grbl_status(data)
            elif data.startswith('ok'):
                # Command successfully executed
                self.grbl_output_text.append(f"<span style='color: #00ff00;'>GRBL: {data}</span>")
                if self.gcode_to_send_queue:
                    self.gcode_lines_sent += 1
                    self.update_gcode_progress()
                    # Trigger sending next command after 'ok'
                    if not self.gcode_send_timer.isActive():
                        self.gcode_send_timer.start(5) # Small delay to avoid flooding
                else:
                    # All commands sent and finished, if 'ok' comes when queue is empty
                    self.progress_bar.setValue(100)
                    elapsed_time = time.time() - self.gcode_start_time
                    self.estimated_time_label.setText(f"Completed in: {self._format_time(elapsed_time)}")
                    self._highlight_gcode_line(-1) # Clear highlighting
                    QMessageBox.information(self, "G-code Complete", "G-code transmission finished!")

            elif data.startswith('error'):
                # GRBL reported an error
                self.grbl_output_text.append(f"<span style='color: red;'>GRBL Error: {data}</span>")
                self.gcode_send_timer.stop()
                self.gcode_to_send_queue.clear()
                self.gcode_lines_sent = 0
                self.gcode_current_line_index = -1
                self.progress_bar.setValue(0)
                self.estimated_time_label.setText("Estimated Time: --:--:--")
                self._highlight_gcode_line(-1) # Clear highlighting
                QMessageBox.critical(self, "GRBL Error", f"GRBL reported an error: {data}\nG-code transmission stopped.")
            else:
                # Other GRBL messages
                self.grbl_output_text.append(f"GRBL: {data}")
            
            self.grbl_output_text.verticalScrollBar().setValue(self.grbl_output_text.verticalScrollBar().maximum())
            
    def send_command(self, command):
        """
        Sends a single command to GRBL via the serial connection.
        
        Args:
            command (str): The G-code or GRBL command to send (without newline)
            
        Returns:
            bool: True if command was sent successfully, False otherwise
            
        Note:
            Commands are automatically terminated with a newline character.
            All sent commands are logged to the output console.
        """
        if not self.serial_port.isOpen():
            QMessageBox.warning(self, "Error", "Not connected to Arduino. Please connect first.")
            return False
        
        if not command or not command.strip():
            QMessageBox.warning(self, "Error", "Cannot send empty command.")
            return False
        
        # Clean and prepare the command
        command = command.strip()
        command_b = (command + '\n').encode('utf-8')
        
        try:
            bytes_written = self.serial_port.write(command_b)
            if bytes_written == -1:
                error_msg = f"Failed to write to serial port: {self.serial_port.errorString()}"
                self.grbl_output_text.append(f"<span style='color: red;'>[ERROR] {error_msg}</span>")
                QMessageBox.critical(self, "Send Error", error_msg)
                return False
            elif bytes_written != len(command_b):
                warning_msg = f"Partial write: {bytes_written}/{len(command_b)} bytes sent"
                self.grbl_output_text.append(f"<span style='color: orange;'>[WARNING] {warning_msg}</span>")
            
            # Log successful command
            self.grbl_output_text.append(f"<span style='color: #ffff00;'>Sent: {command}</span>")
            self.grbl_output_text.verticalScrollBar().setValue(self.grbl_output_text.verticalScrollBar().maximum())
            return True
            
        except Exception as e:
            error_msg = f"Unexpected error sending command '{command}': {str(e)}"
            self.grbl_output_text.append(f"<span style='color: red;'>[ERROR] {error_msg}</span>")
            QMessageBox.critical(self, "Send Error", error_msg)
            return False

    def _send_next_gcode_command(self):
        """Sends the next G-code command from the queue."""
        if self.gcode_to_send_queue:
            command = self.gcode_to_send_queue.pop(0)
            self.gcode_current_line_index += 1 # Increment for highlighting the next line
            self.send_command(command)
            self._highlight_gcode_line(self.gcode_current_line_index)
            # Update preview dynamically for movements (G0, G1)
            # self._update_preview_path(command) # This function will be called by status reports
        else:
            self.gcode_send_timer.stop() # Stop timer if queue is empty
            # Final progress update if not already done by 'ok' response
            if self.progress_bar.value() < 100:
                self.progress_bar.setValue(100)
                elapsed_time = time.time() - self.gcode_start_time
                self.estimated_time_label.setText(f"Completed in: {self._format_time(elapsed_time)}")
                self._highlight_gcode_line(-1) # Clear highlighting
                QMessageBox.information(self, "G-code Complete", "G-code transmission finished!")


    def parse_grbl_status(self, status_string):
        """Parses the GRBL status string and updates UI."""
        # Example: <Idle|WPos:0.000,0.000,0.000|Bf:15,128|FS:0,0|Ov:100,100,100|A:S>
        
        # Extract status (e.g., Idle, Run, Hold, Jog, Alarm)
        status_match = re.search(r'<(Idle|Run|Hold|Jog|Alarm|Check|Door|Home|Sleep)', status_string)
        if status_match:
            self.grbl_status = status_match.group(1)
            self.status_label.setText(f'Status: {self.grbl_status}')
            if self.grbl_status == "Idle":
                self.status_label.setStyleSheet("font-weight: bold; color: #90ee90;")
            elif self.grbl_status == "Run" or self.grbl_status == "Jog":
                self.status_label.setStyleSheet("font-weight: bold; color: #00bfff;") # Deep Sky Blue
            elif self.grbl_status == "Hold" or self.grbl_status == "Alarm":
                self.status_label.setStyleSheet("font-weight: bold; color: #ff4500;") # Orange Red
            else:
                self.status_label.setStyleSheet("font-weight: bold; color: #cccccc;") # Default neutral color
        
        # Extract Work Position (WPos)
        wpos_match = re.search(r'WPos:([-\d.]+),([-\d.]+),([-\d.]+)', status_string)
        if wpos_match:
            self.current_x = float(wpos_match.group(1))
            self.current_y = float(wpos_match.group(2))
            self.current_z = float(wpos_match.group(3))
            self.pos_label.setText(f'Position (WPos): X: {self.current_x:.2f} Y: {self.current_y:.2f} Z: {self.current_z:.2f}')
            self._update_preview_current_position() # Update the dot on preview

        self.update_ui_state(self.serial_port.isOpen()) # Update button states based on new status


    def request_grbl_status(self):
        """Requests a status report from GRBL."""
        if self.serial_port.isOpen():
            self.serial_port.write(b'?') # '?' is the real-time status report request


    def send_jog_command(self, dx, dy):
        """Sends a jog command for X and Y axes."""
        if self.serial_port.isOpen() and self.grbl_status in ["Idle", "Jog"]:
            current_feed_rate = self.feed_rate_slider.value()
            # Use G91 for relative movement and G21 for millimeters
            command = f"$J=G91 G21 X{dx} Y{dy} F{current_feed_rate}"
            self.send_command(command)
        else:
            QMessageBox.warning(self, "Jogging Not Possible", "Please connect or ensure GRBL is in 'Idle' or 'Jog' state.")

    def send_jog_command_z(self, dz):
        """Sends a jog command for Z axis."""
        if self.serial_port.isOpen() and self.grbl_status in ["Idle", "Jog"]:
            current_feed_rate = self.feed_rate_slider.value()
            command = f"$J=G91 G21 Z{dz} F{current_feed_rate}"
            self.send_command(command)
        else:
            QMessageBox.warning(self, "Jogging Not Possible", "Please connect or ensure GRBL is in 'Idle' or 'Jog' state.")

    def update_jog_step(self):
        """Updates the jogging step from the input field."""
        try:
            self.jog_step = float(self.jog_step_input.text())
        except ValueError:
            self.jog_step = 1.0 # Fallback to default
            self.jog_step_input.setText(str(self.jog_step))
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for jog step.")

    def set_origin(self):
        """Sends the G92 X0 Y0 Z0 command to set current position as origin."""
        if self.serial_port.isOpen():
            confirm = QMessageBox.question(self, "Set Origin",
                                           "Are you sure you want to set the current position as the work origin (work zero)?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.send_command('G92 X0 Y0 Z0')
                self.send_command('G10 P0 L20 X0 Y0 Z0') # Set work offset (WCO) to current position
                QMessageBox.information(self, "Success", "Work origin has been set to the current position.")
        else:
            QMessageBox.warning(self, "Error", "Not connected to Arduino. Please connect first.")

    def update_laser_power_label(self):
        """Updates the laser power label as slider moves."""
        self.laser_power_label.setText(f'S: {self.laser_power_slider.value()}')

    def send_laser_power_command(self):
        """Sends a G-code command to set laser power (M3 SXXX) or turn off (M5)."""
        if self.serial_port.isOpen():
            power = self.laser_power_slider.value()
            if power > 0:
                self.send_command(f'M3 S{power}')
            else:
                self.send_command('M5') # M5 turns off laser/spindle
        else:
            QMessageBox.warning(self, "Error", "Not connected to Arduino.")

    def update_feed_rate_label(self):
        """Updates the feed rate label as slider moves."""
        self.feed_rate_label.setText(f'F: {self.feed_rate_slider.value()}')

    def send_feed_rate_command(self):
        """Sends a G-code command to set feed rate (G1 FXXX)."""
        if self.serial_port.isOpen():
            feed_rate = self.feed_rate_slider.value()
            self.send_command(f'G1 F{feed_rate}') # This sets the default feed rate
        else:
            QMessageBox.warning(self, "Error", "Not connected to Arduino.")

    def select_image(self):
        """Opens a file dialog to select an image file."""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.image_path = selected_files[0]
                self.image_path_label.setText(f"Selected: {self.image_path.split('/')[-1]}")
                self.convert_to_gcode_button.setEnabled(self.serial_port.isOpen()) # Enable conversion button
            else:
                self.image_path = None
                self.image_path_label.setText("No image selected.")
                self.convert_to_gcode_button.setEnabled(False)

    def update_laser_threshold(self):
        """Updates the laser threshold from the input field."""
        try:
            self.laser_threshold = int(self.laser_threshold_input.text())
            if not (0 <= self.laser_threshold <= 255):
                raise ValueError("Threshold out of range")
        except ValueError:
            self.laser_threshold = 200 # Fallback
            self.laser_threshold_input.setText(str(self.laser_threshold))
            QMessageBox.warning(self, "Invalid Input", "Laser Threshold must be an integer from 0 to 255.")

    def update_preview_resolution(self):
        """Updates the preview resolution (pixels per mm) from the input field."""
        try:
            self.preview_image_resolution_ppm = int(self.preview_resolution_input.text())
            if not (1 <= self.preview_image_resolution_ppm <= 50):
                raise ValueError("Resolution out of range")
        except ValueError:
            self.preview_image_resolution_ppm = 5 # Fallback
            self.preview_resolution_input.setText(str(self.preview_image_resolution_ppm))
            QMessageBox.warning(self, "Invalid Input", "Resolution must be an integer from 1 to 50.")

    def convert_image_to_gcode(self):
        """
        Converts the selected image to G-code for laser engraving.
        
        This method processes a grayscale image and generates G-code commands
        suitable for laser engraving. The conversion process:
        1. Loads and converts the image to grayscale
        2. Resizes to specified dimensions 
        3. Scans pixel by pixel to generate laser movements
        4. Creates G00 (rapid move) and G01 (laser engraving) commands
        
        The laser is turned on/off based on the pixel intensity threshold.
        Darker pixels (below threshold) trigger laser activation.
        
        Returns:
            None (updates the G-code console and preview)
            
        Raises:
            No exceptions are raised; errors are handled with user notifications.
        """
        if not self.image_path:
            QMessageBox.warning(self, "Error", "Please select an image first.")
            return

        # Validate input dimensions
        try:
            target_width_mm = float(self.width_input.text())
            target_height_mm = float(self.height_input.text())
            if target_width_mm <= 0 or target_height_mm <= 0:
                raise ValueError("Dimensions must be positive.")
            if target_width_mm > 1000 or target_height_mm > 1000:
                raise ValueError("Dimensions too large (max 1000mm).")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", 
                              f"Please enter valid dimensions (1-1000mm):\n{str(e)}")
            return

        # Load and validate image
        try:
            img = Image.open(self.image_path).convert('L')  # Convert to grayscale
            if img.size[0] == 0 or img.size[1] == 0:
                raise ValueError("Image has zero dimensions.")
        except Exception as e:
            QMessageBox.critical(self, "Image Loading Error", 
                               f"Failed to load image '{self.image_path}':\n{str(e)}")
            return

        # Calculate pixels based on target mm and PPM
        img_width_px = int(target_width_mm * self.preview_image_resolution_ppm)
        img_height_px = int(target_height_mm * self.preview_image_resolution_ppm)
        
        # Resize without maintaining aspect ratio to fit the specified dimensions
        img = img.resize((img_width_px, img_height_px), Image.Resampling.LANCZOS)
        
        gcode_commands = []
        
        # Initial G-code commands
        gcode_commands.append("G21")  # Set units to millimeters
        gcode_commands.append("G90")  # Set absolute positioning
        gcode_commands.append("G17")  # XY plane
        gcode_commands.append(f"F{self.feed_rate_slider.value()}") # Set initial feed rate
        gcode_commands.append("M5 S0") # Ensure laser is off and power is zero at start

        # Iterate through pixels and generate G-code
        # Using a simple row-by-row (raster) scan with zig-zag movement for efficiency
        
        # Start at Y=0 (bottom) and go up. Image origin (0,0) is usually top-left, GRBL (0,0) is bottom-left.
        # We need to invert Y for G-code if image origin is top-left.
        
        for y_px in range(img_height_px):
            # Map image Y-coordinate to G-code Y-coordinate (invert for bottom-left origin)
            grbl_y_mm = y_px / self.preview_image_resolution_ppm # No inversion here, assuming image y_px grows downwards

            if y_px % 2 == 0:  # Even row (0, 2, 4...): Left to Right
                for x_px in range(img_width_px):
                    grbl_x_mm = x_px / self.preview_image_resolution_ppm
                    
                    pixel_intensity = img.getpixel((x_px, y_px)) # Get pixel from PIL image
                    
                    # If dark enough, laser ON. Scale 0-255 (image) to 0-1000 (GRBL). Darker = higher power.
                    if pixel_intensity < self.laser_threshold:
                        # Invert intensity for laser power: 0 intensity (black) = max power, 255 (white) = min power
                        laser_power = int(1000 * (1 - pixel_intensity / 255.0))
                        laser_power = max(1, min(1000, laser_power)) # Ensure it's between 1 and 1000
                        gcode_commands.append(f"M3 S{laser_power} G1 X{grbl_x_mm:.3f} Y{grbl_y_mm:.3f}")
                    else: # If too bright, laser OFF (move without burning)
                        gcode_commands.append(f"M5 S0 G0 X{grbl_x_mm:.3f} Y{grbl_y_mm:.3f}")
            else:  # Odd row (1, 3, 5...): Right to Left
                for x_px in range(img_width_px - 1, -1, -1): # Iterate backwards
                    grbl_x_mm = x_px / self.preview_image_resolution_ppm
                    
                    pixel_intensity = img.getpixel((x_px, y_px))
                    
                    if pixel_intensity < self.laser_threshold:
                        laser_power = int(1000 * (1 - pixel_intensity / 255.0))
                        laser_power = max(1, min(1000, laser_power))
                        gcode_commands.append(f"M3 S{laser_power} G1 X{grbl_x_mm:.3f} Y{grbl_y_mm:.3f}")
                    else:
                        gcode_commands.append(f"M5 S0 G0 X{grbl_x_mm:.3f} Y{grbl_y_mm:.3f}")
            
            # After each row, ensure the laser is off before moving to the next row (if not already off)
            gcode_commands.append("M5 S0") 

        gcode_commands.append("G0 X0 Y0") # Return to origin
        gcode_commands.append("M5 S0") # Ensure laser is off
        
        gcode_str = "\n".join(gcode_commands)
        self.gcode_input.setText(gcode_str)
        QMessageBox.information(self, "Conversion Complete", "Image successfully converted to G-code.")
        
        # Update preview with the newly generated G-code
        self.preview_gcode(gcode_commands)

    def preview_gcode(self, gcode_commands_list):
        """Draws the G-code path on the QGraphicsScene."""
        self.graphics_scene.clear() # Clear previous drawings

        # Draw grid
        scene_width = float(self.width_input.text()) if self.width_input.text() else 50
        scene_height = float(self.height_input.text()) if self.height_input.text() else 50
        
        # Set scene rect based on the image dimensions
        self.graphics_scene.setSceneRect(0, 0, scene_width, scene_height)

        grid_pen = QPen(QColor(60, 60, 60), 0.5) # Darker gray for grid
        
        # Draw horizontal lines
        for y in range(int(scene_height) + 1):
            self.graphics_scene.addLine(0, y, scene_width, y, grid_pen)
        # Draw vertical lines
        for x in range(int(scene_width) + 1):
            self.graphics_scene.addLine(x, 0, x, scene_height, grid_pen)

        # Draw origin (0,0) crosshairs
        origin_pen = QPen(QColor(255, 0, 0), 1.5) # Red for origin
        self.graphics_scene.addLine(-2, 0, 2, 0, origin_pen) # X
        self.graphics_scene.addLine(0, -2, 0, 2, origin_pen) # Y

        # Draw bounds rectangle
        bounds_pen = QPen(QColor(100, 100, 255), 2) # Blue for bounds
        self.graphics_scene.addRect(0, 0, scene_width, scene_height, bounds_pen)

        # G-code Path Visualization
        # We will store the path to draw segment by segment during execution,
        # but for initial preview, we draw the full path.
        self.gcode_path_items = [] # Store individual line items for dynamic update
        
        current_preview_x = 0.0
        current_preview_y = 0.0
        
        for command in gcode_commands_list:
            command = command.strip().upper()
            
            # Ignore comments, empty lines
            if not command or command.startswith('(') or command.startswith(';'):
                continue
            
            # Extract G0/G1 movements
            # Using regex to find X and Y coordinates in G0/G1 commands
            match_g0_g1 = re.search(r'(G0|G1)\s*(?:X([-\d.]+))?\s*(?:Y([-\d.]+))?', command)
            if match_g0_g1:
                cmd_type = match_g0_g1.group(1)
                new_x_str = match_g0_g1.group(2)
                new_y_str = match_g0_g1.group(3)
                
                # Update coordinates only if present in the command
                new_x = float(new_x_str) if new_x_str is not None else current_preview_x
                new_y = float(new_y_str) if new_y_str is not None else current_preview_y
                
                # Check for laser power (M3 SXXX) for color coding
                is_laser_on = "M3" in command and "S" in command # Simple check
                
                # Add line segment to the path for preview
                path_pen = QPen(QColor(0, 200, 0) if is_laser_on else QColor(200, 200, 200), 0.5) # Green for laser on, grey for rapid/off
                line = self.graphics_scene.addLine(current_preview_x, current_preview_y, new_x, new_y, path_pen)
                self.gcode_path_items.append(line)

                current_preview_x = new_x
                current_preview_y = new_y
            
        # Add the current position indicator after drawing the full path
        self._update_preview_current_position()

        # Center and fit the view
        self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.graphics_view.centerOn(self.graphics_scene.sceneRect().center())


    def _update_preview_current_position(self):
        """Updates the yellow dot representing the GRBL's current work position on the graphics scene."""
        # Remove old "current position" indicator if exists
        for item in self.graphics_scene.items():
            if hasattr(item, '_is_current_pos_indicator') and item._is_current_pos_indicator:
                self.graphics_scene.removeItem(item)
        
        # Add new current position indicator
        # Scale indicator size based on scene dimensions for better visibility
        scene_width = self.graphics_scene.sceneRect().width()
        scene_height = self.graphics_scene.sceneRect().height()
        
        if scene_width > 0 and scene_height > 0:
            pos_indicator_size = max(1.0, min(scene_width, scene_height) / 50) # Make it ~1/50th of smallest dimension
        else:
            pos_indicator_size = 1.0 # Default if scene not yet defined
            
        current_pos_rect = QGraphicsRectItem(self.current_x - pos_indicator_size/2, self.current_y - pos_indicator_size/2, pos_indicator_size, pos_indicator_size)
        current_pos_rect.setBrush(QColor(255, 255, 0)) # Yellow dot
        current_pos_rect.setPen(QPen(Qt.PenStyle.NoPen))
        current_pos_rect._is_current_pos_indicator = True # Custom attribute to identify it
        self.graphics_scene.addItem(current_pos_rect)


    def graphics_view_wheelEvent(self, event):
        """Handles zooming with the mouse wheel for the graphics view."""
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            self.graphics_view.scale(zoom_factor, zoom_factor)
        else:
            self.graphics_view.scale(1 / zoom_factor, 1 / zoom_factor)

    def send_gcode(self):
        """Starts sending G-code commands from the QTextEdit."""
        gcode_text = self.gcode_input.toPlainText()
        self.gcode_to_send_queue = [
            line.strip() for line in gcode_text.split('\n') 
            if line.strip() and not line.strip().startswith(';') and not line.strip().startswith('(') # Filter out comments and empty lines
        ]
        
        if not self.gcode_to_send_queue:
            QMessageBox.warning(self, "G-code", "No G-code found to send.")
            return

        if not self.serial_port.isOpen():
            QMessageBox.warning(self, "Error", "Not connected to Arduino. Please connect first.")
            return
        
        confirm = QMessageBox.question(self, "Start G-code Transmission",
                                       f"Are you sure you want to start transmitting {len(self.gcode_to_send_queue)} lines of G-code?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.total_gcode_lines = len(self.gcode_to_send_queue)
            self.gcode_lines_sent = 0
            self.gcode_current_line_index = -1 # Reset to -1, will become 0 on first send
            self.progress_bar.setValue(0)
            self.estimated_time_label.setText("Estimated Time: Calculating...")
            self.gcode_start_time = time.time() # Record start time

            self._send_next_gcode_command() # Start the sending process
            QMessageBox.information(self, "Started", "G-code transmission has begun.")
        else:
            self.gcode_to_send_queue = [] # Clear queue if user cancels

    def update_gcode_progress(self):
        """Updates the progress bar and estimated time."""
        if self.total_gcode_lines > 0:
            progress_percent = int((self.gcode_lines_sent / self.total_gcode_lines) * 100)
            self.progress_bar.setValue(progress_percent)

            if self.gcode_lines_sent > 0:
                elapsed_time = time.time() - self.gcode_start_time
                if elapsed_time > 0:
                    # Estimate remaining time
                    time_per_line = elapsed_time / self.gcode_lines_sent
                    remaining_lines = self.total_gcode_lines - self.gcode_lines_sent
                    estimated_remaining_time = remaining_lines * time_per_line
                    
                    total_estimated_time = elapsed_time + estimated_remaining_time
                    self.estimated_time_label.setText(f"Estimated Time: {self._format_time(total_estimated_time)}")
            else:
                self.estimated_time_label.setText("Estimated Time: Calculating...")
        else:
            self.progress_bar.setValue(0)
            self.estimated_time_label.setText("Estimated Time: --:--:--")

    def _format_time(self, seconds):
        """Formats seconds into HH:MM:SS string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02}:{minutes:02}:{secs:02}"

    def _highlight_gcode_line(self, line_index):
        """Highlights the specified line in the gcode_input QTextEdit."""
        # Clear previous highlighting
        format = QTextCharFormat()
        format.setBackground(QColor(0, 0, 0, 0)) # Transparent background
        cursor = QTextCursor(self.gcode_input.document())
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.setCharFormat(format)

        if line_index >= 0 and line_index < self.gcode_input.document().blockCount():
            # Apply new highlighting
            highlight_format = QTextCharFormat()
            highlight_format.setBackground(QColor(50, 150, 255, 100)) # Light blue with transparency

            cursor.setPosition(0)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line_index)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            cursor.setCharFormat(highlight_format)
            
            # Scroll to make the highlighted line visible
            self.gcode_input.ensureCursorVisible()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LaserControllerApp()
    ex.show()
    sys.exit(app.exec())