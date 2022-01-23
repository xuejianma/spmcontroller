from time import sleep

from PyQt5.QtCore import QObject, pyqtSignal, QThread


class PowerCalibration(QObject):
    halted = pyqtSignal()
    finished = pyqtSignal()
    progress_update = pyqtSignal()

    def __init__(self, parent, laser_controller, ndfilter_controller, powermeter):
        super(PowerCalibration, self).__init__()
        self.laser_controller = laser_controller
        self.ndfilter_controller = ndfilter_controller
        self.powermeter = powermeter
        self.parent = parent
        self.starting_wavelength = self.parent.spinBox_laser_calibration_wavelength_start.value()
        self.ending_wavelength = self.parent.spinBox_laser_calibration_wavelength_end.value()
        self.step = self.parent.spinBox_laser_calibration_step.value()
        self.number = (self.ending_wavelength - self.starting_wavelength) // self.step
        self.i = 0
        self.curr_wavelength = 0
        self.progress = 0

    def sweep_wavelength(self):
        self.progress_update.emit()
        print("finnaly it works!", self.parent.mainThread)
        while self.i < self.number and self.parent.calibration_on:
            self.curr_wavelength = self.starting_wavelength + self.i * self.step
            self.progress = int((self.i + 1) * 100 / self.number)
            self.progress_update.emit()
            self.setWavelength(self.curr_wavelength)
            self.i += 1

        if self.parent.calibration_on:
            self.setWavelength(self.ending_wavelength)
            self.progress_update.emit()
            self.finished.emit()
            # return
        self.moveToThread(self.parent.mainThread)
        self.halted.emit()


    def put(self, url, data):
        return self.laser_controller.put(url, data)

    def get(self, url):
        return self.laser_controller.get(url)

    def setWavelength(self, wavelength):
        self.put('/Optical/WavelengthControl/SetWavelengthUsingAnyInteraction', wavelength)
        self.waitTillWavelengthIsSet()
        # self.finished.emit()

    def waitTillWavelengthIsSet(self):
        """
        Waits till wavelength setting is finished.  If user needs to do any manual
        operations (e.g.  change wavelength separator), inform him/her and wait for confirmation.
        """
        while (True):
            sleep(0.1) # to avoid too fast http requests
            s = self.get('/Optical/WavelengthControl/Output').json()
            self.progress = int(s['WavelengthSettingCompletionPart'] * 100.0)
            if s['IsWavelengthSettingInProgress'] == False or s['IsWaitingForUserAction']:
                break
        state = self.get('/Optical/WavelengthControl/Output').json()
        if state['IsWaitingForUserAction']:
            self.put('/Optical/WavelengthControl/FinishWavelengthSettingAfterUserActions', {'RestoreShutter': True})
        # print("Done setting wavelength")