# This Python file uses the following encoding: utf-8
import sys
import os


from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QGridLayout, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QFile, Qt, QSize, QObject, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
import numpy as np



class SPMController(QWidget):
    def __init__(self):
        super(SPMController, self).__init__()
        self.load_ui()
        self.initialize_formats();
        self.plot_scan_range();
        self.x_curr = 0
        self.y_curr = 0

    def load_ui(self):
        path = os.path.join(os.path.dirname(__file__), "form.ui")
        uic.loadUi(path, self)

    def initialize_formats(self):
        self.widget_display_piezo_limit.setStyleSheet("background-color: grey;")
        self.widget_display_scan_window_ch1.setStyleSheet("background-color: black;")
        self.widget_display_scan_window_ch2.setStyleSheet("background-color: black;")
        self.widget_linescan_ch1.setBackground("w")
        self.widget_linescan_ch2.setBackground("w")

    def plot_scan_range(self):
        tmp =  QWidget()
        tmp.canvas = FigureCanvas(Figure())
        self.verticalLayout_display_piezo_limit.addWidget(tmp.canvas)
        tmp.canvas.axes = tmp.canvas.figure.add_subplot(111)
        tmp.canvas.axes.set_aspect(1)
        X = np.linspace(-10, 10, 100)
        Y = np.linspace(-10, 10, 100)
        XX, YY = np.meshgrid(X, Y)
        array = np.exp(-(XX**2+YY**2))
        tmp.canvas.axes.pcolormesh(XX, YY, array, shading='auto')
        tmp.canvas.figure.tight_layout(pad=4)

if __name__ == "__main__":
    app = QApplication([])
    widget = SPMController()
    widget.show()
    sys.exit(app.exec_())
