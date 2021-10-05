import nidaqmx

label_error_text = "🚫 Hardware not connected properly"
class OutputVoltage:
    def __init__(self, port, label_error):
        self.label_error = label_error
        try:
            self.ratio = 15
            self.ports = {'x': "NIdevice/ao1", 'y': "NIdevice/ao2", 'z': "NIdevice/ao3"}
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
    def __init__(self, port, label_error):
        self.label_error = label_error
        try:
            self.ports = {'ch1': "NIdevice/ai1", 'ch2': "NIdevice/ai2"}
            self.task = nidaqmx.Task()
            self.task.ai_channels.add_ai_voltage_chan(self.ports[port])
        except:
            self.label_error.setText(label_error_text)
    def getVoltage(self):
        try:
            return self.task.read()
        except:
            self.label_error.setText(label_error_text)
            return 0.0
    def close(self):
        try:
            self.task.close()
        except:
            self.label_error.setText(label_error_text)
