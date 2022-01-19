from PyQt5.QtCore import QObject
import numpy as np


class PowerCalibration(QObject):
    def __init__(self, parent, laser_controller, ndfilter_controller, powermeter):
        self.laser_controller = laser_controller
        self.ndfilter_controller = ndfilter_controller
        self.powermeter = powermeter
        self.parent = parent
        self.starting_wavelength = self.parent.spinBox_laser_calibration_wavelength_start.value()
        self.ending_wavelength = self.parent.spinBox_laser_calibration_wavelength_end.value()
        self.number = (self.ending_wavelength - self.starting_wavelength) // self.step
        self.i = 0
        self.curr_wavelength = 0

    def sweep_wavelength(self):
        while self.i < self.number:
            self.curr_wavelength = self.starting_wavelength + self.i * self.step
            self.setWavelength(self.starting_wavelength)
            

    def put(self, url, data):
        return self.laser_controller.put(url, data)

    def get(self, url):
        return self.laser_controller.get(url)

    def setWavelength(self, wavelength):
        self._mutex.lock()
        self.put('/Optical/WavelengthControl/SetWavelengthUsingAnyInteraction', wavelength)
        self.waitTillWavelengthIsSet()
        self._mutex.unlock()
        self.finished.emit()

    def waitTillWavelengthIsSet(self):
        """
        Waits till wavelength setting is finished.  If user needs to do any manual
        operations (e.g.  change wavelength separator), inform him/her and wait for confirmation.
        """
        while (True):
            s = self.get('/Optical/WavelengthControl/Output').json()
            self.progress = int(s['WavelengthSettingCompletionPart'] * 100.0)
            if s['IsWavelengthSettingInProgress'] == False or s['IsWaitingForUserAction']:
                break
        state = self.get('/Optical/WavelengthControl/Output').json()
        if state['IsWaitingForUserAction']:
            self.put('/Optical/WavelengthControl/FinishWavelengthSettingAfterUserActions', {'RestoreShutter': True})
        print("Done setting wavelength")