from lib.oscilloscope import Oscilloscope, OscilloscopeRead, label_error_text
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QFileDialog
import numpy as np
from datetime import datetime
from pandas import DataFrame


class LifetimePage:
    def reconnect_oscilloscope(self):
        self.label_oscilloscope_error.setText("")
        try:
            self.oscilloscope = Oscilloscope()
        except:
            self.oscilloscope = None
            self.label_oscilloscope_error.setText(label_error_text)
        self.time_list = []
        self.data = []
        self.averaged_data = []

    def start_lifetime(self):
        print("starting...")
        if not self.oscilloscope:
            self.label_oscilloscope_error.setText(label_error_text)
            return
        try:
            self.thread_lifetime = QThread()
            self.oscilloscope_read = OscilloscopeRead(oscilloscope=self.oscilloscope, loading_time = self.doubleSpinBox_lifetime_loading_time.value(), label_oscilloscope_error=self.label_oscilloscope_error, repetition_num=self.spinBox_oscilloscope_repetition_num.value(),
                                                      time_list=self.time_list, data=self.data)
            self.oscilloscope_read.moveToThread(self.thread_lifetime)
            self.thread_lifetime.started.connect(self.oscilloscope_read.run)
            self.oscilloscope_read.finished.connect(
                self.oscilloscope_read.deleteLater)
            self.oscilloscope_read.finished.connect(self.thread_lifetime.exit)
            self.oscilloscope_read.finished.connect(self.save_lifetime_with_dialog)
            self.oscilloscope_read.update.connect(self.plot_lifetime)
            self.thread_lifetime.finished.connect(
                self.thread_lifetime.deleteLater)
            self.thread_lifetime.start()
        except Exception as e:
            print(e)
            self.label_oscilloscope_error.setText(label_error_text)
        print("ended...")

    def plot_lifetime(self):
        self.widget_lifetime_current.clear()
        self.widget_lifetime_averaged.clear()
        self.widget_lifetime_current.plot(self.time_list, self.data[-1])
        self.averaged_data = np.average(self.data, axis=0)
        self.widget_lifetime_averaged.plot(self.time_list, self.averaged_data)

    def save_lifetime_with_dialog(self):
        now = datetime.now()
        file_path = self.lineEdit_lifetime_directory.text()+'/' +\
                                                   self.lineEdit_lifetime_default_filename.text().\
                                                   replace("{d}", now.strftime("%Y%m%d")).\
                                                   replace("{t}", now.strftime("%H%M%S"))
        self.save_lifetime_data(file_path)

    def save_lifetime_data(self, file_path):
        if file_path == '':
            return
        column_headers = ['Time (s)'] + [str(i) for i in range(len(self.data))] + ['Averaged Voltage (V)']
        # for j in range(self.tableWidget_laser_calibration.model().columnCount()):
        #     column_headers.append(self.tableWidget_laser_calibration.horizontalHeaderItem(j).text())
        data = np.stack((self.time_list, *self.data, self.averaged_data), axis=1)
        df = DataFrame(data, columns = column_headers)
        try:
            df.to_csv(file_path, index = False)
        except Exception as e:
            print(e)
            self.label_error_calibration_path.setText("🚫 Error: Data not saved. Directory might be invalid!")
    
    def select_directory_lifetime(self):
        directoryName = QFileDialog.getExistingDirectory(self, 'Select directory', self.lineEdit_lifetime_directory.text())
        if directoryName:
            self.lineEdit_lifetime_directory.setText(directoryName)