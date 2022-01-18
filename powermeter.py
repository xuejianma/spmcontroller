from PyQt5.QtCore import QObject, pyqtSignal
from pyvisa import ResourceManager
from time import sleep

label_error_text = "🚫 P0016683 Power Meter not Detected!"

class PowerMeter:
    def __init__(self):
        self.rm = ResourceManager()
        self.instrument = None
        usb_list = self.rm.list_resources()
        for item in usb_list:
            if "P0016683" in item:
                self.instrument = self.rm.open_resource(item)
                break
        if self.instrument is None:
            self.error()
    def error(self):
        print("P0016683 Power Meter Not Detected!")
    def getPower(self):
        return float(self.instrument.query('Measure:Scalar:POWer?'))

class PowerMeterRead(QObject):
    finished = pyqtSignal()
    def __init__(self, checkBox_read_power, lcdNumber_laser_power, lcdNumber_laser_power_uW, label_power_error):
        super(PowerMeterRead, self).__init__()
        self.checkBox_read_power = checkBox_read_power
        self.lcdNumber_laser_power = lcdNumber_laser_power
        self.lcdNumber_laser_power_uW = lcdNumber_laser_power_uW
        self.label_power_error = label_power_error
        self.curr_value = 0.0
        self.pm = PowerMeter()

    def updatePower(self):
        self.curr_value = self.pm.getPower()
        self.lcdNumber_laser_power.display(self.curr_value)
        self.lcdNumber_laser_power_uW.display(self.curr_value * 1e6)

    def run(self):
        while self.checkBox_read_power.isChecked():
            try:
                self.updatePower()
                sleep(0.1)
            except Exception as e:
                print(e)
                self.label_power_error.setText(label_error_text)
                self.checkBox_read_power.setChecked(False)
                break
        # self.close()
        self.finished.emit()


