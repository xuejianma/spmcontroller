from lasermeasurement import LaserMeasurement
from lib.ndfiltercontroller import NDFilterChange, NDFilterController
from lib.powermeter import PowerMeter, PowerMeterRead
from lib.topas4 import LaserWavelengthChange, Topas4
from powercalibration import PowerCalibration
from pyqtgraph import mkPen
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem
from datetime import datetime
import numpy as np
from pandas import DataFrame, read_csv
from os.path import isdir


class LaserPage:
    def update_line_graph_laser_measurement(self):
        self.widget_laser_measurement_ch1.clear()
        self.widget_laser_measurement_ch2.clear()
        key_to_show = 'wavelength'
        if self.laser_measurement_line_trace['mode'] == 1 or self.laser_measurement_line_trace['mode'] == 2:
            key_to_show = 'wavelength'
        else: # mode 3 or 4
            if self.laser_measurement_line_trace['mode'] == 4:#self.checkBox_laser_measurement_angle_to_power.isChecked():
                key_to_show = 'power'
            else:
                key_to_show = 'angle'
        # print(self.laser_measurement_line_trace)
        self.widget_laser_measurement_ch1.plot(self.laser_measurement_line_trace[key_to_show],
                                               self.laser_measurement_line_trace['ch1'],
                                               pen=mkPen(color=(0, 180, 0)), symbol='o', symbolBrush =(0, 180, 0))
        self.widget_laser_measurement_ch2.plot(self.laser_measurement_line_trace[key_to_show],
                                               self.laser_measurement_line_trace['ch2'],
                                               pen=mkPen(color=(180, 0, 0)), symbol='o', symbolBrush =(180, 0, 0))

    def reconnect_opa(self):
        try:
            self.laser_controller = Topas4()
            # self.laser_wavelength_change = None
            self.laser_wavelength_changing = False
            self.lcdNumber_laser_wavelength.display(self.laser_controller.getWavelength())
            self.label_error_wavelength.setText("")
            self.progressBar_wavelength.setValue(100)
        except:
            self.laser_controller = None
            self.label_error_wavelength.setText("🚫 Error: Laser OPA not detected!")


    def reconnect_ndfilter(self):
        try:
            self.laser_ndfilter_changing = False
            self.ndfilter_controller = NDFilterController()
            self.lcdNumber_ndfilter.display(self.ndfilter_controller.get_angle())
            self.label_error_ndfilter.setText("")
            self.progressBar_ndfilter.setValue(100)

        except Exception as e:
            print(e)
            self.ndfilter_controller = None
            self.label_error_ndfilter.setText("🚫 Error: ND Filter Controller not detected!")

    def reconnect_power(self):
        try:
            self.power_reading = False
            self.powermeter = PowerMeter()
            self.lcdNumber_laser_power.display(0)
            self.lcdNumber_laser_power_uW.display(0)
            self.label_power_error.setText("")
            self.checkBox_read_power.setEnabled(True)
        except Exception as e:
            print(e)
            self.powermeter = None
            self.label_power_error.setText("🚫 Error: Power Meter not detected!")
            self.checkBox_read_power.setChecked(False)
            self.checkBox_read_power.setEnabled(False)





    def real_time_power(self):
        if self.powermeter is None:
            return
        try:
            if self.checkBox_read_power.isChecked():
                self.thread_powermeter = QThread()
                self.power_meter_read = PowerMeterRead(#self,
                    powermeter = self.powermeter,
                    label_power_error=self.label_power_error, lcdNumber_laser_power=self.lcdNumber_laser_power,
                    lcdNumber_laser_power_uW = self.lcdNumber_laser_power_uW, checkBox_read_power=self.checkBox_read_power)
                self.power_meter_read.moveToThread(self.thread_powermeter)
                self.thread_powermeter.started.connect(self.power_meter_read.run)
                # self.input_voltage_encoder.update.connect(
                #     lambda: self.lcdNumber_encoder_reading.display(self.input_voltage_encoder.curr_value))
                self.power_meter_read.finished.connect(self.power_meter_read.deleteLater)
                self.power_meter_read.finished.connect(self.thread_powermeter.exit)
                self.thread_powermeter.finished.connect(self.thread_powermeter.deleteLater)
                self.thread_powermeter.start()
            else:
                self.checkBox_read_power.setEnabled(False)
                # the 105ms delay (disable checkbox) makes sure the run function does not crash
                # as time.sleep(0.1) in it is lower than 0.11 second, such that
                # "while self.checkBox_....isChecked()" can be checked without a problem when someone try to
                # check and uncheck the checkbox in a very high frequency.
                QTimer.singleShot(110, lambda: self.checkBox_read_power.setEnabled(True))
        except Exception as e:
            print(e)
            self.label_power_error.setText("🚫 Error: Power Meter not detected!")
            self.checkBox_read_power.setState(False)
            self.checkBox_read_power.setEnabled(False)

    def opa_set_wavelength(self, wavelength):
        if self.checkBox_set_wavelength_powermeter.isChecked():
            try: # TODO: set wavelength of powermeter first. Needs improvements.
                self.powermeter.set_wavelength(wavelength)
                print("Powermeter wavelength has first been successfully set to " + str(wavelength))
            except Exception as e:
                print(e)
        if self.checkBox_set_wavelength_labels.isChecked():
            self.lineEdit_laser_calibration_default_filename_label.setText(str(wavelength))
            self.lineEdit_laser_measurement_data_save_filename_label.setText(str(wavelength))

        if self.laser_controller is None:
            return
        self.label_error_wavelength.setText("")
        
        try:
            self.thread_set_wavelength = QThread()
            self.laser_wavelength_changing = True
            self.laser_wavelength_change = LaserWavelengthChange(self, self.laser_controller, wavelength)
            self.laser_wavelength_change.progress_update.connect(lambda: self.progressBar_wavelength.setValue(
                self.laser_wavelength_change.progress if self.laser_wavelength_change is not None else 100
            ))
            self.laser_wavelength_change.moveToThread(self.thread_set_wavelength)
            def turnoff():

                self.doubleSpinBox_laser_set_wavelength.setEnabled(
                    False)
                self.pushButton_laser_set_wavelength.setEnabled(False),
                # print("started")
            self.thread_set_wavelength.started.connect(turnoff)
            self.thread_set_wavelength.started.connect(self.laser_wavelength_change.setWavelength)
            def turnon():

                self.doubleSpinBox_laser_set_wavelength.setEnabled(True)
                self.pushButton_laser_set_wavelength.setEnabled(True)
                # print(self.pushButton_laser_set_wavelength.isEnabled())
                self.lcdNumber_laser_wavelength.display(
                    self.laser_controller.getWavelength())
                self.laser_wavelength_changing = False

            self.laser_wavelength_change.finished.connect(self.laser_wavelength_change.deleteLater)
            self.laser_wavelength_change.finished.connect(self.thread_set_wavelength.exit)
            self.laser_wavelength_change.finished.connect(turnon)
            self.thread_set_wavelength.finished.connect(self.thread_set_wavelength.deleteLater)
            self.thread_set_wavelength.start()

            # self.thread_set_wavelength = QThread()
            # self.laser_wavelength_change = LaserWavelengthChange(self.laser_controller, wavelength,
            #                                                      progressBar_wavelength=self.progressBar_wavelength)
        except Exception as e:
            print(e)
            self.label_error_wavelength.setText("🚫 Error: Laser OPA not detected!")

    def ndfilter_set_angle(self, angle):
        if self.ndfilter_controller is None:
            return
        self.label_error_wavelength.setText("")
        try:
            self.thread_set_angle = QThread()
            self.laser_ndfilter_changing = True
            self.ndfilter_change = NDFilterChange(self, self.ndfilter_controller, angle)
            self.ndfilter_change.moveToThread(self.thread_set_angle)
            self.ndfilter_change.progress_update.connect(lambda: self.progressBar_ndfilter.setValue(
                self.ndfilter_change.progress if self.ndfilter_change is not None else 100
            ))
            self.ndfilter_change.progress_update.connect(lambda: self.lcdNumber_ndfilter.display(
                self.ndfilter_controller.get_angle()))
            def turnoff():
                self.doubleSpinBox_ndfilter.setEnabled(False)
                self.pushButton_ndfilter.setEnabled(False)
            self.thread_set_angle.started.connect(turnoff)
            self.thread_set_angle.started.connect(self.ndfilter_change.set_angle)
            def turnon():
                self.doubleSpinBox_ndfilter.setEnabled(True)
                self.pushButton_ndfilter.setEnabled(True)
                self.lcdNumber_ndfilter.display(self.ndfilter_controller.get_angle())
                self.laser_ndfilter_changing = False

            self.ndfilter_change.finished.connect(self.ndfilter_change.deleteLater)
            self.ndfilter_change.finished.connect(self.thread_set_angle.exit)
            self.ndfilter_change.finished.connect(turnon)
            self.thread_set_angle.finished.connect(self.thread_set_angle.deleteLater)
            self.thread_set_angle.start()

        except Exception as e:
            print(e)
            self.label_error_wavelength.setText("🚫 Error: ND Filter Controller not detected!")

    def start_calibration(self):

        # try:
        #     print(self.power_calibration, self.power_calibration.i, self.thread_calibration)
        # except:
        #     print('wrong')
        self.thread_calibration = QThread()
        if not hasattr(self, 'power_calibration') or self.power_calibration is None:
            self.on_off_laser_widget_list_turn_off()
            self.pushButton_laser_measurement.setEnabled(False)
            self.power_calibration = PowerCalibration(self, self.laser_controller, self.ndfilter_controller, self.powermeter)
            self.last_calibration_mode = self.power_calibration.mode
            self.reset_calibration_form()
        try:
            self.power_calibration.halted.disconnect()
            self.power_calibration.finished.disconnect()
            self.power_calibration.progress_finished_wavelength.disconnect()
            self.power_calibration.progress_finished_angle.disconnect()
            self.power_calibration.progress_update_wavelength.disconnect()
            self.power_calibration.progress_update_angle.disconnect()
        except Exception as e:
            print(e)
        # def update_wavelength():
        #
        #     self.progressBar_power_calibration.setValue(self.power_calibration.progress if self.power_calibration is not None else 100)
        #     self.lcdNumber_laser_wavelength.display(self.laser_controller.getWavelength())

        self.power_calibration.fresh_new_start.connect(lambda: self.progressBar_power_calibration.setValue(0))
        self.power_calibration.progress_finished_wavelength_but_waiting_for_angle.connect(lambda: self.lcdNumber_laser_wavelength.display(self.laser_controller.getWavelength()))
        self.power_calibration.progress_finished_wavelength.connect(lambda: self.progressBar_power_calibration.setValue(self.power_calibration.progress if self.power_calibration is not None else 100))
        self.power_calibration.progress_finished_angle.connect(lambda: self.lcdNumber_ndfilter.display(
            self.ndfilter_controller.get_angle()
        ))
        self.power_calibration.progress_update_wavelength.connect(lambda: self.progressBar_wavelength.setValue(
            self.power_calibration.progress_wavelength if self.power_calibration is not None else 100
        ))
        self.power_calibration.progress_update_angle.connect(lambda: self.progressBar_ndfilter.setValue(
            self.power_calibration.progress_angle if self.power_calibration is not None else 100
        ))
        self.power_calibration.progress_update_angle.connect(lambda: self.lcdNumber_ndfilter.display(
            self.ndfilter_controller.get_angle()
        ))

        self.power_calibration.moveToThread(self.thread_calibration)
        self.thread_calibration.started.connect(self.power_calibration.sweep_wavelength)
        self.power_calibration.finished.connect(self.power_calibration.deleteLater)
        self.power_calibration.halted.connect(self.thread_calibration.exit)
        self.power_calibration.finished.connect(self.thread_calibration.exit)
        self.thread_calibration.finished.connect(self.thread_calibration.deleteLater)
        # def tmp():
        #     self.thread_calibration = None


        # def none_power_calibration():
        #     self.power_calibration = None
        # # self.thread_calibration.finished.connect(none_power_calibration)
        # self.power_calibration.finished.connect(lambda: self.toggle_calibration() if self.calibration_on else None)
        # self.power_calibration.finished.connect(none_power_calibration)
        self.power_calibration.finished.connect(self.abort_calibration)


        self.power_calibration.progress_finished_wavelength.connect(self.update_calibration_form)

        # self.power_calibration.destroyed.connect(none_power_calibration)
        self.thread_calibration.start()



    def toggle_calibration(self):
        self.pushButton_laser_calibration.setEnabled(False)
        self.pushButton_laser_calibration_abort.setEnabled(False)
        QTimer.singleShot(200, lambda: self.pushButton_laser_calibration.setEnabled(True))
        QTimer.singleShot(200, lambda: self.pushButton_laser_calibration_abort.setEnabled(True))

        if self.calibration_on:
            self.calibration_on = False
            self.pushButton_laser_calibration.setText("Start/Continue\nCalibration")
        else:
            self.label_error_calibration_path.setText("")
            if not isdir(self.lineEdit_laser_calibration_directory.text()):
                self.label_error_calibration_path.setText("🚫 Error: Invalid directory!")
                return
            self.calibration_on = True
            self.pushButton_laser_calibration.setText("Halt Calibration")
            # if not hasattr(self, 'power_calibration') or self.power_calibration is None:
            self.start_calibration()
            # else:
            #     self.power_calibration.sweep_wavelength()

    def abort_calibration(self):
        self.label_error_calibration_path.setText('')
        if self.calibration_on:
            self.toggle_calibration()
        self.calibration_on = False
        # self.power_calibration.deleteLater()
        self.power_calibration = None
        self.progressBar_power_calibration.setValue(100)
        self.on_off_laser_widget_list_turn_on()
        self.pushButton_laser_measurement.setEnabled(True)

    def reset_calibration_form(self):
        self.tableWidget_laser_calibration.setRowCount(0)

    def update_calibration_form(self):
        self.tableWidget_laser_calibration.insertRow(0)
        # print(self.main.tableWidget_laser_calibration.columnCount(), self.main.tableWidget_laser_calibration.rowCount() - 1)
        try:
            self.tableWidget_laser_calibration.setItem(0, 0, QTableWidgetItem(str(np.round(float(self.laser_controller.getWavelength()), 1))))
        except:
            self.tableWidget_laser_calibration.setItem(0, 0, QTableWidgetItem("null"))
        self.tableWidget_laser_calibration.setItem(0, 1, QTableWidgetItem(str(np.round(self.ndfilter_controller.get_angle(), 2))))
        self.tableWidget_laser_calibration.setItem(0, 2, QTableWidgetItem(str(np.round(self.powermeter.get_power() * 1e6, 2))))

    def save_calibration_form_without_dialog(self):
        now = datetime.now()
        file_path = self.lineEdit_laser_calibration_directory.text()+'/' +\
                                                   self.lineEdit_laser_calibration_default_filename.text().\
                                                   replace("{d}", now.strftime("%Y%m%d")).\
                                                   replace("{t}", now.strftime("%H%M%S")).\
                                                   replace("{m}", self.last_calibration_mode).\
                                                   replace("{l}", self.lineEdit_laser_calibration_default_filename_label.text())
        
        self.save_calibration_form(file_path)
        
        

    def save_calibration_form_with_dialog(self):
        now = datetime.now()
        file_path, _ = QFileDialog.getSaveFileName(self,"Save Calibration As:",
                                                   self.lineEdit_laser_calibration_directory.text()+'/' +
                                                   self.lineEdit_laser_calibration_default_filename.text().
                                                   replace("{d}", now.strftime("%Y%m%d")).
                                                   replace("{t}", now.strftime("%H%M%S")).
                                                   replace("{m}", self.last_calibration_mode).
                                                   replace("{l}", self.lineEdit_laser_calibration_default_filename_label.text()),
                                                   "CSV Files (*.csv);;All Files (*)")
        self.save_calibration_form(file_path)

    def save_calibration_form(self, file_path):
        if file_path == '':
            return
        
        column_headers = ['Wavelength (nm)', 'ND Filter Angle (degree)', 'Power (uW)']
        # for j in range(self.tableWidget_laser_calibration.model().columnCount()):
        #     column_headers.append(self.tableWidget_laser_calibration.horizontalHeaderItem(j).text())
        df = DataFrame(columns = column_headers)
        for row in range(self.tableWidget_laser_calibration.rowCount()):
            for col in range(self.tableWidget_laser_calibration.columnCount()):
                df.at[row, column_headers[col]] = self.tableWidget_laser_calibration.item(row, col).text()
        try:
            df.to_csv(file_path, index = False)
        except Exception as e:
            print(e)
            self.label_error_calibration_path.setText("🚫 Error: Data not saved. Directory might be invalid!")

    

    def load_calibration_form(self):
        file_path, _ = QFileDialog.getOpenFileName(self,"Load Calibration File:",
                                                   self.lineEdit_laser_calibration_directory.text(),
                                                   "CSV Files (*.csv);;All Files (*)")
        if file_path == '':
            return
        df = read_csv(file_path, index_col=None)
        file_wavelength_list = df.iloc[:, 0].values
        file_angle_list = df.iloc[:, 1].values
        file_power_list = df.iloc[:, 2].values
        self.tableWidget_laser_calibration.setRowCount(0)
        self.tableWidget_laser_calibration.setRowCount(len(file_wavelength_list))
        for ind in range(len(file_wavelength_list)):
            self.tableWidget_laser_calibration.setItem(ind, 0, QTableWidgetItem(str(float(file_wavelength_list[ind]))))
            self.tableWidget_laser_calibration.setItem(ind, 1, QTableWidgetItem(str(float(file_angle_list[ind]))))
            self.tableWidget_laser_calibration.setItem(ind, 2, QTableWidgetItem(str(float(file_power_list[ind]))))

    def start_laser_measurement(self):
        self.laser_measurement_thread = QThread()
        if not hasattr(self, 'laser_measurement') or self.laser_measurement is None:
            self.on_off_laser_widget_list_turn_off()
            self.pushButton_laser_calibration.setEnabled(False)
            self.label_warning_laser_measurement.setText('')
            self.laser_measurement_line_trace['wavelength'].clear()
            self.laser_measurement_line_trace['power'].clear()
            self.laser_measurement_line_trace['angle'].clear()
            self.laser_measurement_line_trace['ch1'].clear()
            self.laser_measurement_line_trace['ch2'].clear()
            self.laser_measurement = LaserMeasurement(self, self.laser_controller, self.ndfilter_controller,
                                                      self.powermeter)
            # self.reset_calibration_form()
        try:
            self.laser_measurement.halted.disconnect()
            self.laser_measurement.finished.disconnect()
            self.laser_measurement.progress_finished_wavelength.disconnect()
            self.laser_measurement.progress_finished_angle.disconnect()
            self.laser_measurement.progress_update_wavelength.disconnect()
            self.laser_measurement.progress_update_angle.disconnect()
        except Exception as e:
            print(e)
        # self.laser_measurement.moveToThread(self.laser_measurement_thread)
        # self.laser_measurement_thread.started.connect(self.laser_measurement.laser_measurement)
        # self.laser_measurement.finished.connect(self.laser_measurement.deleteLater)
        # self.laser_measurement.finished.connect(self.laser_measurement_thread.exit)
        # self.laser_measurement_thread.finished.connect(self.laser_measurement_thread.deleteLater)
        # self.laser_measurement_thread.start()
        self.laser_measurement.fresh_new_start.connect(lambda: self.progressBar_laser_measurement.setValue(0))
        self.laser_measurement.progress_finished_wavelength_but_waiting_for_angle.connect(lambda: self.lcdNumber_laser_wavelength.display(self.laser_controller.getWavelength()))
        self.laser_measurement.progress_finished_wavelength.connect(lambda: self.progressBar_laser_measurement.setValue(self.laser_measurement.progress if self.laser_measurement is not None else 100))
        self.laser_measurement.progress_finished_angle.connect(lambda: self.lcdNumber_ndfilter.display(
            self.ndfilter_controller.get_angle()
        ))
        self.laser_measurement.progress_update_wavelength.connect(lambda: self.progressBar_wavelength.setValue(
            self.laser_measurement.progress_wavelength if self.laser_measurement is not None else 100
        ))
        self.laser_measurement.progress_update_angle.connect(lambda: self.progressBar_ndfilter.setValue(
            self.laser_measurement.progress_angle if self.laser_measurement is not None else 100
        ))
        self.laser_measurement.progress_update_angle.connect(lambda: self.lcdNumber_ndfilter.display(
            self.ndfilter_controller.get_angle()
        ))
        self.laser_measurement.progress_finished_wavelength.connect(self.update_line_graph_laser_measurement)
        self.laser_measurement.moveToThread(self.laser_measurement_thread)
        self.laser_measurement_thread.started.connect(self.laser_measurement.laser_measurement)
        self.laser_measurement.finished.connect(self.laser_measurement.deleteLater)
        self.laser_measurement.halted.connect(self.laser_measurement_thread.exit)
        self.laser_measurement.finished.connect(self.laser_measurement_thread.exit)
        self.laser_measurement_thread.finished.connect(self.laser_measurement_thread.deleteLater)
        # def none_laser_measurement():
        #     self.laser_measurement = None
        # self.laser_measurement.finished.connect(lambda: self.toggle_laser_measurement() if self.laser_measurement_on else None)
        # self.laser_measurement.finished.connect(none_laser_measurement)
        self.laser_measurement.finished.connect(self.abort_laser_measurement)
        # self.laser_measurement.progress_finished_wavelength.connect(self.update_calibration_form)
        self.laser_measurement_thread.start()


    def toggle_laser_measurement(self):
        self.pushButton_laser_measurement.setEnabled(False)
        self.pushButton_laser_measurement_abort.setEnabled(False)
        QTimer.singleShot(200, lambda: self.pushButton_laser_measurement.setEnabled(True))
        QTimer.singleShot(200, lambda: self.pushButton_laser_measurement_abort.setEnabled(True))
        if self.laser_measurement_on:
            self.laser_measurement_on = False
            self.pushButton_laser_measurement.setText("Start/Continue\nMeasurement")
        else:
            self.label_warning_laser_measurement.setText("")
            if not isdir(self.lineEdit_laser_measurement_data_save_directory.text()):
                self.label_warning_laser_measurement.setText("🚫 Error: \nInvalid\nDirectory")
                return
            self.laser_measurement_on = True
            self.pushButton_laser_measurement.setText("Halt Measurement")
            # if not hasattr(self, 'power_calibration') or self.power_calibration is None:
            self.start_laser_measurement()

    def abort_laser_measurement(self):
        if self.laser_measurement_on:
            self.toggle_laser_measurement()
        self.laser_measurement_on = False
        self.laser_measurement = None
        self.progressBar_laser_measurement.setValue(100)
        self.label_warning_laser_measurement.setText('')
        self.on_off_laser_widget_list_turn_on()
        self.pushButton_laser_calibration.setEnabled(True)

    def on_off_laser_widget_list_turn_on(self):
        for widget in self.on_off_laser_widget_list:
            widget.setEnabled(True)

    def on_off_laser_widget_list_turn_off(self):
        for widget in self.on_off_laser_widget_list:
            widget.setEnabled(False)
    
    def select_directory_laser_calibration(self):
        directoryName = QFileDialog.getExistingDirectory(self, 'Select directory', self.lineEdit_laser_calibration_directory.text())
        if directoryName:
            self.lineEdit_laser_calibration_directory.setText(directoryName)

    def select_directory_laser_measurement(self):
        directoryName = QFileDialog.getExistingDirectory(self, 'Select directory', self.lineEdit_laser_measurement_data_save_directory.text())
        if directoryName:
            self.lineEdit_laser_measurement_data_save_directory.setText(directoryName)