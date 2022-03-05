from PyQt5.QtCore import QObject, pyqtSignal
from pyvisa import ResourceManager
from time import sleep

label_error_text = "🚫 Error: Power Meter not detected!"

# class PowerMeter:
#     def __init__(self):
#         self.rm = ResourceManager()
#         self.instrument = None
#         usb_list = self.rm.list_resources()
#         # print(usb_list)
#         for item in usb_list:
#             if "P0016683" in item:
#                 self.instrument = self.rm.open_resource(item)
#                 break
#         if self.instrument is None:
#             self.error()
#     def error(self):
#         raise ValueError()
#     def get_power(self):
#         return float(self.instrument.query('Measure:Scalar:POWer?'))
#     def get_power_uW(self):
#         return self.get_power() * 1e6

# class PowerMeterRead(QObject):
#     finished = pyqtSignal()
#     def __init__(self, powermeter, checkBox_read_power, lcdNumber_laser_power, lcdNumber_laser_power_uW, label_power_error):
#         super(PowerMeterRead, self).__init__()
#         self.checkBox_read_power = checkBox_read_power
#         self.lcdNumber_laser_power = lcdNumber_laser_power
#         self.lcdNumber_laser_power_uW = lcdNumber_laser_power_uW
#         self.label_power_error = label_power_error
#         self.curr_value = 0.0
#         self.powermeter = powermeter

#     def updatePower(self):
#         self.curr_value = self.powermeter.get_power()
#         self.lcdNumber_laser_power.display(self.curr_value)
#         self.lcdNumber_laser_power_uW.display(self.curr_value * 1e6)

#     def run(self):
#         self.label_power_error.setText("")
#         while self.checkBox_read_power.isChecked():
#             try:
#                 self.updatePower()
#                 sleep(0.1)
#             except Exception as e:
#                 print(e)
#                 self.powermeter = None
#                 self.label_power_error.setText(label_error_text)
#                 self.checkBox_read_power.setEnabled(False)
#                 #
#                 self.checkBox_read_power.blockSignals(True)
#                 self.checkBox_read_power.setChecked(False)
#                 self.checkBox_read_power.blockSignals(False)
#                 break
#         # self.close()
#         self.finished.emit()


# class PowerMeter:
#     def __init__(self, parent):
#         self.parent = parent
#     def get_power(self):
#         # return float(self.instrument.query('Measure:Scalar:POWer?'))
#         return self.simulate_power(self.parent.laser_controller.getWavelength(), self.parent.ndfilter_controller.get_angle())

#     def get_power_uW(self):
#         return self.get_power() * 1e6
#     def simulate_power(self, wavelength, angle):
#         return 1.0e-4 * (1.0e-4 * (wavelength - 500) ** 2 + 1) * (360 - angle)/360


# class PowerMeterRead(QObject):
#     finished = pyqtSignal()
#     def __init__(self, powermeter, checkBox_read_power, lcdNumber_laser_power, lcdNumber_laser_power_uW, label_power_error):
#         super(PowerMeterRead, self).__init__()
#         self.checkBox_read_power = checkBox_read_power
#         self.lcdNumber_laser_power = lcdNumber_laser_power
#         self.lcdNumber_laser_power_uW = lcdNumber_laser_power_uW
#         self.label_power_error = label_power_error
#         self.curr_value = 0.0
#         self.powermeter = powermeter

#     def updatePower(self):
#         self.curr_value = self.powermeter.get_power()
#         self.lcdNumber_laser_power.display(self.curr_value)
#         self.lcdNumber_laser_power_uW.display(self.curr_value * 1e6)

#     def run(self):
#         self.label_power_error.setText("")
#         while self.checkBox_read_power.isChecked():
#             try:
#                 self.updatePower()
#                 sleep(0.1)
#             except Exception as e:
#                 print(e)
#                 self.powermeter = None
#                 self.label_power_error.setText(label_error_text)
#                 self.checkBox_read_power.setEnabled(False)
#                 self.checkBox_read_power.blockSignals(True)
#                 self.checkBox_read_power.setChecked(False)
#                 self.checkBox_read_power.blockSignals(False)
#                 break
#         # self.close()
#         self.finished.emit()



class PowerMeter:

    def get_power(self):
        # return float(self.instrument.query('Measure:Scalar:POWer?'))
        return 1.0

    def get_power_uW(self):
        return self.get_power() * 1e6
    def simulate_power(self, wavelength, angle):
        return 1.0e-4 * (1.0e-4 * (wavelength - 500) ** 2 + 1) * (360 - angle)/360


class PowerMeterRead(QObject):
    finished = pyqtSignal()
    def __init__(self, powermeter, checkBox_read_power, lcdNumber_laser_power, lcdNumber_laser_power_uW, label_power_error):
        super(PowerMeterRead, self).__init__()
        self.checkBox_read_power = checkBox_read_power
        self.lcdNumber_laser_power = lcdNumber_laser_power
        self.lcdNumber_laser_power_uW = lcdNumber_laser_power_uW
        self.label_power_error = label_power_error
        self.curr_value = 0.0
        self.powermeter = powermeter

    def updatePower(self):
        self.curr_value = self.powermeter.get_power()
        self.lcdNumber_laser_power.display(self.curr_value)
        self.lcdNumber_laser_power_uW.display(self.curr_value * 1e6)

    def run(self):
        self.label_power_error.setText("")
        while self.checkBox_read_power.isChecked():
            try:
                self.updatePower()
                sleep(0.1)
            except Exception as e:
                print(e)
                self.powermeter = None
                self.label_power_error.setText(label_error_text)
                self.checkBox_read_power.setEnabled(False)
                self.checkBox_read_power.blockSignals(True)
                self.checkBox_read_power.setChecked(False)
                self.checkBox_read_power.blockSignals(False)
                break
        # self.close()
        self.finished.emit()