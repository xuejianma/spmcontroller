import nidaqmx
from PyQt5.QtCore import QObject, pyqtSignal
from nidaqmx.stream_readers import AnalogMultiChannelReader, AnalogSingleChannelReader
import time


label_error_text = "🚫 Hardware not connected properly"
class OutputVoltage:
    def __init__(self, port, label_error, ratio = 15):
        self.label_error = label_error
        self.ratio = ratio
        try:
            self.ports = {'encoder': "NIdevice/ao0", 'x': "NIdevice/ao1", 'y': "NIdevice/ao2", 'z': "NIdevice/ao3"}
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

class InputVoltage:
    def __init__(self, label_error):
        self.label_error = label_error
        self.pre_ch1 = 0.0
        self.pre_ch2 = 0.0
        try:
            self.ports = {'ch1': "NIdevice/ai1", 'ch2': "NIdevice/ai2", 'encoder' : "NIdevice/ai3"}
            self.task = nidaqmx.Task()
            self.task.ai_channels.add_ai_voltage_chan(self.ports['ch1'])
            self.task.ai_channels.add_ai_voltage_chan(self.ports['ch2'])
            self.reader = AnalogMultiChannelReader(self.task.in_stream)
        except:
            self.label_error.setText(label_error_text)
    def getVoltage(self):
        try:
            # t1 = time.time()
            vals = self.task.read()
            self.pre_ch1, self.pre_ch2 = vals
            return vals
            # print(time.time() - t1)
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
    update = pyqtSignal()
    def __init__(self, label_error, lcdNumber_encoder_reading, checkBox_encoder_reading):
        super(InputVoltageEncoder, self).__init__()
        self.label_error = label_error
        self.curr_value = 0.0
        self.lcdNumber_encoder_reading = lcdNumber_encoder_reading
        self.checkBox_encoder_reading = checkBox_encoder_reading
        try:
            self.ports = {'encoder' : "NIdevice/ai3"}
            self.task = nidaqmx.Task()
            self.task.ai_channels.add_ai_voltage_chan(self.ports['encoder'])
            self.reader = AnalogSingleChannelReader(self.task.in_stream)
        except:
            self.label_error.setText(label_error_text)
    def getVoltage(self):
        try:
            self.curr_value = self.task.read() * 1000
            # print(self.curr_value)
            self.lcdNumber_encoder_reading.display(self.curr_value)
            self.update.emit()
        except:
            self.label_error.setText(label_error_text)
            # return 0.0

    def run(self):
        while self.checkBox_encoder_reading.isChecked():
            self.getVoltage()
            time.sleep(1)
        self.close()
        self.finished.emit()

    def close(self):
        try:
            self.task.close()
        except:
            self.label_error.setText(label_error_text)