from datetime import datetime
from time import sleep

import numpy as np
import pandas as pd
from PyQt5.QtCore import QObject, pyqtSignal

from lib.ndfiltercontroller import NDFilterChange
from lib.topas4 import LaserWavelengthChange


class LaserMeasurement(QObject):
    halted = pyqtSignal()
    finished = pyqtSignal()
    fresh_new_start = pyqtSignal()
    progress_finished_wavelength_but_waiting_for_angle = pyqtSignal()
    progress_finished_wavelength = pyqtSignal()
    progress_finished_angle = pyqtSignal()
    progress_update_wavelength = pyqtSignal()
    progress_update_angle = pyqtSignal()
    def __init__(self, main, laser_controller, ndfilter_controller, powermeter):
        super(LaserMeasurement, self).__init__()
        self.laser_controller = laser_controller
        self.ndfilter_controller = ndfilter_controller
        self.powermeter = powermeter
        self.main = main
        self.starting_wavelength = self.main.doubleSpinBox_laser_measurement_wavelength_start.value()
        self.ending_wavelength = self.main.doubleSpinBox_laser_measurement_wavelength_end.value()
        self.starting_angle = self.main.doubleSpinBox_laser_measurement_starting_angle.value()
        self.ending_angle = self.main.doubleSpinBox_laser_measurement_ending_angle.value()
        self.mode = 1
        self.convert_angle_to_power_boolean = self.main.radioButton_laser_measurement_mode4.isChecked()
        if self.main.tabWidget_laser_measurement.currentIndex() == 0:
            if self.main.radioButton_laser_measurement_constant_power.isChecked():
                self.mode = 1
            else:
                self.mode = 2
        else:
            if not self.convert_angle_to_power_boolean:
                self.mode = 3
            else:
                self.mode = 4
        # self.step = self.main.doubleSpinBox_laser_measurement_step.value() if self.mode != 3 \
        #     else self.main.doubleSpinBox_laser_measurement_step_sweep_power.value()
        if self.mode == 1 or self.mode == 2:
            self.step = self.main.doubleSpinBox_laser_measurement_step.value()
            if self.starting_wavelength > self.ending_wavelength:
                self.step = -self.step
        else:
            self.step = self.main.doubleSpinBox_laser_measurement_step_sweep_power.value()
            if self.starting_angle > self.ending_angle:
                self.step = -self.step

        self.number = abs(self.ending_wavelength - self.starting_wavelength) // abs(self.step) + 1
        self.number_angle = abs(self.ending_angle - self.starting_angle) // abs(self.step) + 1
        self.curr_wavelength = 0
        self.curr_angle = 0
        self.i = 0
        self.now = datetime.now()

        self.main.laser_measurement_line_trace['mode'] = self.mode

        print("mode number: ", self.mode)
        self.filename = self.main.lineEdit_laser_measurement_data_save_filename.text().\
            replace("{d}", self.now.strftime(
            "%Y%m%d")).\
            replace("{t}", self.now.strftime("%H%M%S")).\
            replace("{m}", str(self.mode)).\
            replace("{l}", self.main.lineEdit_laser_measurement_data_save_filename_label.text())
        self.progress = 0
        self.angle_dict = self.get_calibration_dict_in_form()
        self.power_dict = None
        if self.mode == 4:
            self.power_dict = self.get_calibration_dict_angle_to_power_in_form()
        # print(self.angle_dict)
    def laser_measurement(self):
        if self.mode == 1 or self.mode == 2:
            self.laser_measurement_modes_1_2()
        else: # self.mode == 3 or 4
            self.laser_measurement_mode_3_4()

    def laser_measurement_modes_1_2(self):
        # print(self.curr_wavelength)
        if self.i == 0:
            self.fresh_new_start.emit()
        while self.i < self.number and self.main.laser_measurement_on:
            sleep(self.main.doubleSpinBox_laser_measurement_time.value())
            if self.i < self.number:
                self.curr_wavelength = self.starting_wavelength + self.i * self.step
            else:
                if self.curr_wavelength == self.ending_wavelength:
                    break
                else:
                    self.curr_wavelength = self.ending_wavelength

            key = str(np.round(self.curr_wavelength, 1))
            if self.mode == 1:
                # while self.main.laser_measurement_on:

                # print(key)
                # print(self.angle_dict)
                # print(self.angle_dict[key])
                if key not in self.angle_dict:
                    if self.main.label_warning_laser_measurement.text() == '':
                        self.main.label_warning_laser_measurement.setText('⚠\nPoint(s) Missing\nFrom Calibration')
                    # break
                else:
                    self.set_wavelength_mechanical(self.curr_wavelength)
                    next_angle = float(self.angle_dict[key])
                    self.set_angle_mechanical(next_angle)
                    # ndfilter_change = NDFilterChange(self.main, self.ndfilter_controller, next_angle)
                    # def progress_angle_update():
                    #     self.progress_angle = ndfilter_change.progress
                    #     self.progress_update_angle.emit()
                    # ndfilter_change.progress_update.connect(progress_angle_update)
                    # def progress_finished_angle_update():
                    #     self.curr_angle = ndfilter_change.angle
                    #     self.progress_finished_angle.emit()
                    # ndfilter_change.finished.connect(progress_finished_angle_update)
                    # self.main.laser_ndfilter_changing = True
                    # ndfilter_change.set_angle()
                    # self.main.laser_ndfilter_changing = False
            else: # mode 2
                self.set_wavelength_mechanical(self.curr_wavelength)
            if (self.mode == 1 and key in self.angle_dict) or self.mode == 2:
                # print('voltages', self.main.get_voltage_ch1_ch2())
                ch1_voltage, ch2_voltage = self.main.get_voltage_ch1_ch2()
                self.main.laser_measurement_line_trace['wavelength'].append(self.curr_wavelength)
                self.main.laser_measurement_line_trace['ch1'].append(ch1_voltage)
                self.main.laser_measurement_line_trace['ch2'].append(ch2_voltage)
            # self.update_form()
            self.progress = min(int((self.i + 1) * 100 / self.number), 100)
            # print(self.laser_controller.getWavelength())
            self.progress_finished_wavelength.emit()
            sleep(0.05)  # This time ensures that the calibration form updates with correct self.curr_wavelength in extreme cases
            self.i += 1

        if self.main.laser_measurement_on:
            # if self.curr_wavelength != self.ending_wavelength:
            #     self.curr_wavelength = self.ending_wavelength
            #     laserwavelength_change = LaserWavelengthChange(self.main, self.laser_controller, self.curr_wavelength)
            #     self.progress_wavelength = laserwavelength_change.progress
            #     laserwavelength_change.progress_update.connect(self.progress_update_wavelength.emit)
            #     self.main.laser_wavelength_changing = True
            #     laserwavelength_change.setWavelength()
            #     self.main.laser_wavelength_changing = False
            #     # print(laserwavelength_change.wavelength)
            #     self.progress_finished_wavelength.emit()
            df = pd.DataFrame({'wavelength (nm)': self.main.laser_measurement_line_trace['wavelength'],
                               'ch1 (V)': self.main.laser_measurement_line_trace['ch1'],
                               'ch2 (V)': self.main.laser_measurement_line_trace['ch2']})
            df.to_csv(self.main.lineEdit_laser_measurement_data_save_directory.text() + '/' + self.filename, index = False)
            self.finished.emit()
            # return
        self.moveToThread(self.main.mainThread)
        self.halted.emit()

    def laser_measurement_mode_3_4(self):
        if self.i == 0:
            self.fresh_new_start.emit()
        while self.i < self.number_angle and self.main.laser_measurement_on:
            sleep(self.main.doubleSpinBox_laser_measurement_time.value())
            if self.i < self.number_angle:
                self.curr_angle = self.starting_angle + self.i * self.step
            else:
                if self.curr_angle == self.ending_angle:
                    break
                else:
                    self.curr_angle = self.ending_angle
            curr_power = 0.0
            key = str(np.round(self.curr_angle, 2))
            if self.convert_angle_to_power_boolean:
                if key not in self.power_dict:
                    if self.main.label_warning_laser_measurement.text() == '':
                        self.main.label_warning_laser_measurement.setText('⚠\nPoint(s) Missing\nFrom Calibration')
                    # break
                else:
                    curr_power = float(self.power_dict[key])
                    self.set_angle_mechanical(self.curr_angle)
            else:
                self.set_angle_mechanical(self.curr_angle)
            # if (self.mode == 1 and key in self.power_dict) or self.mode == 2:
            #     # print('voltages', self.main.get_voltage_ch1_ch2())
            #     ch1_voltage, ch2_voltage = self.main.get_voltage_ch1_ch2()
            #     self.main.laser_measurement_line_trace['wavelength'].append(self.curr_wavelength)
            #     self.main.laser_measurement_line_trace['ch1'].append(ch1_voltage)
            #     self.main.laser_measurement_line_trace['ch2'].append(ch2_voltage)
            if self.convert_angle_to_power_boolean and key in self.power_dict:
                ch1_voltage, ch2_voltage = self.main.get_voltage_ch1_ch2()
                self.main.laser_measurement_line_trace['power'].append(curr_power)
                self.main.laser_measurement_line_trace['ch1'].append(ch1_voltage)
                self.main.laser_measurement_line_trace['ch2'].append(ch2_voltage)
            elif not self.convert_angle_to_power_boolean:
                ch1_voltage, ch2_voltage = self.main.get_voltage_ch1_ch2()
                self.main.laser_measurement_line_trace['angle'].append(self.curr_angle)
                self.main.laser_measurement_line_trace['ch1'].append(ch1_voltage)
                self.main.laser_measurement_line_trace['ch2'].append(ch2_voltage)
            # self.update_form()
            self.progress = min(int((self.i + 1) * 100 / self.number_angle), 100)
            # print(self.laser_controller.getWavelength())
            self.progress_finished_wavelength.emit()
            sleep(0.05)  # This time ensures that the calibration form updates with correct self.curr_wavelength in extreme cases
            self.i += 1

        if self.main.laser_measurement_on:
            if self.convert_angle_to_power_boolean:
                df = pd.DataFrame({'power (uW)': self.main.laser_measurement_line_trace['power'],
                                   'ch1 (V)': self.main.laser_measurement_line_trace['ch1'],
                                   'ch2 (V)': self.main.laser_measurement_line_trace['ch2']})
            else:
                df = pd.DataFrame({'angle (degree)': self.main.laser_measurement_line_trace['angle'],
                                   'ch1 (V)': self.main.laser_measurement_line_trace['ch1'],
                                   'ch2 (V)': self.main.laser_measurement_line_trace['ch2']})
            df.to_csv(self.main.lineEdit_laser_measurement_data_save_directory.text() + '/' + self.filename,
                      index=False)
            self.finished.emit()
            # return
        self.moveToThread(self.main.mainThread)
        self.halted.emit()

    def set_angle_mechanical(self, angle):
        ndfilter_change = NDFilterChange(self.main, self.ndfilter_controller, angle)

        def progress_angle_update():
            self.progress_angle = ndfilter_change.progress
            self.progress_update_angle.emit()

        ndfilter_change.progress_update.connect(progress_angle_update)

        def progress_finished_angle_update():
            self.curr_angle = ndfilter_change.angle
            self.progress_finished_angle.emit()

        ndfilter_change.finished.connect(progress_finished_angle_update)
        self.main.laser_ndfilter_changing = True
        ndfilter_change.set_angle()
        self.main.laser_ndfilter_changing = False

    def set_wavelength_mechanical(self, wavelength):
        laserwavelength_change = LaserWavelengthChange(self.main, self.laser_controller, wavelength)

        def progress_wavelength_update():
            self.progress_wavelength = laserwavelength_change.progress
            self.progress_update_wavelength.emit()

        laserwavelength_change.progress_update.connect(progress_wavelength_update)
        self.main.laser_wavelength_changing = True
        laserwavelength_change.setWavelength()
        self.progress_finished_wavelength_but_waiting_for_angle.emit()
        self.main.laser_wavelength_changing = False

    def get_calibration_dataframe_in_form(self):
        column_headers = ['Wavelength (nm)', 'ND Filter Angle (degree)', 'Power (uW)']
        # for j in range(self.tableWidget_laser_calibration.model().columnCount()):
        #     column_headers.append(self.tableWidget_laser_calibration.horizontalHeaderItem(j).text())
        df = pd.DataFrame(columns=column_headers)
        for row in range(self.main.tableWidget_laser_calibration.rowCount()):
            for col in range(self.main.tableWidget_laser_calibration.columnCount()):
                df.at[row, column_headers[col]] = self.main.tableWidget_laser_calibration.item(row, col).text()
        return df

    def get_calibration_dict_in_form(self):
        column_headers = ['Wavelength (nm)', 'ND Filter Angle (degree)', 'Power (uW)']
        df = self.get_calibration_dataframe_in_form()
        df.index = df.loc[:, column_headers[0]]
        df = df.drop(columns = [column_headers[0], column_headers[2]])
        # df = df.drop(columns=[column_headers[0]])
        return df.to_dict()[column_headers[1]]

    def get_calibration_dict_angle_to_power_in_form(self):
        column_headers = ['Wavelength (nm)', 'ND Filter Angle (degree)', 'Power (uW)']
        df = self.get_calibration_dataframe_in_form()
        df.index = df.loc[:, column_headers[1]]
        df = df.drop(columns = [column_headers[0], column_headers[1]])
        # df = df.drop(columns=[column_headers[1]])
        return df.to_dict()[column_headers[2]]