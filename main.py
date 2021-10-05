"""
Created by Xuejian Ma at 10/2/2021.
All rights reserved.
"""

# This Python file uses the following encoding: utf-8
import sys
import os

from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget
from pyqtgraph import mkPen
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QGridLayout, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QFile, Qt, QSize, QObject, QThread, pyqtSignal
from scan import Scan, MoveToTarget, Map
import numpy as np


class SPMController(QWidget):
    update_voltage_signal = pyqtSignal()

    def __init__(self):
        super(SPMController, self).__init__()
        self.error_lock = False
        self.data_store = []  # 5 x n, (XX, YY, array1, array2) x n)
        self.data_choose = -1
        self.channel_choose = 1  # 1 or 2
        self.scan_on_boolean = False
        self.map_on_boolean = False
        self.map_trace = {'XX': [], 'YY': [], 'ch1': [], 'ch2': []}
        self.map_retrace = {'XX': [], 'YY': [], 'ch1': [], 'ch2': []}
        self.load_ui()
        self.initialize_formats()
        self.determine_scan_window()
        self.connect_all()
        self.curr_coords = [0, 0]
        self.on_off_spinbox_list = [self.doubleSpinBox_x_min, self.doubleSpinBox_x_max, self.doubleSpinBox_y_min,
                                    self.doubleSpinBox_y_max, self.spinBox_x_pixels, self.spinBox_y_pixels,
                                    self.doubleSpinBox_rotation,#self.doubleSpinBox_frequency,
                                    self.doubleSpinBox_piezo_limit_x, self.doubleSpinBox_piezo_limit_y,
                                    self.lineEdit_filename_trace_ch1, self.lineEdit_filename_trace_ch2,
                                    self.lineEdit_filename_retrace_ch1, self.lineEdit_filename_retrace_ch2,
                                    self.lineEdit_directory]
        self.on_off_button_list = [self.pushButton_scan, self.pushButton_image, self.pushButton_goto0,
                                   self.pushButton_goto, self.doubleSpinBox_goto_x, self.doubleSpinBox_goto_y]
        self.line_trace = {'X': [], 'ch1': [], 'ch2': []}
        self.line_retrace = {'X': [], 'ch1': [], 'ch2': []}


        # check_minmaxrotation_valid()

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

    def plot_scan_range(self, widget, xlim_min, xlim_max, ylim_min, ylim_max, colorbar_manual = False):
        widget.getFigure().clear()
        subplot = widget.getFigure().subplots()
        subplot.set_aspect(1)
        subplot.set_facecolor('black')
        subplot.set_xlim(xlim_min, xlim_max)
        subplot.set_ylim(ylim_min, ylim_max)
        subplot.invert_xaxis()
        subplot.invert_yaxis()
        subplot.plot([0, self.piezo_limit_x], [0, 0], '--', c='white')
        subplot.plot([self.piezo_limit_x, self.piezo_limit_x], [0, self.piezo_limit_y], '--', c='white')
        subplot.plot([self.piezo_limit_x, 0], [self.piezo_limit_y, self.piezo_limit_y], '--', c='white')
        subplot.plot([0, 0], [self.piezo_limit_y, 0], '--', c='white')
        if (len(self.data_store) > 0):
            subplot.pcolormesh(self.data_store[self.data_choose][0], self.data_store[self.data_choose][1],
                               self.data_store[self.data_choose][self.channel_choose + 1], cmap="afmhot")

        exceeds_limit = False

        for p in [self.p1, self.p2, self.p3, self.p4]:
            if p[0] > self.piezo_limit_x or p[0] < 0 or p[1] > self.piezo_limit_y or p[1] < 0:
                exceeds_limit = True
        if widget == self.widget_display_piezo_limit:
            if exceeds_limit:
                self.error_lock = True
                self.label_error.setText("🚫 Error: Scan window exceeds piezo limit")
            else:
                self.error_lock = True
                self.label_error.setText("")
        if len(self.map_trace['XX']) != 0:
            if widget == self.widget_display_piezo_limit:
                if self.radioButton_main_ch1.isChecked():
                    if self.radioButton_main_trace.isChecked():
                        if not colorbar_manual:
                            subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch1'],
                                               cmap='afmhot')
                        else:
                            subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch1'],
                                               cmap='afmhot', vmin = self.doubleSpinBox_colorbar_manual_min_main.value(), vmax = self.doubleSpinBox_colorbar_manual_max_main.value())
                    else:
                        if not colorbar_manual:
                            subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'],
                                                cmap='afmhot')
                        else:
                            subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'],
                                               cmap='afmhot', vmin = self.doubleSpinBox_colorbar_manual_min_main.value(), vmax = self.doubleSpinBox_colorbar_manual_max_main.value())
                else:
                    if self.radioButton_main_trace.isChecked():
                        if not colorbar_manual:
                            subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'],
                                               cmap='afmhot')
                        else:
                            subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'],
                                               cmap='afmhot', vmin = self.doubleSpinBox_colorbar_manual_min_main.value(), vmax = self.doubleSpinBox_colorbar_manual_max_main.value())
                    else:
                        if not colorbar_manual:
                            subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'],
                                                cmap='afmhot')
                        else:
                            subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'],
                                               cmap='afmhot', vmin = self.doubleSpinBox_colorbar_manual_min_main.value(), vmax = self.doubleSpinBox_colorbar_manual_max_main.value())
            elif widget == self.widget_display_scan_window_ch1:
                if self.radioButton_ch1_trace.isChecked():
                    subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch1'], cmap = 'afmhot')
                else:
                    subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'], cmap='afmhot')
            elif widget == self.widget_display_scan_window_ch2:
                if self.radioButton_ch2_trace.isChecked():
                    subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'], cmap = 'afmhot')
                else:
                    subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'], cmap='afmhot')


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
        self.frequency = self.doubleSpinBox_frequency.value()
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
        self.p1 = self.rotate_coord(p1_input, center, rotate_matrix)
        self.p2 = self.rotate_coord(p2_input, center, rotate_matrix)
        self.p3 = self.rotate_coord(p3_input, center, rotate_matrix)
        self.p4 = self.rotate_coord(p4_input, center, rotate_matrix)

        self.X_raw = np.round(np.linspace(0, self.xmax_input - self.xmin_input, self.xpixels), 6)
        self.Y_raw = np.round(np.linspace(0, self.ymax_input - self.ymin_input, self.ypixels), 6)
        XX_input, YY_input = np.meshgrid(self.X_raw + self.xmin_input, self.Y_raw + self.ymin_input)
        xx_yy = np.array([np.array([xx, yy]) for xx, yy in zip(XX_input.reshape((1, -1)), YY_input.reshape((1, -1)))])
        xx_yy_rot = self.rotate_coord(xx_yy, center, rotate_matrix)
        self.XX = xx_yy_rot[0, :].reshape(XX_input.shape)
        self.YY = xx_yy_rot[1, :].reshape(YY_input.shape)
        self.update_graphs()

    def update_graphs(self, single = 'all', colorbar_manual = False):
        xlim_min = np.min([self.p1[0], self.p2[0], self.p3[0], self.p4[0]])
        xlim_max = np.max([self.p1[0], self.p2[0], self.p3[0], self.p4[0]])
        ylim_min = np.min([self.p1[1], self.p2[1], self.p3[1], self.p4[1]])
        ylim_max = np.max([self.p1[1], self.p2[1], self.p3[1], self.p4[1]])
        if single == 'all' or single == 'main':
            self.plot_scan_range(self.widget_display_piezo_limit, xlim_min=0, xlim_max=self.piezo_limit_x, ylim_min=0,
                                 ylim_max=self.piezo_limit_y, colorbar_manual = colorbar_manual)
        if single == 'all' or single == 'ch1':
            self.plot_scan_range(self.widget_display_scan_window_ch1, xlim_min=xlim_min, xlim_max=xlim_max,
                                 ylim_min=ylim_min,
                                 ylim_max=ylim_max, colorbar_manual = colorbar_manual)
        if single == 'all' or single == 'ch2':
            self.plot_scan_range(self.widget_display_scan_window_ch2, xlim_min=xlim_min, xlim_max=xlim_max,
                                 ylim_min=ylim_min,
                                 ylim_max=ylim_max, colorbar_manual = colorbar_manual)

    def rotate_coord(self, p, center, rotate_matrix):
        p = np.reshape(p, (2, -1))
        if p.shape[1] == 1:
            return np.round(np.reshape(np.matmul(rotate_matrix, (p - center)) + center, (-1, 2))[0], 6)
        else:
            return np.round(np.reshape(np.matmul(rotate_matrix, (p - center)) + center, (2, -1)), 6)

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
        self.doubleSpinBox_frequency.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_rotation.valueChanged.connect(self.determine_scan_window)
        self.update_voltage_signal.connect(self.update_voltage)
        self.pushButton_scan.clicked.connect(self.toggle_scan_button)
        self.pushButton_goto0.clicked.connect(lambda: self.goto_position(np.array([0, 0])))
        self.pushButton_goto.clicked.connect(lambda: self.goto_position(np.array([self.doubleSpinBox_goto_x.value(),
                                                                   self.doubleSpinBox_goto_y.value()])))
        self.pushButton_image.clicked.connect(self.toggle_map_button)
        self.buttonGroup.buttonToggled.connect(lambda: self.update_graphs(single = 'main'))
        self.buttonGroup_2.buttonToggled.connect(lambda: self.update_graphs(single = 'main'))
        self.buttonGroup_3.buttonToggled.connect(lambda: self.update_graphs(single = 'ch1'))
        self.buttonGroup_4.buttonToggled.connect(lambda: self.update_graphs(single = 'ch2'))
        self.buttonGroup_5.buttonToggled.connect(self.toggle_colorbar_main)
        self.doubleSpinBox_colorbar_manual_min_main.valueChanged.connect(self.toggle_colorbar_main)
        self.doubleSpinBox_colorbar_manual_max_main.valueChanged.connect(self.toggle_colorbar_main)

    def toggle_colorbar_main(self):
        if self.radioButton_colorbar_manual_main.isChecked():
            self.update_graphs(single='main', colorbar_manual=True)
            self.doubleSpinBox_colorbar_manual_min_main.setDisabled(False)
            self.doubleSpinBox_colorbar_manual_max_main.setDisabled(False)
        else:
            self.update_graphs(single='main', colorbar_manual=False)
            self.doubleSpinBox_colorbar_manual_min_main.setDisabled(True)
            self.doubleSpinBox_colorbar_manual_max_main.setDisabled(True)


    def toggle_scan_button(self):
        if self.scan_on_boolean:
            self.on_off_spinbox_list_turn_on()
            self.pushButton_image.setDisabled(False)
            self.pushButton_scan.setText("Scan")
        else:
            self.pushButton_scan.setText("OFF")
            self.on_off_spinbox_list_turn_off()
            self.pushButton_image.setDisabled(True)
            self.start_scan()
        self.scan_on_boolean = not self.scan_on_boolean

    def toggle_map_button(self):
        if self.map_on_boolean:
            self.on_off_spinbox_list_turn_on()
            self.pushButton_scan.setDisabled(False)
            self.pushButton_image.setText("Image")
        else:
            self.pushButton_image.setText("OFF")
            self.on_off_spinbox_list_turn_off()
            self.pushButton_scan.setDisabled(True)
            self.start_map()
        self.map_on_boolean = not self.map_on_boolean

    def start_scan(self):
        self.thread = QThread()
        self.scan = Scan(self)  # .curr_coords, self.XX, self.YY, self.frequency, self.update_voltage_signal, self.scan_on_boolean_in_list)
        self.scan.moveToThread(self.thread)
        self.thread.started.connect(self.scan.run)
        self.scan.finished.connect(self.scan.deleteLater)
        self.scan.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def start_map(self):
        self.thread = QThread()
        self.map = Map(self)  # .curr_coords, self.XX, self.YY, self.frequency, self.update_voltage_signal, self.scan_on_boolean_in_list)
        self.map.moveToThread(self.thread)
        self.thread.started.connect(self.map.run)
        self.thread.started.connect(self.update_graphs)
        self.map.finishedAfterMapping.connect(self.toggle_map_button)
        # self.map.finished.connect(self.on_off_spinbox_list_turn_on)
        self.map.finished.connect(self.map.deleteLater)
        self.map.finished.connect(self.thread.quit)
        self.map.lineFinished.connect(self.update_graphs)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()


    def update_voltage(self):
        # print("Updated voltage: x = ", self.curr_coords[0], ", y = ", self.curr_coords[1])
        self.label_current_x.setText("Current x (V): " + str(self.curr_coords[0]))
        self.label_current_y.setText("Current y (V): " + str(self.curr_coords[1]))
        #todo: update line graph with certain time interval.
        self.update_line_graph()

    def get_voltage_ch1_ch2(self):
        return (np.random.random() + 1, np.random.random() + 2)

    def update_line_graph(self):
        self.widget_linescan_ch1.clear()
        self.widget_linescan_ch2.clear()
        self.widget_linescan_ch1.plot(self.line_trace['X'], self.line_trace['ch1'], pen = mkPen(color=(0, 180, 0)))
        self.widget_linescan_ch1.plot(self.line_retrace['X'], self.line_retrace['ch1'], pen = mkPen(color=(180, 0, 0)))
        self.widget_linescan_ch2.plot(self.line_trace['X'], self.line_trace['ch2'], pen = mkPen(color=(0, 180, 0)))
        self.widget_linescan_ch2.plot(self.line_retrace['X'], self.line_retrace['ch2'], pen = mkPen(color=(180, 0, 0)))

    # def update_map_graph(self):


    def goto_position(self, p):
        self.thread = QThread()
        self.move = MoveToTarget(self, p, manual_move=True)  # .curr_coords, self.XX, self.YY, self.frequency, self.update_voltage_signal, self.scan_on_boolean_in_list)
        self.move.moveToThread(self.thread)
        self.thread.started.connect(self.move.move)
        self.move.started.connect(self.on_off_button_list_turn_off)
        self.move.started.connect(self.on_off_spinbox_list_turn_off)
        self.move.finished.connect(self.move.deleteLater)
        self.move.finished.connect(self.on_off_button_list_turn_on)
        self.move.finished.connect(self.on_off_spinbox_list_turn_on)
        self.move.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_off_button_list_turn_on(self, without_pushButton_image = False, without_pushButton_scan = False):
        for w in self.on_off_button_list:
            if (without_pushButton_image and w == self.pushButton_image) or (without_pushButton_scan and w == self.pushButton_scan):
                continue
            w.setDisabled(False)
    def on_off_button_list_turn_off(self):
        for w in self.on_off_button_list:
            w.setDisabled(True)
    def on_off_spinbox_list_turn_on(self):
        for w in self.on_off_spinbox_list:
            w.setDisabled(False)
    def on_off_spinbox_list_turn_off(self):
        for w in self.on_off_spinbox_list:
            w.setDisabled(True)
'''
import nidaqmx
with nidaqmx.Task() as task:
    task.ao_channels.add_ao_voltage_chan("NIdevice/ao3")
    task.write(0.)
'''






if __name__ == "__main__":
    app = QApplication([])
    widget = SPMController()
    widget.show()
    sys.exit(app.exec_())
