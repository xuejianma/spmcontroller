"""
Created by Xuejian Ma at 10/2/2021.
All rights reserved.
"""

# This Python file uses the following encoding: utf-8
import sys
import os

from PyQt5.QtMultimedia import QSound
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget
from pyqtgraph import mkPen
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QGridLayout, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QFile, Qt, QSize, QObject, QThread, pyqtSignal, QSettings
from scan import Scan, MoveToTarget, Map, ApproachDisplay, MoveToTargetZ, AutoApproach
from plotscanrange import plot_scan_range, toggle_colorbar_main, toggle_colorbar_ch1, toggle_colorbar_ch2
from anc300 import ANC300
from sr830 import SR830
from hardware import OutputVoltage, InputVoltage, InputVoltageEncoder
from os.path import isdir
# from pyvisa import ResourceManager
from planefit import PlaneFit
import numpy as np


class SPMController(QWidget):
    update_graphs_signal = pyqtSignal()
    update_display_approach_signal = pyqtSignal()

    # output_voltage_signal = pyqtSignal()
    def __init__(self):
        super(SPMController, self).__init__()
        # self.anc_controller = ANC300(3)
        # self.rm = ResourceManager()

        self.curr_coord_z = 0.0
        self.error_lock = False
        self.positioner_moving = False
        self.display_approach_on = False
        self.error_lock_text = "🚫 Error: Scan window exceeds piezo limit"
        self.data_store = []  # 5 x n, (XX, YY, array1, array2) x n)
        self.display_list_ch1 = []
        self.display_list_ch2 = []
        self.data_choose = -1
        self.channel_choose = 1  # 1 or 2
        self.scan_on_boolean = False
        self.map_on_boolean = False
        self.auto_approach_on_boolean = False
        self.map_trace = {'XX': [], 'YY': [], 'ch1': [], 'ch2': []}
        self.map_retrace = {'XX': [], 'YY': [], 'ch1': [], 'ch2': []}
        self.colorbar_manual_main = False
        self.colorbar_manual_ch1 = False
        self.colorbar_manual_ch2 = False
        self.load_ui()
        self.preload()
        self.reconnect_anc300()
        self.reconnect_lockin()

        # self.list_resources()

        self.initialize_formats()
        self.determine_scan_window()
        self.plane_fit_list = [
            [self.doubleSpinBox_plane_fit_x, self.doubleSpinBox_plane_fit_x_2, self.doubleSpinBox_plane_fit_x_3,
             self.doubleSpinBox_plane_fit_x_4, self.doubleSpinBox_plane_fit_x_5],
            [self.doubleSpinBox_plane_fit_y, self.doubleSpinBox_plane_fit_y_2, self.doubleSpinBox_plane_fit_y_3,
             self.doubleSpinBox_plane_fit_y_4, self.doubleSpinBox_plane_fit_y_5],
            [self.doubleSpinBox_plane_fit_delta_z, self.doubleSpinBox_plane_fit_delta_z_2,
             self.doubleSpinBox_plane_fit_delta_z_3,
             self.doubleSpinBox_plane_fit_delta_z_4, self.doubleSpinBox_plane_fit_delta_z_5],
            [self.checkBox_plane_fit, self.checkBox_plane_fit_2, self.checkBox_plane_fit_3,
             self.checkBox_plane_fit_4, self.checkBox_plane_fit_5]
        ]
        self.connect_all()
        self.curr_coords = [0, 0]
        self.on_off_spinbox_list = [self.doubleSpinBox_x_min, self.doubleSpinBox_x_max, self.doubleSpinBox_y_min,
                                    self.doubleSpinBox_y_max, self.spinBox_x_pixels, self.spinBox_y_pixels,
                                    self.doubleSpinBox_rotation,  # self.doubleSpinBox_frequency,
                                    self.doubleSpinBox_piezo_limit_x, self.doubleSpinBox_piezo_limit_y,
                                    self.lineEdit_filename_trace_ch1, self.lineEdit_filename_trace_ch2,
                                    self.lineEdit_filename_retrace_ch1, self.lineEdit_filename_retrace_ch2,
                                    self.lineEdit_directory, self.doubleSpinBox_goto_x, self.doubleSpinBox_goto_y,
                                    self.pushButton_goto0,
                                    self.pushButton_goto,
                                    self.pushButton_reconnect_hardware,
                                    ]
        self.on_off_button_list = [self.pushButton_scan, self.pushButton_image,
                                   # self.doubleSpinBox_goto_x, self.doubleSpinBox_goto_y,
                                   ]

        self.line_trace = {'X': [], 'ch1': [], 'ch2': []}
        self.line_retrace = {'X': [], 'ch1': [], 'ch2': []}
        self.hardware_io()
        self.approached_sound = QSound("57806__guitarguy1985__aircraftalarm.wav")
        self.plane_fit = PlaneFit()
        # self.output_voltage_x = OutputVoltage(port='x', label_error=self.label_error)
        # self.output_voltage_y = OutputVoltage(port='y', label_error=self.label_error)
        # self.output_voltage_z = OutputVoltage(port='z', label_error=self.label_error)
        # self.input_voltage_ch1_ch2 = InputVoltage(label_error=self.label_error)
        #
        # self.output_voltage_encoder = OutputVoltage(port='encoder', label_error=self.label_error)
        # self.input_voltage_encoder = InputVoltageEncoder(label_error=self.label_error)
        # self.input_voltage_ch1 = InputVoltage(port='ch1', label_error=self.label_error)
        # self.input_voltage_ch2 = InputVoltage(port='ch2', label_error=self.label_error)

        # check_minmaxrotation_valid()


    def hardware_io(self):
        try:
            self.output_voltage_x.close()
            self.output_voltage_y.close()
            self.output_voltage_z.close()
            self.input_voltage_ch1_ch2.close()
        except:
            pass
        self.output_voltage_x = OutputVoltage(port='x', label_error=self.label_error)
        self.output_voltage_y = OutputVoltage(port='y', label_error=self.label_error)
        self.output_voltage_z = OutputVoltage(port='z', label_error=self.label_error)
        self.input_voltage_ch1_ch2 = InputVoltage(label_error=self.label_error)
        self.output_voltage_encoder = OutputVoltage(port='encoder', label_error=self.label_error, ratio = 1000)
        # self.input_voltage_encoder = InputVoltageEncoder(label_error=self.label_error)


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

        self.widget_linescan_approach_ch1.setBackground("w")
        self.widget_linescan_approach_ch2.setBackground("w")

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

    def update_graphs(self, single='all'):
        xlim_min = np.min([self.p1[0], self.p2[0], self.p3[0], self.p4[0]])
        xlim_max = np.max([self.p1[0], self.p2[0], self.p3[0], self.p4[0]])
        ylim_min = np.min([self.p1[1], self.p2[1], self.p3[1], self.p4[1]])
        ylim_max = np.max([self.p1[1], self.p2[1], self.p3[1], self.p4[1]])
        if single == 'all' or single == 'main':
            self.plot_scan_range(self.widget_display_piezo_limit, xlim_min=0, xlim_max=self.piezo_limit_x, ylim_min=0,
                                 ylim_max=self.piezo_limit_y)
        if single == 'all' or single == 'ch1':
            self.plot_scan_range(self.widget_display_scan_window_ch1, xlim_min=xlim_min, xlim_max=xlim_max,
                                 ylim_min=ylim_min,
                                 ylim_max=ylim_max)
        if single == 'all' or single == 'ch2':
            self.plot_scan_range(self.widget_display_scan_window_ch2, xlim_min=xlim_min, xlim_max=xlim_max,
                                 ylim_min=ylim_min,
                                 ylim_max=ylim_max)

    def update_display_approach(self):
        self.widget_linescan_approach_ch1.clear()
        self.widget_linescan_approach_ch2.clear()
        self.widget_linescan_approach_ch1.plot(self.display_list_ch1, pen=mkPen(color=(0, 0, 0)))
        self.widget_linescan_approach_ch2.plot(self.display_list_ch2, pen=mkPen(color=(0, 0, 0)))

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
        self.update_graphs_signal.connect(self.update_voltage)
        # self.output_voltage_signal.connect(self.output_voltage)
        self.pushButton_scan.clicked.connect(self.toggle_scan_button)
        self.pushButton_goto0.clicked.connect(lambda: self.goto_position(np.array([0, 0])))
        self.pushButton_goto.clicked.connect(lambda: self.goto_position(np.array([self.doubleSpinBox_goto_x.value(),
                                                                                  self.doubleSpinBox_goto_y.value()])))
        self.checkBox_maintenance.toggled.connect(self.toggle_maintenance)
        self.doubleSpinBox_current_x.valueChanged.connect(self.update_voltage_maintenance)
        self.doubleSpinBox_current_y.valueChanged.connect(self.update_voltage_maintenance)
        self.pushButton_image.clicked.connect(self.toggle_map_button)
        self.buttonGroup.buttonToggled.connect(lambda: self.update_graphs(single='main'))
        self.buttonGroup_2.buttonToggled.connect(lambda: self.update_graphs(single='main'))
        self.buttonGroup_3.buttonToggled.connect(lambda: self.update_graphs(single='ch1'))
        self.buttonGroup_4.buttonToggled.connect(lambda: self.update_graphs(single='ch2'))

        self.buttonGroup_5.buttonToggled.connect(self.toggle_colorbar_main)
        self.doubleSpinBox_colorbar_manual_min_main.valueChanged.connect(self.toggle_colorbar_main)
        self.doubleSpinBox_colorbar_manual_max_main.valueChanged.connect(self.toggle_colorbar_main)

        self.buttonGroup_6.buttonToggled.connect(self.toggle_colorbar_ch1)
        self.doubleSpinBox_colorbar_manual_min_ch1.valueChanged.connect(self.toggle_colorbar_ch1)
        self.doubleSpinBox_colorbar_manual_max_ch1.valueChanged.connect(self.toggle_colorbar_ch1)

        self.buttonGroup_7.buttonToggled.connect(self.toggle_colorbar_ch2)
        self.doubleSpinBox_colorbar_manual_min_ch2.valueChanged.connect(self.toggle_colorbar_ch2)
        self.doubleSpinBox_colorbar_manual_max_ch2.valueChanged.connect(self.toggle_colorbar_ch2)

        self.pushButton_directory.clicked.connect(self.selectDirectory)
        self.doubleSpinBox_z.valueChanged.connect(self.output_voltage_z_direction)
        self.pushButton_reconnect_hardware.clicked.connect(self.hardware_io)

        # self.comboBox_anc300.currentIndexChanged.connect(self.choose_anc300)
        self.pushButton_reconnect_anc300.clicked.connect(self.reconnect_anc300)
        self.pushButton_positioner_on.clicked.connect(lambda: self.anc_controller.setm(4, "stp"))
        self.pushButton_positioner_off.clicked.connect(lambda: self.anc_controller.setm(4, "gnd"))
        self.pushButton_positioner_off.clicked.connect(
            lambda: self.move_positioner_toggle() if self.positioner_moving else None)
        self.pushButton_scanner_x_dc_on.clicked.connect(lambda: self.anc_controller.setdci(1, "on"))
        self.pushButton_scanner_x_dc_off.clicked.connect(lambda: self.anc_controller.setdci(1, "off"))
        self.pushButton_scanner_y_dc_on.clicked.connect(lambda: self.anc_controller.setdci(2, "on"))
        self.pushButton_scanner_y_dc_off.clicked.connect(lambda: self.anc_controller.setdci(2, "off"))
        self.pushButton_scanner_z_dc_on.clicked.connect(lambda: self.anc_controller.setdci(3, "on"))
        self.pushButton_scanner_z_dc_off.clicked.connect(lambda: self.anc_controller.setdci(3, "off"))
        self.pushButton_scanner_x_ac_on.clicked.connect(lambda: self.anc_controller.setaci(1, "on"))
        self.pushButton_scanner_x_ac_off.clicked.connect(lambda: self.anc_controller.setaci(1, "off"))
        self.pushButton_scanner_y_ac_on.clicked.connect(lambda: self.anc_controller.setaci(2, "on"))
        self.pushButton_scanner_y_ac_off.clicked.connect(lambda: self.anc_controller.setaci(2, "off"))
        self.pushButton_scanner_z_ac_on.clicked.connect(lambda: self.anc_controller.setaci(3, "on"))
        self.pushButton_scanner_z_ac_off.clicked.connect(lambda: self.anc_controller.setaci(3, "off"))

        self.pushButton_positioner_move.clicked.connect(self.move_positioner_toggle)
        self.spinBox_positioner_frequency.valueChanged.connect(
            lambda: self.anc_controller.setf(4, self.spinBox_positioner_frequency.value()))
        self.doubleSpinBox_positioner_amplitude.valueChanged.connect(
            lambda: self.anc_controller.setv(4, self.doubleSpinBox_positioner_amplitude.value()))

        #SR830 Top:
        self.spinBox_lockin_top_reference.valueChanged.connect(
            lambda: self.lockin_top.set_reference_source(self.spinBox_lockin_top_reference.value()))
        self.doubleSpinBox_lockin_top_reference_internal_frequency.valueChanged.connect(
            lambda: self.lockin_top.set_frequency(self.doubleSpinBox_lockin_top_reference_internal_frequency.value()))
        self.spinBox_lockin_top_time_constant.valueChanged.connect(
            lambda: self.lockin_top.set_time_constant(self.spinBox_lockin_top_time_constant.value()))
        self.spinBox_lockin_top_display.valueChanged.connect(
            lambda: self.lockin_top.set_display(1, self.spinBox_lockin_top_display.value()))
        self.spinBox_lockin_top_output_mode.valueChanged.connect(
            lambda: self.lockin_top.set_output(1, self.spinBox_lockin_top_output_mode.value()))
        #SR830 Bottom:
        self.spinBox_lockin_bottom_reference.valueChanged.connect(
            lambda: self.lockin_bottom.set_reference_source(self.spinBox_lockin_bottom_reference.value()))
        self.doubleSpinBox_lockin_bottom_reference_internal_frequency.valueChanged.connect(
            lambda: self.lockin_bottom.set_frequency(self.doubleSpinBox_lockin_bottom_reference_internal_frequency.value()))
        self.spinBox_lockin_bottom_time_constant.valueChanged.connect(
            lambda: self.lockin_bottom.set_time_constant(self.spinBox_lockin_bottom_time_constant.value()))
        self.spinBox_lockin_bottom_display.valueChanged.connect(
            lambda: self.lockin_bottom.set_display(1, self.spinBox_lockin_bottom_display.value()))
        self.spinBox_lockin_bottom_output_mode.valueChanged.connect(
            lambda: self.lockin_bottom.set_output(1, self.spinBox_lockin_bottom_output_mode.value()))
        # start display for approach
        self.pushButton_approach_monitor.clicked.connect(self.toggle_display_approach_button)

        self.update_display_approach_signal.connect(self.update_display_approach)
        self.doubleSpinBox_encoder.valueChanged.connect(
            lambda: self.output_voltage_encoder.outputVoltage(self.doubleSpinBox_encoder.value()))

        self.checkBox_encoder_reading.stateChanged.connect(self.real_time_encoder)

        self.pushButton_z_goto.clicked.connect(
            lambda: self.goto_position_z(self.doubleSpinBox_z_goto.value()))
        self.pushButton_z_goto0.clicked.connect(
            lambda: self.goto_position_z(0.0))

        self.pushButton_approach_auto_start.clicked.connect(self.toggle_auto_approach_button)

        for i in range(len(self.plane_fit_list[0])):
            plane_fit_x, plane_fit_y, plane_fit_z, plane_fit_checked = self.plane_fit_list[0][i],\
            self.plane_fit_list[1][i], self.plane_fit_list[2][i], self.plane_fit_list[3][i]
            plane_fit_x.valueChanged.connect(self.update_plane_fit)
            plane_fit_y.valueChanged.connect(self.update_plane_fit)
            plane_fit_z.valueChanged.connect(self.update_plane_fit)
            plane_fit_checked.toggled.connect(self.update_plane_fit)

    def plot_scan_range(self, widget, xlim_min, xlim_max, ylim_min, ylim_max):
        plot_scan_range(self, widget, xlim_min, xlim_max, ylim_min, ylim_max)

    def toggle_colorbar_main(self):
        toggle_colorbar_main(self)

    def toggle_colorbar_ch1(self):
        toggle_colorbar_ch1(self)

    def toggle_colorbar_ch2(self):
        toggle_colorbar_ch2(self)

    def toggle_maintenance(self):
        if self.checkBox_maintenance.isChecked():
            self.doubleSpinBox_current_x.setDisabled(False)
            self.doubleSpinBox_current_y.setDisabled(False)
        else:
            self.doubleSpinBox_current_x.setDisabled(True)
            self.doubleSpinBox_current_y.setDisabled(True)

    def toggle_scan_button(self):
        if self.error_lock:
            self.label_error.setText(self.error_lock_text)
            return
        if self.scan_on_boolean:
            # The reason we didn't put the following expression outside of if-else is because while loop in start_
            # scan's Scan() needs to
            # determine whether to run based on the new boolean value. It somehow works if we put it at the end, but
            # simply because assigining new thread takes more time, and it has time to change boolean value before
            # the running really starts.
            self.scan_on_boolean = not self.scan_on_boolean
            self.on_off_spinbox_list_turn_on()
            self.pushButton_image.setDisabled(False)
            self.pushButton_scan.setText("Scan")
        else:
            self.scan_on_boolean = not self.scan_on_boolean
            self.pushButton_scan.setText("OFF")
            self.on_off_spinbox_list_turn_off()
            self.pushButton_image.setDisabled(True)
            self.start_scan()


    def toggle_map_button(self):
        if self.error_lock:
            self.label_error.setText(self.error_lock_text)
            return
        if not isdir(self.lineEdit_directory.text()):
            self.label_error.setText("🚫 Error: Auto save directory not found")
            return
        if self.map_on_boolean:
            self.map_on_boolean = not self.map_on_boolean
            self.on_off_spinbox_list_turn_on()
            self.pushButton_scan.setDisabled(False)
            self.pushButton_image.setText("Image")
        else:
            self.map_on_boolean = not self.map_on_boolean
            self.pushButton_image.setText("OFF")
            self.on_off_spinbox_list_turn_off()
            self.pushButton_scan.setDisabled(True)
            self.start_map()


    def toggle_display_approach_button(self):
        if self.display_approach_on:
            self.display_approach_on = not self.display_approach_on
            self.pushButton_approach_monitor.setText("START  Display Channel 1 and Channel 2")
        else:
            self.display_approach_on = not self.display_approach_on
            self.pushButton_approach_monitor.setText("STOP  Display Channel 1 and Channel 2")
            self.start_display_approach()


    def toggle_auto_approach_button(self):
        if self.auto_approach_on_boolean:
            self.auto_approach_on_boolean = not self.auto_approach_on_boolean

            self.pushButton_approach_auto_start.setText("START Auto Approach")
        else:
            self.auto_approach_on_boolean = not self.auto_approach_on_boolean
            self.pushButton_approach_auto_start.setText("STOP Auto Approach")
            self.auto_approach()

    def update_voltage_maintenance(self):
        self.curr_coords[0] = self.doubleSpinBox_current_x.value()
        self.curr_coords[1] = self.doubleSpinBox_current_y.value()
        self.update_voltage()

    def start_scan(self):
        self.thread = QThread()
        self.scan = Scan(
            self)  # .curr_coords, self.XX, self.YY, self.frequency, self.update_voltage_signal, self.scan_on_boolean_in_list)
        self.scan.moveToThread(self.thread)
        self.thread.started.connect(self.scan.run)
        self.scan.finished.connect(self.scan.deleteLater)
        self.scan.finished.connect(self.thread.exit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def start_map(self):
        self.thread = QThread()
        self.map = Map(
            self)  # .curr_coords, self.XX, self.YY, self.frequency, self.update_voltage_signal, self.scan_on_boolean_in_list)
        self.map.moveToThread(self.thread)
        self.thread.started.connect(self.map.run)
        self.thread.started.connect(self.update_graphs)
        self.map.finishedAfterMapping.connect(self.toggle_map_button)
        # self.map.finished.connect(self.on_off_spinbox_list_turn_on)
        self.map.finished.connect(self.map.deleteLater)
        self.map.finished.connect(self.thread.exit)
        self.map.lineFinished.connect(self.update_graphs)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def start_display_approach(self):
        self.thread = QThread()
        self.approach_display = ApproachDisplay(self)
        self.approach_display.moveToThread(self.thread)
        self.thread.started.connect(self.approach_display.run)
        self.approach_display.finished.connect(self.approach_display.deleteLater)
        self.approach_display.finished.connect(self.thread.exit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def update_voltage(self):
        # print("Updated voltage: x = ", self.curr_coords[0], ", y = ", self.curr_coords[1])
        self.label_current_x.setText("Current x (V): " + str(self.curr_coords[0]))
        self.label_current_y.setText("Current y (V): " + str(self.curr_coords[1]))
        self.update_line_graph()

    def output_voltage(self):
        self.output_voltage_x.outputVoltage(self.curr_coords[0])
        self.output_voltage_y.outputVoltage(self.curr_coords[1])
        self.output_voltage_z.outputVoltage(self.curr_coord_z +
                                            self.plane_fit.get_delta_z_plane_fitted(self.curr_coords[0],
                                                                                    self.curr_coords[1]))
    def output_voltage_z_direction(self):
        self.curr_coord_z = np.round(self.doubleSpinBox_z.value(), 6)
        self.output_voltage_z.outputVoltage(self.curr_coord_z +
                                            self.plane_fit.get_delta_z_plane_fitted(self.curr_coords[0],
                                                                                    self.curr_coords[1]))

    def get_voltage_ch1_ch2(self):
        # return (np.random.random() + 1, np.random.random() + 2)
        # return self.input_voltage_ch1.getVoltage(), self.input_voltage_ch2.getVoltage()
        return self.input_voltage_ch1_ch2.getVoltage()

    def real_time_encoder(self):
        if self.checkBox_encoder_reading.isChecked():
            self.thread_encoder = QThread()
            self.input_voltage_encoder = InputVoltageEncoder(
                label_error=self.label_error, lcdNumber_encoder_reading = self.lcdNumber_encoder_reading,
                checkBox_encoder_reading = self.checkBox_encoder_reading)
            self.input_voltage_encoder.moveToThread(self.thread_encoder)
            self.thread_encoder.started.connect(self.input_voltage_encoder.run)
            # self.input_voltage_encoder.update.connect(
            #     lambda: self.lcdNumber_encoder_reading.display(self.input_voltage_encoder.curr_value))
            self.input_voltage_encoder.finished.connect(self.input_voltage_encoder.deleteLater)
            self.input_voltage_encoder.finished.connect(self.thread_encoder.exit)
            self.thread_encoder.finished.connect(self.thread_encoder.deleteLater)
            self.thread_encoder.start()


    def update_line_graph(self):
        self.widget_linescan_ch1.clear()
        self.widget_linescan_ch2.clear()
        self.widget_linescan_ch1.plot(self.line_trace['X'], self.line_trace['ch1'], pen=mkPen(color=(0, 180, 0)))
        self.widget_linescan_ch1.plot(self.line_retrace['X'], self.line_retrace['ch1'], pen=mkPen(color=(180, 0, 0)))
        self.widget_linescan_ch2.plot(self.line_trace['X'], self.line_trace['ch2'], pen=mkPen(color=(0, 180, 0)))
        self.widget_linescan_ch2.plot(self.line_retrace['X'], self.line_retrace['ch2'], pen=mkPen(color=(180, 0, 0)))

    # def update_map_graph(self):



    def goto_position(self, p):
        self.thread = QThread()
        self.move = MoveToTarget(self, p,
                                 manual_move=True)  # .curr_coords, self.XX, self.YY, self.frequency, self.update_voltage_signal, self.scan_on_boolean_in_list)
        self.move.moveToThread(self.thread)
        self.thread.started.connect(self.move.move)
        self.move.started.connect(self.on_off_button_list_turn_off)
        self.move.started.connect(self.on_off_spinbox_list_turn_off)
        self.move.finished.connect(self.move.deleteLater)
        self.move.finished.connect(self.on_off_button_list_turn_on)
        self.move.finished.connect(self.on_off_spinbox_list_turn_on)
        self.move.finished.connect(self.thread.exit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def goto_position_z(self, target):
        self.thread = QThread()
        self.move = MoveToTargetZ(self, target)
        self.move.moveToThread(self.thread)
        self.thread.started.connect(self.move.move)
        self.move.started.connect(self.goto_position_z_buttons_off)
        self.move.finished.connect(self.goto_position_z_buttons_on)

        self.move.finished.connect(self.move.deleteLater)
        self.move.finished.connect(self.thread.exit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def goto_position_z_buttons_off(self):
        self.pushButton_z_goto.setDisabled(True)
        self.pushButton_z_goto0.setDisabled(True)
        self.doubleSpinBox_z.setDisabled(True)
        self.doubleSpinBox_z_goto.setDisabled(True)
        self.pushButton_positioner_move.setDisabled(True)

    def goto_position_z_buttons_on(self):
        self.pushButton_z_goto.setEnabled(True)
        self.pushButton_z_goto0.setEnabled(True)
        self.doubleSpinBox_z.setEnabled(True)
        self.doubleSpinBox_z_goto.setEnabled(True)
        self.pushButton_positioner_move.setEnabled(True)


    def auto_approach(self):
        self.thread_approach = QThread()
        self.approach_auto = AutoApproach(self)
        self.approach_auto.moveToThread(self.thread_approach)
        self.thread_approach.started.connect(self.approach_auto.move)
        self.approach_auto.approached.connect(self.approached_sound.play)
        self.approach_auto.finished.connect(self.approach_auto.deleteLater)
        self.approach_auto.finished.connect(self.thread_approach.exit)
        # self.approach_auto.finishedAfterApproach.connect(self.toggle_auto_approach_button)
        self.thread_approach.finished.connect(self.thread_approach.deleteLater)
        self.thread_approach.start()


    def on_off_button_list_turn_on(self, without_pushButton_image=False, without_pushButton_scan=False):
        for w in self.on_off_button_list:
            if (without_pushButton_image and w == self.pushButton_image) or (
                    without_pushButton_scan and w == self.pushButton_scan):
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

    def selectDirectory(self):
        directoryName = QFileDialog.getExistingDirectory(self,
                                                         'Select directory')  # getOpenFileName(self, 'Open file', '.', '')
        self.label_error.setText("")
        self.lineEdit_directory.setText(directoryName)

    def preload(self):
        self.approach_attributes_int = {
            'spinBox_lockin_top_reference': self.spinBox_lockin_top_reference,
            'spinBox_lockin_top_time_constant': self.spinBox_lockin_top_time_constant,
            'spinBox_lockin_top_display': self.spinBox_lockin_top_display,
            'spinBox_lockin_top_output_mode': self.spinBox_lockin_top_output_mode,
            'spinBox_lockin_bottom_reference': self.spinBox_lockin_bottom_reference,
            'spinBox_lockin_bottom_time_constant': self.spinBox_lockin_bottom_time_constant,
            'spinBox_lockin_bottom_display': self.spinBox_lockin_bottom_display,
            'spinBox_lockin_bottom_output_mode': self.spinBox_lockin_bottom_output_mode,
            'spinBox_positioner_frequency': self.spinBox_positioner_frequency,
        }
        self.approach_attributes_float = {
            'doubleSpinBox_lockin_top_reference_internal_frequency': self.doubleSpinBox_lockin_top_reference_internal_frequency,
            'doubleSpinBox_lockin_bottom_reference_internal_frequency': self.doubleSpinBox_lockin_bottom_reference_internal_frequency,
            'doubleSpinBox_positioner_amplitude': self.doubleSpinBox_positioner_amplitude,
            'doubleSpinBox_positioner_time_per_turn': self.doubleSpinBox_positioner_time_per_turn,
            'doubleSpinBox_scanner_voltage_per_turn': self.doubleSpinBox_scanner_voltage_per_turn,
            'doubleSpinBox_approach_scanner_speed': self.doubleSpinBox_approach_scanner_speed,
        }
        self.settings = QSettings('SPMController', 'App1')
        # try:
        self.doubleSpinBox_x_min.setValue(float(self.settings.value('doubleSpinBox_x_min')))
        self.doubleSpinBox_x_max.setValue(float(self.settings.value('doubleSpinBox_x_max')))
        self.doubleSpinBox_y_min.setValue(float(self.settings.value('doubleSpinBox_y_min')))
        self.doubleSpinBox_y_max.setValue(float(self.settings.value('doubleSpinBox_y_max')))
        self.spinBox_x_pixels.setValue(self.settings.value('spinBox_x_pixels'))
        self.spinBox_y_pixels.setValue(self.settings.value('spinBox_y_pixels'))
        self.doubleSpinBox_frequency.setValue(float(self.settings.value('doubleSpinBox_frequency')))
        self.doubleSpinBox_rotation.setValue(float(self.settings.value('doubleSpinBox_rotation')))
        self.lineEdit_directory.setText(self.settings.value('lineEdit_directory'))
        self.lineEdit_filename_trace_ch1.setText(self.settings.value('lineEdit_filename_trace_ch1'))
        self.lineEdit_filename_retrace_ch1.setText(self.settings.value('lineEdit_filename_retrace_ch1'))
        self.lineEdit_filename_trace_ch2.setText(self.settings.value('lineEdit_filename_trace_ch2'))
        self.lineEdit_filename_retrace_ch2.setText(self.settings.value('lineEdit_filename_retrace_ch2'))
        self.doubleSpinBox_piezo_limit_x.setValue(float(self.settings.value('doubleSpinBox_piezo_limit_x')))
        self.doubleSpinBox_piezo_limit_y.setValue(float(self.settings.value('doubleSpinBox_piezo_limit_y')))
        for key in self.approach_attributes_float:
            self.approach_attributes_float[key].setValue(float(self.settings.value(key)))
        for key in self.approach_attributes_int:
            self.approach_attributes_int[key].setValue(self.settings.value(key))
        # except:
        #     print("preload error ignored")

    def closeEvent(self, event):

        self.settings.setValue('doubleSpinBox_x_min', self.doubleSpinBox_x_min.value())
        self.settings.setValue('doubleSpinBox_x_max', self.doubleSpinBox_x_max.value())
        self.settings.setValue('doubleSpinBox_y_min', self.doubleSpinBox_y_min.value())
        self.settings.setValue('doubleSpinBox_y_max', self.doubleSpinBox_y_max.value())
        self.settings.setValue('spinBox_x_pixels', self.spinBox_x_pixels.value())
        self.settings.setValue('spinBox_y_pixels', self.spinBox_y_pixels.value())
        self.settings.setValue('doubleSpinBox_frequency', self.doubleSpinBox_frequency.value())
        self.settings.setValue('doubleSpinBox_rotation', self.doubleSpinBox_rotation.value())
        self.settings.setValue('lineEdit_directory', self.lineEdit_directory.text())
        self.settings.setValue('lineEdit_filename_trace_ch1', self.lineEdit_filename_trace_ch1.text())
        self.settings.setValue('lineEdit_filename_retrace_ch1', self.lineEdit_filename_retrace_ch1.text())
        self.settings.setValue('lineEdit_filename_trace_ch2', self.lineEdit_filename_trace_ch2.text())
        self.settings.setValue('lineEdit_filename_retrace_ch2', self.lineEdit_filename_retrace_ch2.text())
        self.settings.setValue('doubleSpinBox_piezo_limit_x', self.doubleSpinBox_piezo_limit_x.value())
        self.settings.setValue('doubleSpinBox_piezo_limit_y', self.doubleSpinBox_piezo_limit_y.value())
        for key in self.approach_attributes_float:
            self.settings.setValue(key, self.approach_attributes_float[key].value())
        for key in self.approach_attributes_int:
            self.settings.setValue(key, self.approach_attributes_int[key].value())

        self.output_voltage_x.close()
        self.output_voltage_y.close()
        self.output_voltage_z.close()
        self.input_voltage_ch1_ch2.close()
        self.output_voltage_encoder.outputVoltage(0.0)
        self.output_voltage_encoder.close()
        # self.input_voltage_encoder.close()

    def reconnect_anc300(self):
        try:
            self.anc_controller = ANC300(3)
            self.label_error_approach.setText("")
        except:
            self.anc_controller = None
            self.label_error_approach.setText("🚫 Error: ANC300 hardware not detected!")

    def reconnect_lockin(self):
        try:
            self.lockin_top = SR830(9)
            self.label_error_lockin_top.setText("")
            self.initialize_lockin_top()
        except:
            self.lockin_top = None
            self.label_error_lockin_top.setText("🚫 SR830 (Top) hardware not detected!")

        try:
            self.lockin_bottom = SR830(8)
            self.label_error_lockin_bottom.setText("")
            self.initialize_lockin_bottom()
        except:
            self.lockin_bottom = None
            self.label_error_lockin_bottom.setText("🚫 SR830 (Bottom) hardware not detected!")
    def initialize_lockin_top(self):
        self.lockin_top.set_reference_source(self.spinBox_lockin_top_reference.value())
        self.lockin_top.set_frequency(self.doubleSpinBox_lockin_top_reference_internal_frequency.value())
        self.lockin_top.set_time_constant(self.spinBox_lockin_top_time_constant.value())
        self.lockin_top.set_display(1, self.spinBox_lockin_top_display.value())
        self.lockin_top.set_output(1, self.spinBox_lockin_top_output_mode.value())

    def initialize_lockin_bottom(self):
        self.lockin_bottom.set_reference_source(self.spinBox_lockin_bottom_reference.value())
        self.lockin_bottom.set_frequency(self.doubleSpinBox_lockin_bottom_reference_internal_frequency.value())
        self.lockin_bottom.set_time_constant(self.spinBox_lockin_bottom_time_constant.value())
        self.lockin_bottom.set_display(1, self.spinBox_lockin_bottom_display.value())
        self.lockin_bottom.set_output(1, self.spinBox_lockin_bottom_output_mode.value())

    def move_positioner_toggle(self):
        if self.positioner_moving:
            self.anc_controller.stop(4)
            self.checkBox_positioner_up.setDisabled(False)
            self.checkBox_positioner_down.setDisabled(False)
            self.label_positioner_running.setText("")
            self.pushButton_positioner_move.setText("Move")
            self.positioner_moving = False
        else:
            self.pushButton_positioner_move.setDisabled(True)
            self.repaint()
            self.checkBox_positioner_up.setDisabled(True)
            self.checkBox_positioner_down.setDisabled(True)
            self.pushButton_positioner_move.setText("Stop")
            self.positioner_moving = True
            try:
                if self.checkBox_positioner_up.isChecked():
                    self.anc_controller.stepu(4, 'c')
                else:
                    self.anc_controller.stepd(4, 'c')
                self.label_positioner_running.setText("Moving...")
            except:
                self.label_positioner_running.setText("🚫 Error: Positioner Off")
                # to stop auto approach when Moving positioner is excuted in AutoApproach module
                self.auto_approach_on_boolean = False
                self.checkBox_positioner_up.setDisabled(False)
                self.checkBox_positioner_down.setDisabled(False)
                self.pushButton_positioner_move.setText("Move")
                self.positioner_moving = False
            self.pushButton_positioner_move.setDisabled(False)

    def update_plane_fit(self):
        points = []
        for i in range(len(self.plane_fit_list[0])):
            plane_fit_x, plane_fit_y, plane_fit_z, plane_fit_checked = self.plane_fit_list[0][i],\
            self.plane_fit_list[1][i], self.plane_fit_list[2][i], self.plane_fit_list[3][i]
            if plane_fit_checked.isChecked():
                points.append([plane_fit_x.value(), plane_fit_y.value(), plane_fit_z.value()])
        print(points, self.plane_fit.p1, self.plane_fit.p2)
        self.plane_fit.fit(points)


'''
TODO: load current position based on values
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
