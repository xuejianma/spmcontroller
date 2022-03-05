from time import sleep

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal

from lib.ndfiltercontroller import NDFilterChange
from lib.topas4 import LaserWavelengthChange
from util.powerconverge import power_converge


class PowerCalibration(QObject):
    halted = pyqtSignal()
    finished = pyqtSignal()
    fresh_new_start = pyqtSignal()
    progress_finished_wavelength_but_waiting_for_angle = pyqtSignal()
    progress_finished_wavelength = pyqtSignal()
    progress_finished_angle = pyqtSignal()
    progress_update_wavelength = pyqtSignal()
    progress_update_angle = pyqtSignal()


    def __init__(self, main, laser_controller, ndfilter_controller, powermeter):
        super(PowerCalibration, self).__init__()
        self.laser_controller = laser_controller
        self.ndfilter_controller = ndfilter_controller
        self.powermeter = powermeter
        self.main = main
        self.starting_wavelength = self.main.doubleSpinBox_laser_calibration_wavelength_start.value()
        self.ending_wavelength = self.main.doubleSpinBox_laser_calibration_wavelength_end.value()
        self.target_power = self.main.doubleSpinBox_laser_calibration_target_power_uW.value()
        self.mode = 'A' if self.main.tabWidget_laser_calibration.currentIndex() == 0 else 'B'
        # self.step = self.main.doubleSpinBox_laser_calibration_step.value() if self.mode == 'A' \
        #     else self.main.doubleSpinBox_laser_calibration_step_sweep_power.value()
        self.lowest_angle = self.main.doubleSpinBox_laser_calibration_lowest_angle.value()
        self.highest_angle = self.main.doubleSpinBox_laser_calibration_highest_angle.value()
        self.starting_angle = self.main.doubleSpinBox_laser_calibration_starting_angle.value()
        self.ending_angle = self.main.doubleSpinBox_laser_calibration_ending_angle.value()
        if self.mode == 'A':
            self.step = self.main.doubleSpinBox_laser_calibration_step.value()
            if self.starting_wavelength > self.ending_wavelength:
                self.step = -self.step
        else:
            self.step = self.main.doubleSpinBox_laser_calibration_step_sweep_power.value()
            if self.starting_angle > self.ending_angle:
                self.step = -self.step
        self.number = abs(self.ending_wavelength - self.starting_wavelength) // abs(self.step) + 1
        self.number_angle = abs(self.ending_angle - self.starting_angle) // abs(self.step) + 1
        self.i = 0
        self.curr_wavelength = 0
        self.curr_angle = 0 #self.main.doubleSpinBox_laser_calibration_highest_current.value()
        self.progress = 0
        self.progress_wavelength = 100
        self.progress_angle = 100

        # print("tab status: ", self.main.tabWidget_laser_calibration.currentIndex())

    def sweep_wavelength(self):
        if self.mode == 'A':
            self.sweep_wavelength_mode_A()
        else:
            self.sweep_wavelength_mode_B()

    def sweep_wavelength_mode_A(self):
        # self.progress = 0
        # self.reset_form()
        # self.progress_finished_wavelength.emit()
        # print("finnaly it works!", self.parent.mainThread)
        if self.i == 0:
            self.fresh_new_start.emit()
        while self.i <= self.number and self.main.calibration_on:
            sleep(self.main.doubleSpinBox_laser_calibration_time.value())
            if self.i < self.number:
                self.curr_wavelength = self.starting_wavelength + self.i * self.step
            else:
                if self.curr_wavelength == self.ending_wavelength:
                    break
                else:
                    self.curr_wavelength = self.ending_wavelength
            laserwavelength_change = LaserWavelengthChange(self.main, self.laser_controller, self.curr_wavelength)
            def progress_wavelength_update():
                self.progress_wavelength = laserwavelength_change.progress
                self.progress_update_wavelength.emit()
            laserwavelength_change.progress_update.connect(progress_wavelength_update)
            self.main.laser_wavelength_changing = True
            laserwavelength_change.setWavelength()
            is_shutter_open = self.laser_controller.get('/ShutterInterlock/IsShutterOpen').json()
            if not is_shutter_open:
                self.main.checkBox_laser_shutter.setChecked(True)
                sleep(1)
            self.progress_finished_wavelength_but_waiting_for_angle.emit()
            self.main.laser_wavelength_changing = False
            while self.main.calibration_on:
                # print('angle changing')
                next_angle = np.round(power_converge(self.ndfilter_controller.get_angle(),
                                                     self.powermeter.get_power_uW(), self.target_power), 2)
                # print(next_angle)
                if next_angle > self.highest_angle or next_angle < self.lowest_angle or \
                        abs(self.powermeter.get_power_uW() - self.target_power) < \
                        self.target_power * self.main.doubleSpinBox_laser_calibration_tolerance.value() * 0.01:
                    break
                ndfilter_change = NDFilterChange(self.main, self.ndfilter_controller, next_angle)
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
                # break
            # self.update_form()
            self.progress = min(int((self.i + 1) * 100 / self.number), 100)
            # print(self.laser_controller.getWavelength())
            self.progress_finished_wavelength.emit()
            sleep(0.05)  # This time ensures that the calibration form updates with correct self.curr_wavelength in extreme cases
            self.i += 1

        if self.main.calibration_on:
            # if self.curr_wavelength != self.ending_wavelength:
            #     self.curr_wavelength = self.ending_wavelength
            #     laserwavelength_change = LaserWavelengthChange(self.main, self.laser_controller, self.curr_wavelength)
            #     self.progress_wavelength = laserwavelength_change.progress
            #     laserwavelength_change.progress_update.connect(self.progress_update_wavelength.emit)
            #     self.main.laser_wavelength_changing = True
            #     laserwavelength_change.setWavelength()
            #     self.main.laser_wavelength_changing = False
            # # print(laserwavelength_change.wavelength)
            #     self.progress_finished_wavelength.emit()
            self.finished.emit()
            # return
        self.moveToThread(self.main.mainThread)
        self.halted.emit()

    def sweep_wavelength_mode_B(self):
        if self.i == 0:
            self.fresh_new_start.emit()
        while self.i <= self.number_angle and self.main.calibration_on:
            sleep(self.main.doubleSpinBox_laser_calibration_time.value())
            if self.i < self.number_angle:
                self.curr_angle = self.starting_angle + self.i * self.step
            else:
                if self.curr_angle == self.curr_angle:
                    break
                else:
                    self.curr_angle = self.curr_angle
            next_angle = self.curr_angle
            ndfilter_change = NDFilterChange(self.main, self.ndfilter_controller, next_angle)
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
            self.progress = min(int((self.i + 1) * 100 / self.number_angle), 100)
            self.progress_finished_wavelength.emit()
            sleep(0.05)  # This time ensures that the calibration form updates with correct self.curr_wavelength in extreme cases
            self.i += 1
        if self.main.calibration_on:
            self.finished.emit()
        self.moveToThread(self.main.mainThread)
        self.halted.emit()





    # def put(self, url, data):
    #     return self.laser_controller.put(url, data)
    #
    # def get(self, url):
    #     return self.laser_controller.get(url)
    #
    # def setWavelength(self, wavelength):
    #     self.put('/Optical/WavelengthControl/SetWavelengthUsingAnyInteraction', wavelength)
    #     self.waitTillWavelengthIsSet()
    #     # self.finished.emit()
    #
    # def waitTillWavelengthIsSet(self):
    #     """
    #     Waits till wavelength setting is finished.  If user needs to do any manual
    #     operations (e.g.  change wavelength separator), inform him/her and wait for confirmation.
    #     """
    #     while (True):
    #         sleep(0.1) # to avoid too fast http requests
    #         s = self.get('/Optical/WavelengthControl/Output').json()
    #         self.progress = int(s['WavelengthSettingCompletionPart'] * 100.0)
    #         if s['IsWavelengthSettingInProgress'] == False or s['IsWaitingForUserAction']:
    #             break
    #     state = self.get('/Optical/WavelengthControl/Output').json()
    #     if state['IsWaitingForUserAction']:
    #         self.put('/Optical/WavelengthControl/FinishWavelengthSettingAfterUserActions', {'RestoreShutter': True})
    #     # print("Done setting wavelength")
