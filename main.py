# This Python file uses the following encoding: utf-8
import sys
import os


from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QGridLayout, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QFile, Qt, QSize, QObject, QThread, pyqtSignal


class SPMController(QWidget):
    def __init__(self):
        super(SPMController, self).__init__()
        self.load_ui()
        self.initialize_formats();

    def load_ui(self):
        path = os.path.join(os.path.dirname(__file__), "form.ui")
        uic.loadUi(path, self)

    def initialize_formats(self):
        self.widget_display_piezo_limit.setStyleSheet("background-color: black;")
        self.widget_display_scan_window_ch1.setStyleSheet("background-color: grey;")
        self.widget_display_scan_window_ch2.setStyleSheet("background-color: grey;")
        self.widget_linescan_ch1.setBackground("w")
        self.widget_linescan_ch2.setBackground("w")

if __name__ == "__main__":
    app = QApplication([])
    widget = SPMController()
    widget.show()
    sys.exit(app.exec_())
