"""
Created by Xuejian Ma at 10/2/2021.
All rights reserved.
"""

# This Python file uses the following encoding: utf-8
import sys
import os

from PyQt5.QtMultimedia import QSound
from pages.approach_page import ApproachPage
from pages.laser_page import LaserPage
from pages.scan_page import ScanPage
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, QSettings

from lib.ndfiltercontroller import NDFilterController, NDFilterChange
from powercalibration import PowerCalibration
from lib.powermeter import PowerMeterRead, PowerMeter
from util.connect import Connect
# from scan import Scan, MoveToTarget, Map, ApproachDisplay, MoveToTargetZ, AutoApproach
# from util.plotscanrange import plot_scan_range, toggle_colorbar_main, toggle_colorbar_ch1, toggle_colorbar_ch2
from lib.anc300 import ANC300
from lib.sr8x0 import SR8x0
from lib.niboard import OutputVoltage, InputVoltage, OutputVoltageXYZ
# from pyvisa import ResourceManager
from util.planefit import PlaneFit
# import numpy as np
# import pandas as pd

# from lib.topas4 import Topas4, LaserWavelengthChange
# from lasermeasurement import LaserMeasurement


class SPMController(QWidget, ApproachPage, ScanPage, LaserPage, Connect):
    update_graphs_signal = pyqtSignal()
    update_display_approach_signal = pyqtSignal()

    # output_voltage_signal = pyqtSignal()
    def __init__(self):
        # super(SPMController, self).__init__()
        QWidget.__init__(self)
        
        # self.anc_controller = ANC300(3)
        # self.rm = ResourceManager()
        self.load_ui()
        self.mainThread = QThread.currentThread()
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
        self.channel_signal_source = 1 # 1 for NIBoard, 2 for LockIns
        self.manual_goto_boolean = False
        self.scan_on_boolean = False
        self.map_on_boolean = False
        self.manual_z_goto_boolean = False
        self.auto_approach_on_boolean = False
        self.map_trace = {'XX': [], 'YY': [], 'ch1': [], 'ch2': []}
        self.map_retrace = {'XX': [], 'YY': [], 'ch1': [], 'ch2': []}
        self.colorbar_manual_main = False
        self.colorbar_manual_ch1 = False
        self.colorbar_manual_ch2 = False
        self.calibration_on = False
        self.laser_measurement_on = False
        self.last_calibration_mode = 'A'
        self.current_image_index = 1 # 1 by default, which is the latest self.map_trace and self.map_retrace. Any value >1 retrieves image in self.map_history
        self.map_history = []
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
        self.curr_coords = [0.0, 0.0]
        self.on_off_spinbox_list = [self.doubleSpinBox_x_min, self.doubleSpinBox_x_max, self.doubleSpinBox_y_min,
                                    self.doubleSpinBox_y_max, self.spinBox_x_pixels, self.spinBox_y_pixels,
                                    self.doubleSpinBox_rotation,  # self.doubleSpinBox_frequency,
                                    self.doubleSpinBox_piezo_limit_x, self.doubleSpinBox_piezo_limit_y,
                                    self.lineEdit_filename_trace_ch1, self.lineEdit_filename_trace_ch2,
                                    self.lineEdit_filename_retrace_ch1, self.lineEdit_filename_retrace_ch2,
                                    self.lineEdit_directory, self.doubleSpinBox_goto_x, self.doubleSpinBox_goto_y,
                                    self.pushButton_goto0,
                                    self.pushButton_goto,
                                    self.pushButton_stop_goto,
                                    self.pushButton_reconnect_hardware,
                                    ]
        self.on_off_button_list = [self.pushButton_scan, self.pushButton_image,
                                   # self.doubleSpinBox_goto_x, self.doubleSpinBox_goto_y,
                                   ]

        self.on_off_laser_widget_list = [
            self.doubleSpinBox_laser_set_wavelength, self.pushButton_laser_set_wavelength, self.doubleSpinBox_ndfilter,
            self.pushButton_ndfilter, self.doubleSpinBox_laser_calibration_target_power_uW,
            self.doubleSpinBox_laser_calibration_wavelength_start, self.doubleSpinBox_laser_calibration_wavelength_end,
            self.doubleSpinBox_laser_calibration_step, self.doubleSpinBox_laser_calibration_lowest_angle,
            self.doubleSpinBox_laser_calibration_highest_angle, self.doubleSpinBox_laser_calibration_starting_angle,
            self.doubleSpinBox_laser_calibration_ending_angle, self.doubleSpinBox_laser_calibration_step_sweep_power,
            self.radioButton_laser_measurement_constant_power, self.radioButton_laser_measurement_constant_angle,
            self.doubleSpinBox_laser_measurement_wavelength_start, self.doubleSpinBox_laser_measurement_wavelength_end,
            self.doubleSpinBox_laser_measurement_step, self.radioButton_laser_measurement_mode3,
            self.radioButton_laser_measurement_mode4, self.doubleSpinBox_laser_measurement_starting_angle,
            self.doubleSpinBox_laser_measurement_ending_angle, self.doubleSpinBox_laser_measurement_step_sweep_power,
            self.pushButton_laser_controller, self.pushButton_ndfilter_controller, self.pushButton_power,
            self.checkBox_read_power, self.checkBox_laser_shutter
        ]

        self.line_trace = {'X': [], 'ch1': [], 'ch2': []}
        self.line_retrace = {'X': [], 'ch1': [], 'ch2': []}
        self.laser_measurement_line_trace = {'mode': 1, 'wavelength': [], 'power': [], 'angle': [], 'ch1': [], 'ch2': []}
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
        # ApproachPage.__init__(self)
        self.reconnect_anc300()
        self.reconnect_opa()
        self.reconnect_ndfilter()
        self.reconnect_power()
        self.preload()
        self.set_z_max()
        self.set_channel_signal_source()
        self.reconnect_lockin()

        # self.list_resources()

        self.initialize_formats()
        self.determine_scan_window()
        
        self.connect_all()

        self.hardware_io()

        self.pushButton_read_lockin.clicked.connect(self.read_lockin)

    def read_lockin(self):
        print()
        # print(self.lockin_top.get_identification())
        # print(self.lockin_top.get_output(), type(self.lockin_top.get_output()))
        # print(self.curr_coords)
        # print("ANC:")
        # # print("0: ", self.anc_controller.geto(0))
        # print("1: ", self.anc_controller.geto(1))
        # print("2: ", self.anc_controller.geto(2))
        # print("3: ", self.anc_controller.geto(3))
        # print("4: ", self.anc_controller.geto(4))
        # # self.add_image_to_history()
        # # print("map_history length: " + str(len(self.map_history)))
        # # print("p1 - p4: ", self.p1, self.p2, self.p3, self.p4)
        print("Ch1 mean: ", sum(self.display_list_ch1) / float(len(self.display_list_ch1)))
        print("Ch1 mean: ", sum(self.display_list_ch2) / float(len(self.display_list_ch2)))


    def hardware_io(self):
        try:
            # self.output_voltage_x.close()
            # self.output_voltage_y.close()
            self.output_voltage_z.close()
            self.output_voltage_xyz.close()
            self.input_voltage_ch1_ch2.close()
            self.output_voltage_encoder.close()
        except:
            pass
        # self.output_voltage_x = OutputVoltage(port='x', label_error=self.label_error)
        # self.output_voltage_y = OutputVoltage(port='y', label_error=self.label_error)
        self.output_voltage_z = OutputVoltage(port='z', label_error=self.label_error)
        self.output_voltage_xyz = OutputVoltageXYZ(label_error = self.label_error)
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

        self.widget_laser_measurement_ch1.setBackground("w")
        self.widget_laser_measurement_ch2.setBackground("w")
    
    def set_channel_signal_source(self):
        if self.channel_signal_source == 1:
            if not self.radioButton_channel_source_niboard_in_scan_page.isChecked():
                self.radioButton_channel_source_niboard_in_scan_page.setChecked(True)
            if not self.radioButton_channel_source_niboard_in_approach_page.isChecked():
                self.radioButton_channel_source_niboard_in_approach_page.setChecked(True)
            if not self.radioButton_channel_source_niboard_in_laser_page.isChecked():
                self.radioButton_channel_source_niboard_in_laser_page.setChecked(True)
        else:
            if not self.radioButton_channel_source_lockins_in_scan_page.isChecked():
                self.radioButton_channel_source_lockins_in_scan_page.setChecked(True)
            if not self.radioButton_channel_source_lockins_in_approach_page.isChecked():
                self.radioButton_channel_source_lockins_in_approach_page.setChecked(True)
            if not self.radioButton_channel_source_lockins_in_laser_page.isChecked():
                self.radioButton_channel_source_lockins_in_laser_page.setChecked(True)

    def set_channel_signal_source_in_approach_page(self):
        if self.radioButton_channel_source_niboard_in_approach_page.isChecked():
            self.channel_signal_source = 1
        else:
            self.channel_signal_source = 2
        self.set_channel_signal_source()

    def set_channel_signal_source_in_scan_page(self):
        if self.radioButton_channel_source_niboard_in_scan_page.isChecked():
            self.channel_signal_source = 1
        else:
            self.channel_signal_source = 2
        self.set_channel_signal_source()

    def set_channel_signal_source_in_laser_page(self):
        if self.radioButton_channel_source_niboard_in_laser_page.isChecked():
            self.channel_signal_source = 1
        else:
            self.channel_signal_source = 2
        self.set_channel_signal_source()











    def get_voltage_ch1_ch2(self):
        # return (np.random.random() + 1, np.random.random() + 2)
        # return self.input_voltage_ch1.getVoltage(), self.input_voltage_ch2.getVoltage()
        if self.channel_signal_source == 1:
            return self.input_voltage_ch1_ch2.getVoltage()
        try:
            return [self.lockin_top.get_output(), self.lockin_bottom.get_output()]
        except:
            error_message = "🚫 Error: LockIns loading error"
            if self.label_lines.text() != error_message:
                self.label_lines.setText(error_message)
            if self.label_error_approach_channels.text() != error_message:
                self.label_error_approach_channels.setText(error_message)
            return [0.0, 0.0]





    # def update_map_graph(self):













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
        try:
            self.doubleSpinBox_x_min.setValue(float(self.settings.value('doubleSpinBox_x_min')))
            self.doubleSpinBox_x_max.setValue(float(self.settings.value('doubleSpinBox_x_max')))
            self.doubleSpinBox_y_min.setValue(float(self.settings.value('doubleSpinBox_y_min')))
            self.doubleSpinBox_y_max.setValue(float(self.settings.value('doubleSpinBox_y_max')))
            self.doubleSpinBox_z_piezo_limit.setValue(float(self.settings.value('doubleSpinBox_z_piezo_limit')))
            self.spinBox_x_pixels.setValue(self.settings.value('spinBox_x_pixels'))
            self.spinBox_y_pixels.setValue(self.settings.value('spinBox_y_pixels'))
            self.doubleSpinBox_frequency.setValue(float(self.settings.value('doubleSpinBox_frequency')))
            self.doubleSpinBox_rotation.setValue(float(self.settings.value('doubleSpinBox_rotation')))
            self.lineEdit_directory.setText(self.settings.value('lineEdit_directory'))
            self.lineEdit_laser_calibration_directory.setText(self.settings.value('lineEdit_laser_calibration_directory'))
            self.lineEdit_laser_measurement_data_save_directory.setText(self.settings.value('lineEdit_laser_measurement_data_save_directory'))
            self.lineEdit_filename_trace_ch1.setText(self.settings.value('lineEdit_filename_trace_ch1'))
            self.lineEdit_filename_retrace_ch1.setText(self.settings.value('lineEdit_filename_retrace_ch1'))
            self.lineEdit_filename_trace_ch2.setText(self.settings.value('lineEdit_filename_trace_ch2'))
            self.lineEdit_filename_retrace_ch2.setText(self.settings.value('lineEdit_filename_retrace_ch2'))
            self.doubleSpinBox_piezo_limit_x.setValue(float(self.settings.value('doubleSpinBox_piezo_limit_x')))
            self.doubleSpinBox_piezo_limit_y.setValue(float(self.settings.value('doubleSpinBox_piezo_limit_y')))
            self.channel_signal_source = float(self.settings.value('channel_signal_source'))
            self.set_channel_signal_source()
            for key in self.approach_attributes_float:
                self.approach_attributes_float[key].setValue(float(self.settings.value(key)))
            for key in self.approach_attributes_int:
                self.approach_attributes_int[key].setValue(self.settings.value(key))
            self.anc_controller.setf(4, self.spinBox_positioner_frequency.value())
            self.anc_controller.setv(4, self.doubleSpinBox_positioner_amplitude.value())
        except Exception as e:
            print("preload error ignored")
            print(e)

        # try:
        #     self.

    def closeEvent(self, event):
        def msg_func(evt):
            if evt.text() == "Cancel":
                event.ignore()
            else:
                self.closeAndSaveStates()
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Warning")
        msg.setInformativeText('Please make sure peizo stages are zeroed and grounded, then select \'OK\' to close the software.')
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.buttonClicked.connect(msg_func)
        msg.exec_()

    # def isZeroed(self):


    def closeAndSaveStates(self):
        print("closing and saving")
        self.settings.setValue('doubleSpinBox_x_min', self.doubleSpinBox_x_min.value())
        self.settings.setValue('doubleSpinBox_x_max', self.doubleSpinBox_x_max.value())
        self.settings.setValue('doubleSpinBox_y_min', self.doubleSpinBox_y_min.value())
        self.settings.setValue('doubleSpinBox_y_max', self.doubleSpinBox_y_max.value())
        self.settings.setValue('doubleSpinBox_z_piezo_limit', self.doubleSpinBox_z_piezo_limit.value())
        self.settings.setValue('spinBox_x_pixels', self.spinBox_x_pixels.value())
        self.settings.setValue('spinBox_y_pixels', self.spinBox_y_pixels.value())
        self.settings.setValue('doubleSpinBox_frequency', self.doubleSpinBox_frequency.value())
        self.settings.setValue('doubleSpinBox_rotation', self.doubleSpinBox_rotation.value())
        self.settings.setValue('lineEdit_directory', self.lineEdit_directory.text())
        self.settings.setValue('lineEdit_laser_calibration_directory', self.lineEdit_laser_calibration_directory.text())
        self.settings.setValue('lineEdit_laser_measurement_data_save_directory', self.lineEdit_laser_measurement_data_save_directory.text())
        self.settings.setValue('lineEdit_filename_trace_ch1', self.lineEdit_filename_trace_ch1.text())
        self.settings.setValue('lineEdit_filename_retrace_ch1', self.lineEdit_filename_retrace_ch1.text())
        self.settings.setValue('lineEdit_filename_trace_ch2', self.lineEdit_filename_trace_ch2.text())
        self.settings.setValue('lineEdit_filename_retrace_ch2', self.lineEdit_filename_retrace_ch2.text())
        self.settings.setValue('doubleSpinBox_piezo_limit_x', self.doubleSpinBox_piezo_limit_x.value())
        self.settings.setValue('doubleSpinBox_piezo_limit_y', self.doubleSpinBox_piezo_limit_y.value())
        self.settings.setValue('channel_signal_source', self.channel_signal_source)
        for key in self.approach_attributes_float:
            self.settings.setValue(key, self.approach_attributes_float[key].value())
        for key in self.approach_attributes_int:
            self.settings.setValue(key, self.approach_attributes_int[key].value())

        # self.output_voltage_x.close()
        # self.output_voltage_y.close()
        self.output_voltage_z.close()
        self.input_voltage_ch1_ch2.close()
        self.output_voltage_encoder.outputVoltage(0.0)
        self.output_voltage_encoder.close()
        # self.input_voltage_encoder.close()





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
