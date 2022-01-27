from datetime import datetime
from time import sleep

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal

from lib.topas4 import LaserWavelengthChange


class WavelengthSweep(QObject):
    halted = pyqtSignal()
    finished = pyqtSignal()
    fresh_new_start = pyqtSignal()
    progress_finished_wavelength_but_waiting_for_angle = pyqtSignal()
    progress_finished_wavelength = pyqtSignal()
    progress_finished_angle = pyqtSignal()
    progress_update_wavelength = pyqtSignal()
    progress_update_angle = pyqtSignal()
    def __init__(self, main, laser_controller, ndfilter_controller, powermeter):
        super(WavelengthSweep, self).__init__()
        self.laser_controller = laser_controller
        self.ndfilter_controller = ndfilter_controller
        self.powermeter = powermeter
        self.main = main
        self.starting_wavelength = self.main.doubleSpinBox_laser_measurement_wavelength_start.value()
        self.ending_wavelength = self.main.doubleSpinBox_laser_measurement_wavelength_end.value()
        self.step = self.main.doubleSpinBox_laser_measurement_step.value()
        self.number = (self.ending_wavelength - self.starting_wavelength) // self.step + 1
        self.curr_wavelength = 0
        self.i = 0
        self.now = datetime.now()
        self.mode = 1 if self.main.radioButton_laser_measurement_constant_power.isChecked() else 2
        self.filename = self.main.lineEdit_laser_measurement_data_save_filename.text().replace("{d}", self.now.strftime(
            "%Y%m%d")).replace("{t}", self.now.strftime("%H%M%S")).replace("{m}", str(self.mode))
        self.progress = 0

    def sweep_wavelength(self):
        print(self.curr_wavelength)
        if self.i == 0:
            self.fresh_new_start.emit()
        while self.i < self.number and self.main.laser_measurement_on:
            sleep(self.main.spinBox_laser_measurement_time.value())
            self.curr_wavelength = self.starting_wavelength + self.i * self.step
            laserwavelength_change = LaserWavelengthChange(self.main, self.laser_controller, self.curr_wavelength)
            def progress_wavelength_update():
                self.progress_wavelength = laserwavelength_change.progress
                self.progress_update_wavelength.emit()
            laserwavelength_change.progress_update.connect(progress_wavelength_update)
            self.main.laser_measurement_on = True
            laserwavelength_change.setWavelength()
            self.progress_finished_wavelength_but_waiting_for_angle.emit()
            self.main.laser_measurement_on = False
            while self.main.calibration_on:
                pass
            # self.update_form()
            self.progress = int((self.i + 1) * 100 / self.number)
            # print(self.laser_controller.getWavelength())
            self.progress_finished_wavelength.emit()
            sleep(0.05)  # This time ensures that the calibration form updates with correct self.curr_wavelength in extreme cases
            self.i += 1

        if self.main.calibration_on:
            if self.curr_wavelength != self.ending_wavelength:
                self.curr_wavelength = self.ending_wavelength
                laserwavelength_change = LaserWavelengthChange(self.main, self.laser_controller, self.curr_wavelength)
                self.progress_wavelength = laserwavelength_change.progress
                laserwavelength_change.progress_update.connect(self.progress_update_wavelength.emit)
                self.main.laser_wavelength_changing = True
                laserwavelength_change.setWavelength()
                self.main.laser_wavelength_changing = False
                # print(laserwavelength_change.wavelength)
                self.progress_finished_wavelength.emit()
            self.finished.emit()
            # return
        self.moveToThread(self.main.mainThread)
        self.halted.emit()