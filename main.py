# This Python file uses the following encoding: utf-8
import sys
import os

from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QGridLayout, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QFile, Qt, QSize, QObject, QThread, pyqtSignal
import numpy as np



class SPMController(QWidget):
    def __init__(self):
        super(SPMController, self).__init__()
        self.error_lock = False
        self.data_store = [] # 5 x n, (XX, YY, array1, array2) x n)
        self.data_choose = -1
        self.channel_choose = 1 #1 or 2
        self.load_ui()
        self.initialize_formats();
        self.determine_scan_window()
        self.connect_all()
        self.x_curr = 0
        self.y_curr = 0
        #check_minmaxrotation_valid()

    def load_ui(self):
        path = os.path.join(os.path.dirname(__file__), "form.ui")
        uic.loadUi(path, self)

    def initialize_formats(self):
        self.widget_linescan_ch1.setBackground("w")
        self.widget_linescan_ch2.setBackground("w")
        self.widget_display_piezo_limit = MatplotlibWidget()
        self.verticalLayout_display_piezo_limit.addWidget(self.widget_display_piezo_limit)
        self.widget_display_scan_window_ch1 = MatplotlibWidget()
        self.verticalLayout_display_scan_window_ch1.addWidget(self.widget_display_scan_window_ch1)
        self.widget_display_scan_window_ch2 = MatplotlibWidget()
        self.verticalLayout_display_scan_window_ch2.addWidget(self.widget_display_scan_window_ch2)

    def plot_scan_range(self, widget, xlim_min, xlim_max, ylim_min, ylim_max):
        widget.getFigure().clear()
        subplot = widget.getFigure().subplots()
        subplot.set_aspect(1)
        subplot.set_facecolor('black')
        subplot.set_xlim(xlim_min, xlim_max)
        subplot.set_ylim(ylim_min, ylim_max)
        subplot.invert_xaxis()
        subplot.invert_yaxis()
        subplot.plot([0, self.piezo_limit_x], [0, 0], '--', c = 'white')
        subplot.plot([self.piezo_limit_x, self.piezo_limit_x], [0, self.piezo_limit_y], '--', c = 'white')
        subplot.plot([self.piezo_limit_x, 0], [self.piezo_limit_y, self.piezo_limit_y], '--', c = 'white')
        subplot.plot([0, 0], [self.piezo_limit_y, 0], '--', c = 'white')
        if (len(self.data_store) > 0):
            subplot.pcolormesh(self.data_store[self.data_choose][0], self.data_store[self.data_choose][1], self.data_store[self.data_choose][self.channel_choose + 1], cmap = "afmhot")

        exceeds_limit = False
        if (widget == self.widget_display_piezo_limit):

            for p in [self.p1, self.p2, self.p3, self.p4]:
                if p[0] > self.piezo_limit_x or p[0] < 0 or p[1] > self.piezo_limit_y or p[1] < 0:
                    exceeds_limit = True
            if exceeds_limit:
                self.error_lock = True
                self.label_error.setText("🚫 Error: Scan window exceeds piezo limit")
            else:
                self.error_lock = True
                self.label_error.setText("")
        subplot.plot([self.p1[0], self.p2[0]], [self.p1[1], self.p2[1]], '--', linewidth=3,
                     c='red' if exceeds_limit else 'orange')
        subplot.plot([self.p2[0], self.p3[0]], [self.p2[1], self.p3[1]], '--', linewidth=3,
                     c='red' if exceeds_limit else 'green')
        subplot.plot([self.p3[0], self.p4[0]], [self.p3[1], self.p4[1]], '--', linewidth=3,
                     c='red' if exceeds_limit else 'green')
        subplot.plot([self.p4[0], self.p1[0]], [self.p4[1], self.p1[1]], '--', linewidth=3,
                     c='red' if exceeds_limit else 'green')
        subplot.plot([self.p1[0]], [self.p1[1]], '.', markersize=20, c='red')
        widget.draw()

    def determine_scan_window(self):
        self.piezo_limit_x = self.doubleSpinBox_piezo_limit_x.value()
        self.piezo_limit_y = self.doubleSpinBox_piezo_limit_y.value()
        self.xmin_input = self.doubleSpinBox_x_min.value()
        self.xmax_input = self.doubleSpinBox_x_max.value()
        self.ymin_input = self.doubleSpinBox_y_min.value()
        self.ymax_input = self.doubleSpinBox_y_max.value()
        self.xpixels = self.spinBox_x_pixels.value()
        self.ypixels = self.spinBox_y_pixels.value()
        self.rotation_degree = self.doubleSpinBox_rotation.value()
        self.rotation = self.rotation_degree / 180 * np.pi
        center = np.array([[(self.xmin_input + self.xmax_input) / 2,
                            (self.ymin_input + self.ymax_input) / 2]]).T
        p1_input = np.array([self.xmin_input, self.ymin_input])
        p2_input = np.array([self.xmax_input, self.ymin_input])
        p3_input = np.array([self.xmax_input, self.ymax_input])
        p4_input = np.array([self.xmin_input, self.ymax_input])
        rotate_matrix = np.array([[np.cos(self.rotation), -np.sin(self.rotation)],
                                  [np.sin(self.rotation), np.cos(self.rotation)]])
        self.p1 = self.rotate_coord(p1_input, center, rotate_matrix)#np.round(np.reshape(np.matmul(rotate_matrix, (p1_input - center)) + center, (-1, 2))[0], 6)
        self.p2 = self.rotate_coord(p2_input, center, rotate_matrix)#np.round(np.reshape(np.matmul(rotate_matrix, (p2_input - center)) + center, (-1, 2))[0], 6)
        self.p3 = self.rotate_coord(p3_input, center, rotate_matrix)#np.round(np.reshape(np.matmul(rotate_matrix, (p3_input - center)) + center, (-1, 2))[0], 6)
        self.p4 = self.rotate_coord(p4_input, center, rotate_matrix)#np.round(np.reshape(np.matmul(rotate_matrix, (p4_input - center)) + center, (-1, 2))[0], 6)

        self.X_raw = np.linspace(0, self.xmax_input - self.xmin_input, self.xpixels)
        self.Y_raw = np.linspace(0, self.ymax_input - self.ymin_input, self.ypixels)
        XX_input, YY_input = np.meshgrid(self.X_raw + self.xmin_input, self.Y_raw + self.ymin_input)
        xx_yy = np.array([np.array([xx, yy]) for xx, yy in zip(XX_input.reshape((1, -1)), YY_input.reshape((1, -1)))])
        xx_yy_rot = self.rotate_coord(xx_yy, center, rotate_matrix)
        self.XX = xx_yy_rot[0, :].reshape(XX_input.shape)
        self.YY = xx_yy_rot[1, :].reshape(YY_input.shape)

        xlim_min = np.min([self.p1[0], self.p2[0], self.p3[0], self.p4[0]])
        xlim_max = np.max([self.p1[0], self.p2[0], self.p3[0], self.p4[0]])
        ylim_min = np.min([self.p1[1], self.p2[1], self.p3[1], self.p4[1]])
        ylim_max = np.max([self.p1[1], self.p2[1], self.p3[1], self.p4[1]])
        self.plot_scan_range(self.widget_display_piezo_limit, xlim_min=0, xlim_max=self.piezo_limit_x, ylim_min=0,
                             ylim_max=self.piezo_limit_y)
        self.plot_scan_range(self.widget_display_scan_window_ch1, xlim_min = xlim_min, xlim_max = xlim_max, ylim_min = ylim_min,
                             ylim_max = ylim_max)
        self.plot_scan_range(self.widget_display_scan_window_ch2, xlim_min=xlim_min, xlim_max=xlim_max, ylim_min=ylim_min,
                             ylim_max=ylim_max)

    def rotate_coord(self, p, center, rotate_matrix, accuracy_digits = 6):
        p = np.reshape(p, (2, -1))
        if p.shape[1] == 1:
            return np.round(np.reshape(np.matmul(rotate_matrix, (p - center)) + center, (-1, 2))[0], accuracy_digits)
        else:
            return np.round(np.reshape(np.matmul(rotate_matrix, (p - center)) + center, (2, -1)), accuracy_digits)


    def connect_all(self):
        '''
        keyboardTracking of all edges has been set to False in form.ui. Thus valueChanged is only triggered after Enter.
        '''
        self.doubleSpinBox_piezo_limit_x.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_piezo_limit_y.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_x_min.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_x_max.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_y_min.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_y_max.valueChanged.connect(self.determine_scan_window)
        self.spinBox_x_pixels.valueChanged.connect(self.determine_scan_window)
        self.spinBox_y_pixels.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_rotation.valueChanged.connect(self.determine_scan_window)

    def scan(self):



class

if __name__ == "__main__":
    app = QApplication([])
    widget = SPMController()
    widget.show()
    sys.exit(app.exec_())
