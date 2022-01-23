from time import sleep

import requests
import sys

from PyQt5.QtCore import QObject, pyqtSignal, QThreadPool, QRunnable, QMutex

from Topas4Locator import Topas4Locator
# from time import sleep

class Topas4():

    def __init__(self, serialNumber="Orpheus-F-Demo-9302"):
        super(Topas4, self).__init__()
        locator = Topas4Locator()
        availableDevices = locator.locate()
        match = next((obj for obj in availableDevices if obj['SerialNumber'] == serialNumber), None)
        if match is None:
            print('Device with serial number %s not found' % serialNumber)
        else:
            self.baseAddress = match['PublicApiRestUrl_Version0']

    def put(self, url, data):
        return requests.put(self.baseAddress + url, json=data)

    def post(self, url, data):
        return requests.post(self.baseAddress + url, json=data)

    def get(self, url):
        return requests.get(self.baseAddress + url)



    def getWavelength(self):
        return self.get('/Optical/WavelengthControl/Output').json()["Wavelength"]

    def openShutter(self):
        self.put('/ShutterInterlock/OpenCloseShutter', True)

    def closeShutter(self):
        self.put('/ShutterInterlock/OpenCloseShutter', False)



class LaserWavelengthChange(QObject):
    finished = pyqtSignal()
    progress_update = pyqtSignal()
    def __init__(self, parent, laser_controller, wavelength):
        # self._mutex = QMutex()
        # self._mutex.lock()
        super(LaserWavelengthChange, self).__init__()
        self.laser_controller = laser_controller
        self.wavelength = wavelength
        self.progress = 100
        self.parent = parent
        # self._mutex.unlock()

    def put(self, url, data):
        return self.laser_controller.put(url, data)

    def get(self, url):
        return self.laser_controller.get(url)

    def setWavelength(self):
        # self._mutex.lock()
        self.put('/Optical/WavelengthControl/SetWavelengthUsingAnyInteraction', self.wavelength)
        self.waitTillWavelengthIsSet()
        # self._mutex.unlock()
        self.finished.emit()


    def waitTillWavelengthIsSet(self):
        """
        Waits till wavelength setting is finished.  If user needs to do any manual
        operations (e.g.  change wavelength separator), inform him/her and wait for confirmation.
        """
        while (True):
            sleep(0.1)  # to avoid too fast http requests
            if not self.parent.laser_wavelength_changing:
                self.progress = 100
                self.progress_update.emit()
                return
            s = self.get('/Optical/WavelengthControl/Output').json()
            # sys.stdout.write("\r %d %% done" % (s['WavelengthSettingCompletionPart'] * 100.0))
            # if self.progressBar_wavelength is not None:
            #     self.progressBar_wavelength.setValue(int(s['WavelengthSettingCompletionPart'] * 100.0))
            self.progress = int(s['WavelengthSettingCompletionPart'] * 100.0)
            self.progress_update.emit()

            if s['IsWavelengthSettingInProgress'] == False or s['IsWaitingForUserAction']:
                break
            # sleep(0.1)
        state = self.get('/Optical/WavelengthControl/Output').json()
        if state['IsWaitingForUserAction']:
            # print("\nUser actions required. Press enter key to confirm.")
            # inform user what needs to be done
            # for item in state['Messages']:
            #     print(item['Text'] + ' ' + ('' if item['Image'] is None else ', image name: ' + item['Image']))
            # sys.stdin.read(1)  # wait for user confirmation
            # tell the device that required actions have been performed.  If shutter was open before setting wavelength it will be opened again
            self.put('/Optical/WavelengthControl/FinishWavelengthSettingAfterUserActions', {'RestoreShutter': True})
        print("Done setting wavelength")
