from pyvisa import ResourceManager
from PyQt5.QtCore import QObject, pyqtSignal
import time
import numpy as np

label_error_text = "🚫 Error: Oscilloscope (DS6D150100004) Load Error!"

class Oscilloscope():
    def __init__(self):
        self.rm = ResourceManager()
        self.instrument = None
        usb_list = self.rm.list_resources()
        print(usb_list)
        for item in usb_list:
            if "DS6D150100004" in item:
                self.instrument = self.rm.open_resource(item)
                break
        if self.instrument is None:
            self.error()
        self.x_scale = None
        self.y_scale = None
    
    def error(self):
        raise ValueError()

    def start(self):
        self.instrument.write(":RUN")
    
    def stop(self):
        self.instrument.write(":STOP")
    
    def get_data(self, loading_time, label_oscilloscope_error, start=1, points=70000000,):
        try:
            self.start()
            time.sleep(loading_time)
            self.stop()
            wt = 0.01
            self.instrument.write(":WAV:MODE NORM")  # RAW means deeper raw data. NORM means displayed data
            time.sleep(wt)
            self.instrument.write(":WAV:STAR " + str(start))
            time.sleep(wt)
            self.instrument.write(":WAV:STOP " + str(points + start))
            time.sleep(wt)
            self.instrument.write(":WAV:POIN " + str(points))
            time.sleep(wt)
            self.instrument.write(":WAV:SOUR CHAN1")
            time.sleep(wt)
            self.instrument.write(":WAV:RES")
            time.sleep(wt)
            self.instrument.write(":WAV:BEG")
            time.sleep(wt)            
            self.x_scale = float(self.instrument.query(':TIM:SCAL?'))
            time.sleep(wt)
            self.y_scale = float(self.instrument.query(':CHAN1:SCAL?'))
            time.sleep(wt)          
            rawdata = self.instrument.query_binary_values(':WAV:DATA?', datatype='B', is_big_endian=False)
            # print(rawdata)
            return (np.linspace(0, self.x_scale * 14, len(rawdata), endpoint=False), np.asarray(rawdata) * (self.y_scale/(256/8)))
            # print("data...")
            # print(len(rawdata), rawdata)
        except Exception as e:
            print(e)
            self.instrument = None
            label_oscilloscope_error.setText(label_error_text)
        # if self.currTurn % 2 == 0:
        #     self.on_list.append(rawdata)
        #     print('onlist append')
        # else:
        #     self.off_list.append(rawdata)
        #     print('offlist append')
        #     self.label_turnsLeft.setText('Turns Finished: ' + str(int(np.floor((self.currTurn+1)/2))) + '/' + str(int(self.steps)))
        #     # QTimer.singleShot(500,self.plotDecay)
        #     # QTimer.singleShot(500,lambda:print('plotDecay'))
        # self.currTurn += 1


class OscilloscopeRead(QObject):
    finished = pyqtSignal()
    def __init__(self, oscilloscope, label_oscilloscope_error):
        super(OscilloscopeRead, self).__init__()
        self.oscilloscope = oscilloscope
        self.label_oscilloscope_error = label_oscilloscope_error
    
    def run(self):
        try:
            time_list, data = self.oscilloscope.get_data(loading_time=1, label_oscilloscope_error = self.label_oscilloscope_error)
            print(time_list, data)
        except Exception as e:
            print(e)
            self.label_oscilloscope_error.setText(label_error_text)
        self.finished.emit()
    

if __name__ == "__main__":
    osc = Oscilloscope()
    xx, data = osc.get_data(loading_time=1, label_oscilloscope_error = None)
    print(xx, min(data), max(data), max(data) - min(data))