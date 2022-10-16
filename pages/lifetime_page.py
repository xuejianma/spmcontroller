from lib.oscilloscope import Oscilloscope, OscilloscopeRead, label_error_text
from PyQt5.QtCore import QThread

class LifetimePage():
    def reconnect_oscilloscope(self):
        self.label_oscilloscope_error.setText("")
        try:
            self.oscilloscope = Oscilloscope()
        except:
            self.oscilloscope = None
            self.label_oscilloscope_error.setText(label_error_text)
            
    def start_lifetime(self):
        print("starting...")
        if not self.oscilloscope:
            self.label_oscilloscope_error.setText(label_error_text)
            return
        try:
            self.thread_lifetime = QThread()
            self.oscilloscope_read = OscilloscopeRead(oscilloscope=self.oscilloscope, label_oscilloscope_error=self.label_oscilloscope_error)
            self.oscilloscope_read.moveToThread(self.thread_lifetime)
            self.thread_lifetime.started.connect(self.oscilloscope_read.run)
            self.oscilloscope_read.finished.connect(self.oscilloscope_read.deleteLater)
            self.oscilloscope_read.finished.connect(self.thread_lifetime.exit)
            self.thread_lifetime.finished.connect(self.thread_lifetime.deleteLater)
            self.thread_lifetime.start()
        except Exception as e:
            print(e)
            self.label_oscilloscope_error.setText(label_error_text)
        print("ended...")
