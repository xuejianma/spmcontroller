import nidaqmx
from PyQt5.QtCore import QObject, pyqtSignal, QMutex
from nidaqmx.stream_readers import AnalogMultiChannelReader, AnalogSingleChannelReader
import time
import json


nidevice_port_name = "NIdevice"
try:
    with open('../config.json') as f:
        data = json.load(f)
    nidevice_port_name = data['nidevice_port_name']
    print("nidevice_port_name_substitute changed to {}".format(nidevice_port_name))
except:
    print("No config.json found in ../")
label_error_text = "🚫 Hardware not connected properly"
class OutputVoltage:
    def __init__(self, port, label_error, ratio = 15):
        self.label_error = label_error
        self.ratio = ratio
        try:
            self.ports = {'encoder': nidevice_port_name + "/ao0", 'x': nidevice_port_name + "/ao1",
                          'y': nidevice_port_name + "/ao2", 'z': nidevice_port_name + "/ao3"}
            self.task = nidaqmx.Task()
            self.task.ao_channels.add_ao_voltage_chan(self.ports[port])
        except:
            self.label_error.setText(label_error_text)
    def outputVoltage(self, voltage):
        try:
            self.task.write(voltage / self.ratio)
        except:
            self.label_error.setText(label_error_text)

    def close(self):
        try:
            self.task.close()
        except:
            self.label_error.setText(label_error_text)


class OutputVoltageXYZ:
    def __init__(self, label_error, ratio = 15):
        self.label_error = label_error
        self.ratio = ratio
        try:
            self.ports = {'encoder': nidevice_port_name + "/ao0", 'x': nidevice_port_name + "/ao1",
                          'y': nidevice_port_name + "/ao2", 'z': nidevice_port_name + "/ao3"}
            self.task = nidaqmx.Task()
            self.task.ao_channels.add_ao_voltage_chan(self.ports['x'])
            self.task.ao_channels.add_ao_voltage_chan(self.ports['y'])
            self.task.ao_channels.add_ao_voltage_chan(self.ports['z'])
        except:
            self.label_error.setText(label_error_text)
    def outputVoltage(self, voltage_xyz_array):
        try:
            voltage_xyz_array_output = [item / self.ratio for item in voltage_xyz_array]
            self.task.write(voltage_xyz_array_output, auto_start = True)
        except:
            self.label_error.setText(label_error_text)

    def close(self):
        try:
            self.task.close()
        except:
            self.label_error.setText(label_error_text)

mutex = QMutex()
class InputVoltage:
    def __init__(self, label_error):
        self.label_error = label_error
        self.pre_ch1 = 0.0
        self.pre_ch2 = 0.0
        try:
            self.ports = {'ch1': nidevice_port_name + "/ai1", 'ch2': nidevice_port_name + "/ai2",
                          'encoder' : nidevice_port_name + "/ai3"}
            self.task = nidaqmx.Task()
            self.task.ai_channels.add_ai_voltage_chan(self.ports['ch1'])
            self.task.ai_channels.add_ai_voltage_chan(self.ports['ch2'])
            self.reader = AnalogMultiChannelReader(self.task.in_stream)
        except:
            self.label_error.setText(label_error_text)
    def getVoltage(self):
        try:
            # t1 = time()
            mutex.lock()
            vals = self.task.read()
            mutex.unlock()
            self.pre_ch1, self.pre_ch2 = vals
            return vals
            # print(time() - t1)
            # return val
            # return 0
            # return self.task.read()
            # return self.reader.read_one_sample()
        except:
            self.label_error.setText(label_error_text)
            print("Hardware not loaded / Missing data point due to conflict of ch1_ch2 and encoder reading at the same time.")
            return [self.pre_ch1, self.pre_ch2]
    def close(self):
        try:
            self.task.close()
        except:
            self.label_error.setText(label_error_text)


class InputVoltageEncoder(QObject):
    finished = pyqtSignal()
    # update = pyqtSignal()
    def __init__(self, label_error, lcdNumber_encoder_reading, checkBox_encoder_reading):
        super(InputVoltageEncoder, self).__init__()
        self.label_error = label_error
        self.curr_value = 0.0
        self.lcdNumber_encoder_reading = lcdNumber_encoder_reading
        self.checkBox_encoder_reading = checkBox_encoder_reading
        self.label_error.setText("")
        try:
            self.ports = {'encoder' : nidevice_port_name + "/ai3"}
            self.task = nidaqmx.Task()
            self.task.ai_channels.add_ai_voltage_chan(self.ports['encoder'])
            self.reader = AnalogSingleChannelReader(self.task.in_stream)
        except:
            self.label_error.setText(label_error_text)
    def getVoltage(self):
        mutex.lock()
        self.curr_value = self.task.read() * 1000
        mutex.unlock()
        # print(self.curr_value)
        self.lcdNumber_encoder_reading.display(self.curr_value)
        
        # self.update.emit()


    def run(self):
        while self.checkBox_encoder_reading.isChecked():
            try:
                self.getVoltage()
                time.sleep(1)
            except:
                self.label_error.setText(label_error_text)
                self.checkBox_encoder_reading.setChecked(False)
                break
        self.close()
        self.finished.emit()

    def close(self):
        try:
            self.task.close()
        except:
            self.label_error.setText(label_error_text)