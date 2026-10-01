from __future__ import annotations

import html
import math
import re
import sys
from pathlib import Path

from PyQt6.QtCore import QIODeviceBase, Qt, QTimer
from PyQt6.QtGui import QAction, QCloseEvent, QColor, QFont, QKeySequence, QPainter, QPen
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGraphicsEllipseItem,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .gcode import RasterSettings, image_to_gcode, parse_motion_segments
from .grbl import GCodeStreamer, GrblLineBuffer, GrblStatus, StreamState, parse_status_report


class PreviewView(QGraphicsView):
    def wheelEvent(self, event) -> None:  # noqa: N802
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)


class LaserControllerWindow(QMainWindow):
    def __init__(self, demo_mode: bool = False) -> None:
        super().__init__()
        self.demo_mode = demo_mode
        self.connected = False
        self.connecting = False
        self.image_path: Path | None = None
        self.status_report = GrblStatus(raw="", state="Disconnected")
        self.current_position = (0.0, 0.0, 0.0)
        self.position_marker: QGraphicsEllipseItem | None = None
        self.line_buffer = GrblLineBuffer()
        self.streamer = GCodeStreamer()

        self.serial_port = QSerialPort(self)
        self.serial_port.readyRead.connect(self._read_serial_data)
        self.serial_port.errorOccurred.connect(self._serial_error)

        self.status_timer = QTimer(self)
        self.status_timer.setInterval(400)
        self.status_timer.timeout.connect(self.request_status)

        self.detection_timer = QTimer(self)
        self.detection_timer.setSingleShot(True)
        self.detection_timer.timeout.connect(self._detection_failed)

        self.job_timer = QTimer(self)
        self.job_timer.setInterval(500)
        self.job_timer.timeout.connect(self._update_job_progress)

        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(350)
        self.preview_timer.timeout.connect(self.render_preview)

        self._build_interface()
        self._apply_theme()
        self.populate_ports()
        self._set_connected(False)

        if self.demo_mode:
            self._load_demo_job()

    def _build_interface(self) -> None:
        self.setWindowTitle("LaserGRBL for macOS")
        self.setMinimumSize(1_100, 720)
        self.resize(1_440, 900)

        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 16, 18, 18)
        root_layout.setSpacing(14)

        header_layout = QHBoxLayout()
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title = QLabel("LaserGRBL for macOS")
        title.setObjectName("appTitle")
        subtitle = QLabel("A focused GRBL workspace for makers, engravers, and CNC builders.")
        subtitle.setObjectName("appSubtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        self.status_chip = QLabel("DISCONNECTED")
        self.status_chip.setObjectName("statusChip")
        self.status_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.status_chip)

        self.emergency_button = QPushButton("STOP / RESET")
        self.emergency_button.setObjectName("dangerButton")
        self.emergency_button.clicked.connect(lambda: self.abort_job(confirm=False))
        header_layout.addWidget(self.emergency_button)
        root_layout.addLayout(header_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_control_panel())
        splitter.addWidget(self._build_workspace())
        splitter.setSizes([430, 950])
        root_layout.addWidget(splitter, 1)

        self.setCentralWidget(root)
        self.statusBar().showMessage("Ready")
        self._build_menu()

    def _build_control_panel(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 10, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_connection_card())
        layout.addWidget(self._build_motion_card())
        layout.addWidget(self._build_laser_card())
        layout.addWidget(self._build_artwork_card())
        layout.addWidget(self._build_job_card())
        layout.addStretch()
        scroll.setWidget(panel)
        return scroll

    def _build_connection_card(self) -> QGroupBox:
        group = QGroupBox("Connection")
        layout = QVBoxLayout(group)
        row = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.populate_ports)
        row.addWidget(self.port_combo, 1)
        row.addWidget(self.refresh_button)
        layout.addLayout(row)

        self.connect_button = QPushButton("Connect at 115200 baud")
        self.connect_button.setObjectName("primaryButton")
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)

        self.machine_state_label = QLabel("Machine state: Disconnected")
        self.position_label = QLabel("Work position  X 0.000   Y 0.000   Z 0.000")
        self.position_label.setObjectName("coordinateLabel")
        layout.addWidget(self.machine_state_label)
        layout.addWidget(self.position_label)
        return group

    def _build_motion_card(self) -> QGroupBox:
        group = QGroupBox("Motion")
        layout = QVBoxLayout(group)
        step_row = QHBoxLayout()
        step_row.addWidget(QLabel("Jog step"))
        self.jog_step = QDoubleSpinBox()
        self.jog_step.setRange(0.01, 1_000)
        self.jog_step.setDecimals(2)
        self.jog_step.setValue(1.0)
        self.jog_step.setSuffix(" mm")
        step_row.addWidget(self.jog_step, 1)
        layout.addLayout(step_row)

        grid = QGridLayout()
        self.y_plus_button = QPushButton("Y+")
        self.x_minus_button = QPushButton("X−")
        self.home_button = QPushButton("Home")
        self.x_plus_button = QPushButton("X+")
        self.y_minus_button = QPushButton("Y−")
        self.z_plus_button = QPushButton("Z+")
        self.z_minus_button = QPushButton("Z−")
        grid.addWidget(self.y_plus_button, 0, 1)
        grid.addWidget(self.z_plus_button, 0, 2)
        grid.addWidget(self.x_minus_button, 1, 0)
        grid.addWidget(self.home_button, 1, 1)
        grid.addWidget(self.x_plus_button, 1, 2)
        grid.addWidget(self.y_minus_button, 2, 1)
        grid.addWidget(self.z_minus_button, 2, 2)
        layout.addLayout(grid)

        self.y_plus_button.clicked.connect(lambda: self.jog(y=self.jog_step.value()))
        self.y_minus_button.clicked.connect(lambda: self.jog(y=-self.jog_step.value()))
        self.x_plus_button.clicked.connect(lambda: self.jog(x=self.jog_step.value()))
        self.x_minus_button.clicked.connect(lambda: self.jog(x=-self.jog_step.value()))
        self.z_plus_button.clicked.connect(lambda: self.jog(z=self.jog_step.value()))
        self.z_minus_button.clicked.connect(lambda: self.jog(z=-self.jog_step.value()))
        self.home_button.clicked.connect(lambda: self.send_command("$H"))

        action_row = QHBoxLayout()
        self.unlock_button = QPushButton("Unlock")
        self.zero_button = QPushButton("Set work zero")
        self.unlock_button.clicked.connect(lambda: self.send_command("$X"))
        self.zero_button.clicked.connect(self.set_work_zero)
        action_row.addWidget(self.unlock_button)
        action_row.addWidget(self.zero_button)
        layout.addLayout(action_row)

        self.motion_controls = [
            self.y_plus_button,
            self.y_minus_button,
            self.x_plus_button,
            self.x_minus_button,
            self.z_plus_button,
            self.z_minus_button,
            self.home_button,
            self.unlock_button,
            self.zero_button,
            self.jog_step,
        ]
        return group

    def _build_laser_card(self) -> QGroupBox:
        group = QGroupBox("Laser and feed")
        layout = QVBoxLayout(group)

        power_row = QHBoxLayout()
        power_row.addWidget(QLabel("Maximum power"))
        self.power_slider = QSlider(Qt.Orientation.Horizontal)
        self.power_slider.setRange(1, 1_000)
        self.power_slider.setValue(500)
        self.power_value = QLabel("S500")
        self.power_slider.valueChanged.connect(lambda value: self.power_value.setText(f"S{value}"))
        power_row.addWidget(self.power_slider, 1)
        power_row.addWidget(self.power_value)
        layout.addLayout(power_row)

        feed_row = QHBoxLayout()
        feed_row.addWidget(QLabel("Feed rate"))
        self.feed_rate = QSpinBox()
        self.feed_rate.setRange(1, 100_000)
        self.feed_rate.setValue(1_000)
        self.feed_rate.setSuffix(" mm/min")
        feed_row.addWidget(self.feed_rate, 1)
        layout.addLayout(feed_row)

        self.test_enable = QCheckBox("Enable low-power test control")
        self.test_enable.toggled.connect(self._update_controls)
        layout.addWidget(self.test_enable)
        self.test_button = QPushButton("Hold for 1% laser test")
        self.test_button.setObjectName("warningButton")
        self.test_button.pressed.connect(self.start_laser_test)
        self.test_button.released.connect(self.stop_laser_test)
        layout.addWidget(self.test_button)
        return group

    def _build_artwork_card(self) -> QGroupBox:
        group = QGroupBox("Artwork and G-code")
        layout = QVBoxLayout(group)
        file_row = QHBoxLayout()
        self.image_button = QPushButton("Open image")
        self.gcode_open_button = QPushButton("Open G-code")
        self.image_button.clicked.connect(self.select_image)
        self.gcode_open_button.clicked.connect(self.open_gcode)
        file_row.addWidget(self.image_button)
        file_row.addWidget(self.gcode_open_button)
        layout.addLayout(file_row)

        self.selected_file_label = QLabel("No artwork selected")
        self.selected_file_label.setWordWrap(True)
        layout.addWidget(self.selected_file_label)

        settings = QGridLayout()
        self.width_input = QDoubleSpinBox()
        self.height_input = QDoubleSpinBox()
        for field in (self.width_input, self.height_input):
            field.setRange(0.1, 1_000)
            field.setDecimals(1)
            field.setValue(50)
            field.setSuffix(" mm")
        self.resolution_input = QSpinBox()
        self.resolution_input.setRange(1, 20)
        self.resolution_input.setValue(3)
        self.resolution_input.setSuffix(" px/mm")
        self.threshold_input = QSpinBox()
        self.threshold_input.setRange(0, 255)
        self.threshold_input.setValue(220)
        settings.addWidget(QLabel("Width"), 0, 0)
        settings.addWidget(self.width_input, 0, 1)
        settings.addWidget(QLabel("Height"), 1, 0)
        settings.addWidget(self.height_input, 1, 1)
        settings.addWidget(QLabel("Resolution"), 0, 2)
        settings.addWidget(self.resolution_input, 0, 3)
        settings.addWidget(QLabel("Threshold"), 1, 2)
        settings.addWidget(self.threshold_input, 1, 3)
        layout.addLayout(settings)

        action_row = QHBoxLayout()
        self.generate_button = QPushButton("Generate G-code")
        self.generate_button.setObjectName("primaryButton")
        self.generate_button.clicked.connect(self.generate_gcode)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_gcode)
        action_row.addWidget(self.generate_button, 1)
        action_row.addWidget(self.save_button)
        layout.addLayout(action_row)
        return group

    def _build_job_card(self) -> QGroupBox:
        group = QGroupBox("Job")
        layout = QVBoxLayout(group)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.job_detail_label = QLabel("No active job")
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.job_detail_label)

        row = QHBoxLayout()
        self.start_button = QPushButton("Start job")
        self.start_button.setObjectName("primaryButton")
        self.pause_button = QPushButton("Pause")
        self.abort_button = QPushButton("Abort")
        self.abort_button.setObjectName("dangerButton")
        self.start_button.clicked.connect(self.start_job)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.abort_button.clicked.connect(self.abort_job)
        row.addWidget(self.start_button, 1)
        row.addWidget(self.pause_button)
        row.addWidget(self.abort_button)
        layout.addLayout(row)
        return group

    def _build_workspace(self) -> QTabWidget:
        tabs = QTabWidget()

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(8, 8, 8, 8)
        self.preview_scene = QGraphicsScene(self)
        self.preview_view = PreviewView(self.preview_scene)
        self.preview_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.preview_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.preview_view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        preview_layout.addWidget(self.preview_view)
        fit_button = QPushButton("Fit preview")
        fit_button.clicked.connect(self.fit_preview)
        preview_layout.addWidget(fit_button, alignment=Qt.AlignmentFlag.AlignRight)
        tabs.addTab(preview_container, "Path preview")

        self.gcode_editor = QTextEdit()
        self.gcode_editor.setAcceptRichText(False)
        self.gcode_editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.gcode_editor.setPlaceholderText("Open, generate, or paste G-code here.")
        self.gcode_editor.setFont(QFont("Menlo", 11))
        self.gcode_editor.textChanged.connect(lambda: self.preview_timer.start())
        self.gcode_editor.textChanged.connect(self._update_controls)
        tabs.addTab(self.gcode_editor, "G-code")

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.console.setObjectName("console")
        self.console.setFont(QFont("Menlo", 10))
        tabs.addTab(self.console, "Console")
        self.workspace_tabs = tabs
        return tabs

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        open_image_action = QAction("Open Image…", self)
        open_image_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_image_action.triggered.connect(self.select_image)
        file_menu.addAction(open_image_action)
        open_gcode_action = QAction("Open G-code…", self)
        open_gcode_action.setShortcut(QKeySequence.StandardKey.Open)
        open_gcode_action.triggered.connect(self.open_gcode)
        file_menu.addAction(open_gcode_action)
        save_action = QAction("Save G-code…", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_gcode)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        machine_menu = self.menuBar().addMenu("Machine")
        machine_menu.addAction("Refresh Ports", self.populate_ports)
        machine_menu.addAction("Request Settings ($$)", lambda: self.send_command("$$"))
        machine_menu.addAction("Request Parser State ($G)", lambda: self.send_command("$G"))
        machine_menu.addAction("Soft Reset", lambda: self.send_realtime(b"\x18"))

        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("Laser Safety", self.show_safety)
        help_menu.addAction("About", self.show_about)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QWidget { background: #11151c; color: #e7edf5; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text'; font-size: 13px; }
            QMenuBar { background: #11151c; padding: 4px; }
            QMenuBar::item:selected, QMenu::item:selected { background: #2a3442; border-radius: 4px; }
            QMenu { background: #1a202a; border: 1px solid #344052; padding: 6px; }
            QLabel#appTitle { font-size: 26px; font-weight: 700; color: #ffffff; }
            QLabel#appSubtitle { color: #8f9cac; font-size: 13px; }
            QLabel#statusChip { background: #2b323d; color: #a8b3c2; border: 1px solid #3c4654; border-radius: 12px; padding: 5px 12px; font-weight: 700; }
            QLabel#coordinateLabel { font-family: Menlo, monospace; color: #70d6a8; }
            QGroupBox { background: #1a202a; border: 1px solid #2d3745; border-radius: 10px; margin-top: 12px; padding: 14px 12px 12px; font-weight: 650; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #b8c2d0; }
            QPushButton { background: #26303d; border: 1px solid #3a4758; border-radius: 7px; padding: 7px 11px; min-height: 24px; font-weight: 600; }
            QPushButton:hover { background: #303c4b; border-color: #59687a; }
            QPushButton:pressed { background: #1f2732; }
            QPushButton:disabled { color: #5f6875; background: #191e26; border-color: #252c36; }
            QPushButton#primaryButton { background: #e56b2f; border-color: #f08249; color: #ffffff; }
            QPushButton#primaryButton:hover { background: #f0783a; }
            QPushButton#dangerButton { background: #4a2228; border-color: #8d3943; color: #ffb6bd; }
            QPushButton#dangerButton:hover { background: #652c34; }
            QPushButton#warningButton { background: #3b3020; border-color: #7b6335; color: #f8d98d; }
            QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit { background: #0e1218; border: 1px solid #303b49; border-radius: 6px; padding: 6px; selection-background-color: #e56b2f; }
            QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus { border-color: #e56b2f; }
            QTextEdit#console { color: #9fe8c4; background: #090c10; }
            QTabWidget::pane { border: 1px solid #2d3745; border-radius: 8px; background: #121821; }
            QTabBar::tab { background: #1a202a; color: #8f9cac; padding: 9px 18px; margin-right: 2px; border-top-left-radius: 7px; border-top-right-radius: 7px; }
            QTabBar::tab:selected { background: #26303d; color: #ffffff; }
            QGraphicsView { background: #0b0f15; border: none; }
            QProgressBar { background: #0e1218; border: 1px solid #303b49; border-radius: 6px; text-align: center; min-height: 18px; }
            QProgressBar::chunk { background: #e56b2f; border-radius: 5px; }
            QScrollBar:vertical { background: transparent; width: 10px; }
            QScrollBar::handle:vertical { background: #374354; border-radius: 5px; min-height: 30px; }
            QSplitter::handle { background: #202936; width: 2px; }
            """
        )

    def populate_ports(self) -> None:
        current = self.port_combo.currentData()
        self.port_combo.clear()
        if self.demo_mode:
            self.port_combo.addItem("Demo controller (no hardware)", "__demo__")
        for port in sorted(QSerialPortInfo.availablePorts(), key=lambda item: item.portName()):
            description = port.description() or "Serial device"
            self.port_combo.addItem(f"{port.portName()} — {description}", port.portName())
        if current is not None:
            index = self.port_combo.findData(current)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        if self.port_combo.count() == 0:
            self.port_combo.addItem("No serial ports found", None)
        self._update_controls()

    def toggle_connection(self) -> None:
        if self.connected or self.connecting:
            self.disconnect_serial()
            return
        if self.port_combo.currentData() == "__demo__":
            self._connect_demo()
            return
        self.connect_serial()

    def connect_serial(self) -> None:
        port_name = self.port_combo.currentData()
        if not port_name:
            QMessageBox.warning(self, "Connection", "Select a serial port first.")
            return

        self.serial_port.setPortName(port_name)
        self.serial_port.setBaudRate(115_200)
        self.serial_port.setDataBits(QSerialPort.DataBits.Data8)
        self.serial_port.setParity(QSerialPort.Parity.NoParity)
        self.serial_port.setStopBits(QSerialPort.StopBits.OneStop)
        self.serial_port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)

        if not self.serial_port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
            QMessageBox.critical(self, "Connection failed", self.serial_port.errorString())
            return

        self.connecting = True
        self.line_buffer.clear()
        self._set_status("Detecting", "Detecting GRBL controller…")
        self._log("INFO", f"Opened {port_name} at 115200 baud", "#8fc7ff")
        self.serial_port.write(b"\r\n\x18")
        QTimer.singleShot(1_200, self.request_status)
        self.detection_timer.start(3_000)
        self._update_controls()

    def _connect_demo(self) -> None:
        self.connected = True
        self.connecting = False
        self._log("INFO", "Demo controller connected", "#8fc7ff")
        self._apply_status(GrblStatus(raw="", state="Idle", work_position=(0.0, 0.0, 0.0)))
        self.status_timer.start()
        self._set_connected(True)

    def disconnect_serial(self) -> None:
        if self.streamer.is_active:
            self.streamer.cancel()
        self.job_timer.stop()
        self.status_timer.stop()
        self.detection_timer.stop()
        if self.serial_port.isOpen():
            self.serial_port.write(b"!\x18")
            self.serial_port.close()
        self.connected = False
        self.connecting = False
        self.status_report = GrblStatus(raw="", state="Disconnected")
        self._set_status("Disconnected", "Machine state: Disconnected")
        self._set_connected(False)
        self._log("INFO", "Controller disconnected", "#8fc7ff")

    def _read_serial_data(self) -> None:
        chunk = bytes(self.serial_port.readAll())
        for line in self.line_buffer.feed(chunk):
            self._handle_grbl_line(line)

    def _handle_grbl_line(self, line: str) -> None:
        report = parse_status_report(line)
        color = "#74dfaa" if line.lower() == "ok" else "#d7e0eb"
        if line.lower().startswith(("error", "alarm")):
            color = "#ff8993"
        elif report is not None:
            color = "#72c7ff"
        self._log("RX", line, color)

        if self.connecting and ("grbl" in line.lower() or report is not None):
            self._complete_connection()

        if report is not None:
            self._apply_status(report)
            return

        normalized = line.lower()
        if normalized == "ok" and self.streamer.in_flight is not None:
            self.streamer.acknowledge()
            self._update_job_progress()
            if self.streamer.state == StreamState.COMPLETED:
                self._complete_job()
            elif self.streamer.state == StreamState.RUNNING:
                self._send_next_job_line()
        elif normalized.startswith(("error", "alarm")) and self.streamer.is_active:
            self.streamer.fail(line)
            self.send_realtime(b"!")
            self.job_timer.stop()
            self._update_controls()
            QMessageBox.critical(self, "Job stopped", f"GRBL reported: {line}")

    def _complete_connection(self) -> None:
        if self.connected:
            return
        self.connecting = False
        self.connected = True
        self.detection_timer.stop()
        self.status_timer.start()
        self._set_connected(True)
        self.send_command("$G")
        self.statusBar().showMessage("GRBL controller connected", 4_000)

    def _detection_failed(self) -> None:
        if not self.connecting:
            return
        error = "A serial device opened, but it did not identify itself as GRBL."
        self.disconnect_serial()
        QMessageBox.critical(self, "GRBL not detected", error)

    def _serial_error(self, error: QSerialPort.SerialPortError) -> None:
        if error == QSerialPort.SerialPortError.ResourceError and self.serial_port.isOpen():
            message = self.serial_port.errorString()
            self.disconnect_serial()
            QMessageBox.critical(self, "Serial connection lost", message)

    def request_status(self) -> None:
        if self.demo_mode and self.connected:
            state = self.status_report.state if self.status_report.state != "Disconnected" else "Idle"
            self._emit_demo_status(state)
        elif self.serial_port.isOpen():
            self.serial_port.write(b"?")

    def send_realtime(self, command: bytes) -> None:
        if not (self.connected or self.connecting):
            return
        self._log("TX", repr(command), "#f7d477")
        if self.demo_mode:
            if command == b"!":
                self._emit_demo_status("Hold")
            elif command == b"~":
                self._emit_demo_status("Run" if self.streamer.is_active else "Idle")
            elif command == b"\x18":
                self._emit_demo_status("Idle")
            return
        self.serial_port.write(command)

    def send_command(self, command: str, from_stream: bool = False) -> bool:
        if not self.connected:
            QMessageBox.warning(self, "Not connected", "Connect to a GRBL controller first.")
            return False
        if self.streamer.is_active and not from_stream:
            QMessageBox.warning(self, "Job active", "Pause or abort the current job before sending manual commands.")
            return False
        self._log("TX", command, "#f7d477")
        if self.demo_mode:
            self._simulate_command(command)
            return True
        written = self.serial_port.write(f"{command}\n".encode())
        if written < 0:
            QMessageBox.critical(self, "Send failed", self.serial_port.errorString())
            return False
        return True

    def _simulate_command(self, command: str) -> None:
        if command.startswith("$J="):
            coordinates = {axis: float(value) for axis, value in re.findall(r"([XYZ])([-+]?\d*\.?\d+)", command)}
            x, y, z = self.current_position
            self.current_position = (
                x + coordinates.get("X", 0.0),
                y + coordinates.get("Y", 0.0),
                z + coordinates.get("Z", 0.0),
            )
            self._emit_demo_status("Jog")
            QTimer.singleShot(80, lambda: self._emit_demo_status("Idle"))
        elif command == "$H":
            self.current_position = (0.0, 0.0, 0.0)
        elif command == "$G":
            QTimer.singleShot(10, lambda: self._handle_grbl_line("[GC:G0 G54 G17 G21 G90 G94 M5 M9 T0 F0 S0]"))
        QTimer.singleShot(12, lambda: self._handle_grbl_line("ok"))

    def _emit_demo_status(self, state: str) -> None:
        x, y, z = self.current_position
        self._handle_grbl_line(f"<{state}|WPos:{x:.3f},{y:.3f},{z:.3f}|FS:0,0>")

    def _apply_status(self, report: GrblStatus) -> None:
        self.status_report = report
        if report.work_position is not None:
            self.current_position = report.work_position
            x, y, z = report.work_position
            self.position_label.setText(f"Work position  X {x:.3f}   Y {y:.3f}   Z {z:.3f}")
            self._update_position_marker()
        self.machine_state_label.setText(f"Machine state: {report.state}")
        self._set_status(report.state, self.machine_state_label.text())
        self._update_controls()

    def _set_status(self, state: str, message: str) -> None:
        self.status_chip.setText(state.upper())
        colors = {
            "Idle": ("#173c2e", "#7ce0ad"),
            "Run": ("#15344a", "#77cfff"),
            "Jog": ("#15344a", "#77cfff"),
            "Hold": ("#4b3918", "#ffd67a"),
            "Alarm": ("#4a2026", "#ff929c"),
            "Detecting": ("#3d3420", "#f0ce7a"),
        }
        background, foreground = colors.get(state, ("#2b323d", "#a8b3c2"))
        self.status_chip.setStyleSheet(
            f"background: {background}; color: {foreground}; border: 1px solid {foreground}; "
            "border-radius: 12px; padding: 5px 12px; font-weight: 700;"
        )
        self.statusBar().showMessage(message)

    def _set_connected(self, connected: bool) -> None:
        self.connect_button.setText("Disconnect" if connected else "Connect at 115200 baud")
        self._update_controls()

    def _update_controls(self) -> None:
        busy = self.streamer.is_active
        jogging_allowed = self.connected and not busy and self.status_report.state in {"Idle", "Jog"}
        for control in getattr(self, "motion_controls", []):
            control.setEnabled(jogging_allowed)

        has_port = self.port_combo.currentData() is not None
        self.connect_button.setEnabled((has_port and not busy) or self.connected or self.connecting)
        self.port_combo.setEnabled(not self.connected and not self.connecting)
        self.refresh_button.setEnabled(not self.connected and not self.connecting)
        self.start_button.setEnabled(self.connected and not busy and bool(self.gcode_editor.toPlainText().strip()))
        self.pause_button.setEnabled(busy)
        self.abort_button.setEnabled(busy)
        self.emergency_button.setEnabled(self.connected)
        self.gcode_editor.setReadOnly(busy)
        self.image_button.setEnabled(not busy)
        self.gcode_open_button.setEnabled(not busy)
        self.generate_button.setEnabled(self.image_path is not None and not busy)
        self.save_button.setEnabled(bool(self.gcode_editor.toPlainText().strip()) and not busy)
        self.test_button.setEnabled(self.connected and not busy and self.test_enable.isChecked())
        self.test_enable.setEnabled(self.connected and not busy)
        self.pause_button.setText("Resume" if self.streamer.state == StreamState.PAUSED else "Pause")

    def jog(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        axes = " ".join(f"{axis}{value:.3f}" for axis, value in (("X", x), ("Y", y), ("Z", z)) if value != 0)
        self.send_command(f"$J=G91 G21 {axes} F{self.feed_rate.value()}")

    def set_work_zero(self) -> None:
        answer = QMessageBox.question(
            self,
            "Set work zero",
            "Set the current position as X0 Y0 Z0 in the active work coordinate system?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.send_command("G10 L20 P1 X0 Y0 Z0")

    def start_laser_test(self) -> None:
        if self.test_enable.isChecked():
            self.send_command("M4 S10")

    def stop_laser_test(self) -> None:
        if self.connected and not self.streamer.is_active:
            self.send_command("M5")

    def select_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open artwork",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if not filename:
            return
        self.image_path = Path(filename)
        self.selected_file_label.setText(self.image_path.name)
        self._update_controls()

    def generate_gcode(self) -> None:
        if self.image_path is None:
            return
        settings = RasterSettings(
            width_mm=self.width_input.value(),
            height_mm=self.height_input.value(),
            pixels_per_mm=self.resolution_input.value(),
            threshold=self.threshold_input.value(),
            maximum_power=self.power_slider.value(),
            feed_rate=self.feed_rate.value(),
        )
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            commands = image_to_gcode(self.image_path, settings)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "G-code generation failed", str(error))
            return
        finally:
            QApplication.restoreOverrideCursor()
        self.gcode_editor.setPlainText("\n".join(commands))
        self.workspace_tabs.setCurrentWidget(self.gcode_editor)
        self.render_preview()
        self.statusBar().showMessage(f"Generated {len(commands):,} G-code lines", 5_000)

    def open_gcode(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open G-code", "", "G-code (*.gcode *.nc *.tap *.txt);;All files (*)"
        )
        if not filename:
            return
        try:
            content = Path(filename).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(self, "Open failed", str(error))
            return
        self.gcode_editor.setPlainText(content)
        self.selected_file_label.setText(Path(filename).name)
        self.render_preview()

    def save_gcode(self) -> None:
        if not self.gcode_editor.toPlainText().strip():
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save G-code", "job.gcode", "G-code (*.gcode);;Text (*.txt)")
        if not filename:
            return
        try:
            Path(filename).write_text(self.gcode_editor.toPlainText(), encoding="utf-8")
        except OSError as error:
            QMessageBox.critical(self, "Save failed", str(error))

    def render_preview(self) -> None:
        self.preview_scene.clear()
        self.position_marker = None
        segments = parse_motion_segments(self.gcode_editor.toPlainText())
        if not segments:
            self.preview_scene.setSceneRect(-5, -55, 60, 60)
            self._draw_grid(0, 50, 0, 50)
            self.fit_preview()
            return

        x_values = [coordinate for segment in segments for coordinate in (segment.start[0], segment.end[0])]
        y_values = [coordinate for segment in segments for coordinate in (segment.start[1], segment.end[1])]
        minimum_x, maximum_x = min(x_values), max(x_values)
        minimum_y, maximum_y = min(y_values), max(y_values)
        margin = max(2.0, max(maximum_x - minimum_x, maximum_y - minimum_y) * 0.05)
        self.preview_scene.setSceneRect(
            minimum_x - margin,
            -maximum_y - margin,
            maximum_x - minimum_x + margin * 2,
            maximum_y - minimum_y + margin * 2,
        )
        self._draw_grid(minimum_x, maximum_x, minimum_y, maximum_y)

        limit = 20_000
        stride = max(1, math.ceil(len(segments) / limit))
        rapid_pen = QPen(QColor("#536477"), 0)
        rapid_pen.setStyle(Qt.PenStyle.DashLine)
        burn_pen = QPen(QColor("#ff7a3d"), 0)
        for segment in segments[::stride]:
            pen = rapid_pen if segment.rapid or segment.power <= 0 else burn_pen
            self.preview_scene.addLine(
                segment.start[0],
                -segment.start[1],
                segment.end[0],
                -segment.end[1],
                pen,
            )
        self._update_position_marker()
        self.fit_preview()
        self.statusBar().showMessage(
            f"Previewed {len(segments):,} motion segments" + (f" at 1:{stride} detail" if stride > 1 else ""),
            4_000,
        )

    def _draw_grid(self, minimum_x: float, maximum_x: float, minimum_y: float, maximum_y: float) -> None:
        span = max(maximum_x - minimum_x, maximum_y - minimum_y, 10)
        step = 1 if span <= 25 else 5 if span <= 100 else 10
        grid_pen = QPen(QColor("#1e2936"), 0)
        start_x = math.floor(minimum_x / step) * step
        end_x = math.ceil(maximum_x / step) * step
        start_y = math.floor(minimum_y / step) * step
        end_y = math.ceil(maximum_y / step) * step
        x_value = start_x
        while x_value <= end_x:
            self.preview_scene.addLine(x_value, -start_y, x_value, -end_y, grid_pen)
            x_value += step
        y_value = start_y
        while y_value <= end_y:
            self.preview_scene.addLine(start_x, -y_value, end_x, -y_value, grid_pen)
            y_value += step
        origin_pen = QPen(QColor("#75a7d8"), 0)
        self.preview_scene.addLine(start_x, 0, end_x, 0, origin_pen)
        self.preview_scene.addLine(0, -start_y, 0, -end_y, origin_pen)

    def _update_position_marker(self) -> None:
        if self.position_marker is not None and self.position_marker.scene() is self.preview_scene:
            self.preview_scene.removeItem(self.position_marker)
        width = max(0.8, self.preview_scene.sceneRect().width() / 150)
        x, y, _ = self.current_position
        self.position_marker = self.preview_scene.addEllipse(
            x - width / 2,
            -y - width / 2,
            width,
            width,
            QPen(QColor("#ffffff"), 0),
            QColor("#6ce5a5"),
        )
        self.position_marker.setZValue(10)

    def fit_preview(self) -> None:
        if not self.preview_scene.sceneRect().isEmpty():
            self.preview_view.fitInView(self.preview_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def start_job(self) -> None:
        try:
            total = self.streamer.load(self.gcode_editor.toPlainText())
        except RuntimeError as error:
            QMessageBox.warning(self, "Job", str(error))
            return
        if total == 0:
            QMessageBox.warning(self, "Job", "No executable G-code was found.")
            return
        answer = QMessageBox.question(
            self,
            "Start laser job",
            f"Stream {total:,} commands to the connected controller?\n\n"
            "Confirm ventilation, eye protection, focus, and a clear machine area before continuing.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.streamer.start()
        self.progress_bar.setValue(0)
        self.job_timer.start()
        self._update_controls()
        self.workspace_tabs.setCurrentWidget(self.console)
        self._log("JOB", f"Started {total:,}-line job", "#f0a46c")
        self._send_next_job_line()

    def _send_next_job_line(self) -> None:
        command = self.streamer.next_command()
        if command is None:
            return
        if not self.send_command(command.text, from_stream=True):
            self.streamer.fail("Serial write failed.")
            self.job_timer.stop()
            self._update_controls()

    def toggle_pause(self) -> None:
        if self.streamer.state == StreamState.RUNNING:
            self.send_realtime(b"!")
            self.streamer.pause()
            self._log("JOB", "Feed hold requested", "#f0ce7a")
        elif self.streamer.state == StreamState.PAUSED:
            self.send_realtime(b"~")
            self.streamer.resume()
            self._log("JOB", "Cycle resume requested", "#74dfaa")
            if self.streamer.in_flight is None:
                self._send_next_job_line()
        self._update_controls()

    def abort_job(self, checked: bool = False, confirm: bool = True) -> None:
        del checked
        if not self.connected:
            return
        if confirm:
            answer = QMessageBox.question(
                self,
                "Abort job",
                "Immediately issue feed hold and a GRBL soft reset?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.send_realtime(b"!")
        self.send_realtime(b"\x18")
        self.streamer.cancel()
        self.job_timer.stop()
        self.progress_bar.setValue(0)
        self.job_detail_label.setText("Job aborted")
        self._log("JOB", "Job aborted with feed hold and soft reset", "#ff8993")
        self._update_controls()

    def _update_job_progress(self) -> None:
        progress = round(self.streamer.progress * 100)
        self.progress_bar.setValue(progress)
        remaining = self.streamer.estimated_remaining
        remaining_text = "calculating" if remaining is None else self._format_duration(remaining)
        self.job_detail_label.setText(
            f"{self.streamer.acknowledged:,} / {self.streamer.total:,} commands · {remaining_text} remaining"
        )

    def _complete_job(self) -> None:
        self.job_timer.stop()
        self.progress_bar.setValue(100)
        duration = self._format_duration(self.streamer.elapsed)
        self.job_detail_label.setText(f"Completed in {duration}")
        self._log("JOB", f"Completed in {duration}", "#74dfaa")
        self._update_controls()
        QMessageBox.information(self, "Job complete", f"All G-code commands were acknowledged in {duration}.")

    @staticmethod
    def _format_duration(seconds: float) -> str:
        total_seconds = max(0, round(seconds))
        hours, remainder = divmod(total_seconds, 3_600)
        minutes, seconds_value = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds_value:02d}"

    def _log(self, prefix: str, message: str, color: str) -> None:
        self.console.append(f'<span style="color:{color}"><b>{html.escape(prefix)}</b>  {html.escape(message)}</span>')
        scrollbar = self.console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _load_demo_job(self) -> None:
        sample = """; Demo: 30 mm calibration frame
G21
G90
M4 S0
F1000
G0 X0 Y0
G1 X30 Y0 S120
G1 X30 Y20 S120
G1 X0 Y20 S120
G1 X0 Y0 S120
M5
G0 X0 Y0
"""
        self.gcode_editor.setPlainText(sample)
        self.render_preview()

    def show_safety(self) -> None:
        QMessageBox.warning(
            self,
            "Laser safety",
            "Never operate a laser unattended. Use wavelength-rated eye protection, effective ventilation, "
            "a fire-resistant enclosure, and a physical emergency stop. Test with minimum power first. "
            "Software controls are not a substitute for hardware safety systems.",
        )

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About LaserGRBL for macOS",
            f"LaserGRBL for macOS {__version__}\n\n"
            "An open-source desktop controller for GRBL-compatible laser engravers and CNC machines.",
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self.streamer.is_active:
            answer = QMessageBox.question(self, "Active job", "Abort the active job and quit?")
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.abort_job(confirm=False)
        if self.connected or self.connecting:
            self.disconnect_serial()
        event.accept()


def run(demo_mode: bool = False) -> int:
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("LaserGRBL for macOS")
    application.setApplicationVersion(__version__)
    application.setOrganizationName("LaserGRBL MacOS Controller")
    window = LaserControllerWindow(demo_mode=demo_mode)
    window.show()
    return application.exec()
