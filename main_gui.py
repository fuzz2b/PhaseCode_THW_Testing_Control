"""
+automation menus populated by config.py.
"""

import sys
import os
import subprocess

from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon

from config import DROPDOWN_GROUPS
from relay_control import set_relays
from shutdown import run

#  Worker thread
class ScriptRunner(QThread):
    """
    LOREM IPSUM
    """
    output_ready = pyqtSignal(str)
    finished_ok  = pyqtSignal(str)
    finished_err = pyqtSignal(str)

    def __init__(self, script_command: str):
        super().__init__()
        self.script_command = script_command

    def run(self):
        try:
            import shlex
 
            cmd_args = shlex.split(self.script_command) 

            result = subprocess.run(
                [sys.executable] + cmd_args,
                capture_output=True,
                text=True,
                # removed timeout
            )

            output = result.stdout.strip()
            errors = result.stderr.strip()

            if output:
                self.output_ready.emit(output)
            if errors:
                self.output_ready.emit(f"[stderr]\n{errors}")

        except Exception as exc:
            self.finished_err.emit(f"✗ Error: {exc}")

class LauncherWindow(QWidget):
    """
    WRITE SOMETHING
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher")
        self.setMinimumSize(640, 520)
        self._runners: list[ScriptRunner] = []   # keep references alive
        self._build_ui()
        self._apply_styles()

    # UI construction
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(24, 24, 24, 24)

        rootDir = os.path.dirname(__file__) + '/../'
        self.setWindowIcon(QIcon(rootDir + "/data/phase_icon.ico")) # currentley not working

        title = QLabel("Launcher")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        root.addWidget(self._divider())
        # Dropdowns List
        self.combos: list[QComboBox] = []

        # Wire Selection 
        wire_row = QHBoxLayout()
        wire_row.setSpacing(12)

        wire_label = QLabel("Wire Selection")
        wire_label.setFixedWidth(180)
        wire_label.setObjectName("drop_label")
        wire_row.addWidget(wire_label)

        self.wire_combo = QComboBox()
        self.wire_combo.setObjectName("combo")
        self.wire_combo.addItem("— select —", userData=None)
        
        wire_options = [
            ("Wire 1 (Pins 1 & 2)", (1, 2)),
            ("Wire 2 (Pins 2 & 3)", (2, 3)),
            ("Wire 3 (Pins 3 & 4)", (3, 4)),
            ("Wire 4 (Pins 4 & 5)", (4, 5)),
            ("Wire 5 (Pins 5 & 6)", (5, 6))
        ]
        for name, pins in wire_options:
            self.wire_combo.addItem(name, userData={"type": "wire", "pins": pins})
            
        wire_row.addWidget(self.wire_combo, stretch=1)
        root.addLayout(wire_row)

        # DROPDOWNS 2 & 3
        for group in DROPDOWN_GROUPS:
            row = QHBoxLayout()
            row.setSpacing(12)

            label = QLabel(group["label"])
            label.setFixedWidth(180)
            label.setObjectName("drop_label")
            row.addWidget(label)

            combo = QComboBox()
            combo.setObjectName("combo")
            combo.addItem("— select —", userData=None) # placeholder
            
            for item in group["tools"]:
                combo.addItem(item["name"], userData={"type": "tools", "path": item["path"]})
            
            row.addWidget(combo, stretch=1)
            self.combos.append(combo)
            root.addLayout(row)

        # Buttons
        root.addWidget(self._divider())

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_execute = QPushButton("▶   Execute")
        self.btn_execute.setObjectName("btn_execute")
        self.btn_execute.clicked.connect(self._on_execute)

        self.btn_shutdown = QPushButton("⏻    Shutdown")
        self.btn_shutdown.setObjectName("btn_shutdown")
        self.btn_shutdown.clicked.connect(self._on_shutdown)

        btn_row.addWidget(self.btn_execute, stretch=2)
        btn_row.addWidget(self.btn_shutdown, stretch=1)
        root.addLayout(btn_row)

        # Output Log
        self.log = QTextEdit()
        self.log.setObjectName("log")
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Output will appear here…")
        root.addWidget(self.log, stretch=1)

    def _on_execute(self):
        selected_scripts = []
        wire_pins = None
        
        # Hardware Wire Selection
        wire_data = self.wire_combo.currentData()
        if wire_data and wire_data["type"] == "wire":
            wire_pins = wire_data["pins"]

        # Power and Joulescope controls (can add more technicall  - maybe plotting)
        for i, combo in enumerate(self.combos):
            data = combo.currentData()
            if data and data["type"] == "tools":
                selected_scripts.append((DROPDOWN_GROUPS[i]["label"], data["path"]))
                print(selected_scripts)

        self.btn_execute.setEnabled(False)
        self.btn_execute.setText("Running…")

        # STEP A: Execute the relay firmware adjustments first
        if wire_pins:
            pin1, pin2 = wire_pins
            self._log_info(f"Setting relay configurations for Pin {pin1} and Pin {pin2}...")
            try:
                set_relays(pin1, pin2)
                self._log_ok(f"✓ Relay board configured successfully for pins ({pin1}, {pin2})")
            except Exception as e:
                self._log_err(f"✗ Relay Error: {e}")

        # STEP B: Kick off the secondary automation background processes
        if selected_scripts:
            # Look for a Joulescope tool path in our selection pool
            js_script_path = None
            for label, path in selected_scripts:
                if "Joulescope Tests" in label:
                    js_script_path = path

            self._log_info(f"Launching {len(selected_scripts)} process script(s)…")

            for label, path in selected_scripts:
                if "Power Supply Configurations" in label and js_script_path:
                    self._log_info(f"  → [{label}] {Path(path).name} paired with {Path(js_script_path).name}")
                    
                    runner = ScriptRunner(f'"{path}" --js-tool "{js_script_path}"')
                    runner.output_ready.connect(self._log_plain)
                    runner.finished_ok.connect(self._log_ok)
                    runner.finished_err.connect(self._log_err)
                    self._runners.append(runner)
                    runner.start()

    # Shutdown

    def _on_shutdown(self):
        reply = QMessageBox.question(
            self, "Confirm Shutdown",
            "Close the launcher?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            run()
            QApplication.quit()

    # Log helpers 
    def _log_plain(self, msg: str):
        self.log.append(msg)

    def _log_info(self, msg: str):
        self.log.append(f'<span style="color:#6C99BB;">{msg}</span>')

    def _log_ok(self, msg: str):
        self.log.append(f'<span style="color:#7DAF9C;font-weight:bold;">{msg}</span>')

    def _log_err(self, msg: str):
        self.log.append(f'<span style="color:#CC4232;font-weight:bold;">{msg}</span>')

    def _log_warn(self, msg: str):
        self.log.append(f'<span style="color:#EFAC32;">{msg}</span>')

    # Misc helpers 
    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("divider")
        return line

    # Stylesheet - got claude to match it to my VScode theme
    def _apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #372725;
                color: #E6E1C4;
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
            }

            #title {
                font-size: 22px;
                font-weight: 700;
                letter-spacing: 1px;
                color: #EFAC32;
                padding: 4px 0 8px 0;
            }

            #divider {
                color: #5B413D;
                background-color: #5B413D;
                max-height: 1px;
                border: none;
            }

            #drop_label {
                font-size: 13px;
                font-weight: 600;
                color: #C699BB;
                padding-top: 4px;
            }
                           
            QComboBox {
                combobox-popup: 0;  /* Forces PyQt to use a clean style wrapper rather than OS native menus */
            }
            QComboBox#combo {
                background-color: #4A332F;
                border: 1px solid #6B4E32;
                border-radius: 6px;
                padding: 6px 12px;
                color: #E6E1C4;
                min-height: 28px;
            }
                           
            QComboBox#combo:hover  { border-color: #EFAC32; }
            QComboBox#combo::drop-down { border: none; width: 24px; }
            QComboBox#combo QAbstractItemView {
                background-color: #4A332F;
                border: 1px solid #6B4E32;
                selection-background-color: #A40042;
            }

            QPushButton#btn_execute {
                background-color: #EF5D32;
                color: #372725;
                border: none;
                border-radius: 7px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton#btn_execute:hover   { background-color: #EFAC32; }
            QPushButton#btn_execute:pressed { background-color: #D9D762; }
            QPushButton#btn_execute:disabled {
                background-color: #5B413D;
                color: #8A9A95;
            }

            QPushButton#btn_shutdown {
                background-color: #420E09;
                color: #CC4232;
                border: 1px solid #CC4232;
                border-radius: 7px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton#btn_shutdown:hover   { background-color: #5B1A12; }
            QPushButton#btn_shutdown:pressed { background-color: #6E241A; }

            QTextEdit#log {
                background-color: #281C1C;
                border: 1px solid #5B413D;
                border-radius: 7px;
                padding: 10px;
                font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                color: #E6E1C4;
            }
        """)

# Entry point 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())
