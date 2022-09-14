from copy import deepcopy
from os.path import isdir
import numpy as np
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from pyparktiff import SaveParkTiff
from pyqtgraph import mkPen
from PyQt5.QtWidgets import QFileDialog
from time import time, sleep
from datetime import datetime

from util.plotscanrange import plot_scan_range, toggle_colorbar_ch1, toggle_colorbar_ch2, toggle_colorbar_main



class ScanPage:
    
    def determine_scan_window(self):
        self.piezo_limit_x = self.doubleSpinBox_piezo_limit_x.value()
        self.piezo_limit_y = self.doubleSpinBox_piezo_limit_y.value()
        self.xmin_input = self.doubleSpinBox_x_min.value()
        self.xmax_input = self.doubleSpinBox_x_max.value()
        self.ymin_input = self.doubleSpinBox_y_min.value()
        self.ymax_input = self.doubleSpinBox_y_max.value()
        self.xpixels = self.spinBox_x_pixels.value()
        self.ypixels = self.spinBox_y_pixels.value()
        self.frequency = self.doubleSpinBox_frequency.value()
        self.rotation_degree = self.doubleSpinBox_rotation.value()
        self.rotation = self.rotation_degree / 180 * np.pi
        center = np.array([[(self.xmin_input + self.xmax_input) / 2,
                            (self.ymin_input + self.ymax_input) / 2]]).T
        p1_input = np.array([self.xmin_input, self.ymin_input])
        p2_input = np.array([self.xmax_input, self.ymin_input])
        p3_input = np.array([self.xmax_input, self.ymax_input])
        p4_input = np.array([self.xmin_input, self.ymax_input])
        rotate_matrix = np.array([[np.cos(self.rotation), -np.sin(self.rotation)],
                                  [np.sin(self.rotation), np.cos(self.rotation)]])
        self.p1 = self.rotate_coord(p1_input, center, rotate_matrix)
        self.p2 = self.rotate_coord(p2_input, center, rotate_matrix)
        self.p3 = self.rotate_coord(p3_input, center, rotate_matrix)
        self.p4 = self.rotate_coord(p4_input, center, rotate_matrix)

        self.X_raw = np.round(np.linspace(0, self.xmax_input - self.xmin_input, self.xpixels), 6)
        self.Y_raw = np.round(np.linspace(0, self.ymax_input - self.ymin_input, self.ypixels), 6)
        XX_input, YY_input = np.meshgrid(self.X_raw + self.xmin_input, self.Y_raw + self.ymin_input)
        xx_yy = np.array([np.array([xx, yy]) for xx, yy in zip(XX_input.reshape((1, -1)), YY_input.reshape((1, -1)))])
        xx_yy_rot = self.rotate_coord(xx_yy, center, rotate_matrix)
        self.XX = xx_yy_rot[0, :].reshape(XX_input.shape)
        self.YY = xx_yy_rot[1, :].reshape(YY_input.shape)
        self.update_graphs()

    def rotate_coord(self, p, center, rotate_matrix):
        p = np.reshape(p, (2, -1))
        if p.shape[1] == 1:
            return np.round(np.reshape(np.matmul(rotate_matrix, (p - center)) + center, (-1, 2))[0], 6)
        else:
            return np.round(np.reshape(np.matmul(rotate_matrix, (p - center)) + center, (2, -1)), 6)
    
    def toggle_maintenance(self):
        if self.checkBox_maintenance.isChecked():
            self.doubleSpinBox_current_x.setDisabled(False)
            self.doubleSpinBox_current_y.setDisabled(False)
        else:
            self.doubleSpinBox_current_x.setDisabled(True)
            self.doubleSpinBox_current_y.setDisabled(True)

    def toggle_scan_button(self):
        if self.error_lock:
            self.label_error.setText(self.error_lock_text)
            return
        if self.scan_on_boolean:
            # The reason we didn't put the following expression outside of if-else is because while loop in start_
            # scan's Scan() needs to
            # determine whether to run based on the new boolean value. It somehow works if we put it at the end, but
            # simply because assigining new thread takes more time, and it has time to change boolean value before
            # the running really starts.
            self.scan_on_boolean = not self.scan_on_boolean
            self.on_off_spinbox_list_turn_on()
            self.pushButton_image.setDisabled(False)
            self.pushButton_scan.setText("Scan")
            # self.label_error.setText("")
        else:
            self.scan_on_boolean = not self.scan_on_boolean
            self.pushButton_scan.setText("OFF")
            self.on_off_spinbox_list_turn_off()
            self.pushButton_image.setDisabled(True)
            self.start_scan()


    def toggle_map_button(self):
        if self.error_lock:
            self.label_error.setText(self.error_lock_text)
            return
        if not isdir(self.lineEdit_directory.text()):
            self.label_error.setText("🚫 Error: Auto save directory not found")
            return
        if self.map_on_boolean:
            self.map_on_boolean = not self.map_on_boolean
            self.on_off_spinbox_list_turn_on()
            self.pushButton_scan.setDisabled(False)
            self.pushButton_image.setText("Image")
        else:
            self.map_on_boolean = not self.map_on_boolean
            self.pushButton_image.setText("OFF")
            self.on_off_spinbox_list_turn_off()
            self.pushButton_scan.setDisabled(True)
            self.start_map()

    def update_voltage_maintenance_x(self):
        self.curr_coords[0] = self.doubleSpinBox_current_x.value()
        self.update_voltage()

    def update_voltage_maintenance_y(self):
        self.curr_coords[1] = self.doubleSpinBox_current_y.value()
        self.update_voltage()

    def start_scan(self):
        self.thread_scan = QThread()
        self.scan = Scan(
            self)  # .curr_coords, self.XX, self.YY, self.frequency, self.update_voltage_signal, self.scan_on_boolean_in_list)
        self.scan.moveToThread(self.thread_scan)
        self.thread_scan.started.connect(self.scan.run)
        self.scan.finished.connect(self.scan.deleteLater)
        self.scan.finished.connect(self.thread_scan.exit)
        self.thread_scan.finished.connect(self.thread_scan.deleteLater)
        self.thread_scan.start()

    def start_map(self):
        self.thread_map = QThread()
        self.map = Map(
            self)  # .curr_coords, self.XX, self.YY, self.frequency, self.update_voltage_signal, self.scan_on_boolean_in_list)
        self.map.moveToThread(self.thread_map)
        self.thread_map.started.connect(self.map.run)
        self.thread_map.started.connect(self.update_graphs)
        self.map.finishedAfterMapping.connect(self.toggle_map_button)
        # self.map.finished.connect(self.on_off_spinbox_list_turn_on)
        self.map.finished.connect(self.map.deleteLater)
        self.map.finished.connect(self.thread_map.exit)
        self.map.lineFinished.connect(self.update_graphs)
        self.thread_map.finished.connect(self.thread_map.deleteLater)
        self.thread_map.start()

    def update_voltage(self):
        # print("Updated voltage: x = ", self.curr_coords[0], ", y = ", self.curr_coords[1])
        self.label_current_x.setText("Current x (V): " + str(self.curr_coords[0]))
        self.label_current_y.setText("Current y (V): " + str(self.curr_coords[1]))
        self.update_line_graph()

    def output_voltage(self):
        # self.output_voltage_x.outputVoltage(self.curr_coords[0])
        # self.output_voltage_y.outputVoltage(self.curr_coords[1])
        # self.output_voltage_z.outputVoltage(self.curr_coord_z +
        #                                     self.plane_fit.get_delta_z_plane_fitted(self.curr_coords[0],
        #                                                                             self.curr_coords[1]))
        self.output_voltage_xyz.outputVoltage([self.curr_coords[0], self.curr_coords[1], \
            self.curr_coord_z + self.plane_fit.get_delta_z_plane_fitted(self.curr_coords[0], self.curr_coords[1])])
    def update_line_graph(self):
        self.widget_linescan_ch1.clear()
        self.widget_linescan_ch2.clear()
        self.widget_linescan_ch1.plot(self.line_trace['X'], self.line_trace['ch1'], pen=mkPen(color=(0, 180, 0)))
        self.widget_linescan_ch1.plot(self.line_retrace['X'], self.line_retrace['ch1'], pen=mkPen(color=(180, 0, 0)))
        self.widget_linescan_ch2.plot(self.line_trace['X'], self.line_trace['ch2'], pen=mkPen(color=(0, 180, 0)))
        self.widget_linescan_ch2.plot(self.line_retrace['X'], self.line_retrace['ch2'], pen=mkPen(color=(180, 0, 0)))

    def goto_position(self, p):
        self.thread_goto_position = QThread()
        self.move = MoveToTarget(self, p,
                                 manual_move=True)  # .curr_coords, self.XX, self.YY, self.frequency, self.update_voltage_signal, self.scan_on_boolean_in_list)
        self.move.moveToThread(self.thread_goto_position)
        self.thread_goto_position.started.connect(self.move.move)
        self.move.started.connect(self.on_off_button_list_turn_off)
        self.move.started.connect(lambda: self.on_off_spinbox_list_turn_off(exception=self.pushButton_stop_goto))
        self.move.finished.connect(self.move.deleteLater)
        self.move.finished.connect(self.on_off_button_list_turn_on)
        self.move.finished.connect(lambda: self.on_off_spinbox_list_turn_on(exception=self.pushButton_stop_goto))
        self.move.finished.connect(self.thread_goto_position.exit)
        self.thread_goto_position.finished.connect(self.thread_goto_position.deleteLater)
        self.thread_goto_position.start()

    def on_off_button_list_turn_on(self, without_pushButton_image=False, without_pushButton_scan=False):
        for w in self.on_off_button_list:
            if (without_pushButton_image and w == self.pushButton_image) or (
                    without_pushButton_scan and w == self.pushButton_scan):
                continue
            w.setDisabled(False)

    def on_off_button_list_turn_off(self):
        for w in self.on_off_button_list:
            w.setDisabled(True)

    def on_off_spinbox_list_turn_on(self, exception = None):
        for w in self.on_off_spinbox_list:
            if w != exception:
                w.setDisabled(False)

    def on_off_spinbox_list_turn_off(self, exception = None):
        for w in self.on_off_spinbox_list:
            if w != exception:
                w.setDisabled(True)

    def selectDirectory(self):
        directoryName = QFileDialog.getExistingDirectory(self,
                                                         'Select directory', self.lineEdit_directory.text())  # getOpenFileName(self, 'Open file', '.', '')
        self.label_error.setText("")
        # print("folder name: '" + directoryName + "'")
        if directoryName:
            self.lineEdit_directory.setText(directoryName)

    def update_plane_fit(self):
        points = []
        for i in range(len(self.plane_fit_list[0])):
            plane_fit_x, plane_fit_y, plane_fit_z, plane_fit_checked = self.plane_fit_list[0][i],\
            self.plane_fit_list[1][i], self.plane_fit_list[2][i], self.plane_fit_list[3][i]
            if plane_fit_checked.isChecked():
                points.append([plane_fit_x.value(), plane_fit_y.value(), plane_fit_z.value()])
        print(points, self.plane_fit.p1, self.plane_fit.p2)
        self.plane_fit.fit(points)
        
    def update_graphs(self, single='all'):
        if self.current_image_index == 1:
            map_trace, map_retrace = self.map_trace, self.map_retrace
        else:
            map_trace, map_retrace = self.map_history[len(self.map_history) - self.current_image_index + 1]['map_trace'], \
                                    self.map_history[len(self.map_history) - self.current_image_index + 1]['map_retrace']
        xlim_min = np.min([self.p1[0], self.p2[0], self.p3[0], self.p4[0]])
        xlim_max = np.max([self.p1[0], self.p2[0], self.p3[0], self.p4[0]])
        ylim_min = np.min([self.p1[1], self.p2[1], self.p3[1], self.p4[1]])
        ylim_max = np.max([self.p1[1], self.p2[1], self.p3[1], self.p4[1]])
        if single == 'all' or single == 'main':
            self.plot_scan_range(self.widget_display_piezo_limit, xlim_min=0, xlim_max=self.piezo_limit_x, ylim_min=0,
                                 ylim_max=self.piezo_limit_y, map_trace = map_trace, map_retrace = map_retrace)
        if single == 'all' or single == 'ch1':
            self.plot_scan_range(self.widget_display_scan_window_ch1, xlim_min=xlim_min, xlim_max=xlim_max,
                                 ylim_min=ylim_min,
                                 ylim_max=ylim_max, map_trace = map_trace, map_retrace = map_retrace)
        if single == 'all' or single == 'ch2':
            self.plot_scan_range(self.widget_display_scan_window_ch2, xlim_min=xlim_min, xlim_max=xlim_max,
                                 ylim_min=ylim_min,
                                 ylim_max=ylim_max, map_trace = map_trace, map_retrace = map_retrace)
                                 
    def plot_scan_range(self, widget, xlim_min, xlim_max, ylim_min, ylim_max, map_trace, map_retrace):
        plot_scan_range(self, widget, xlim_min, xlim_max, ylim_min, ylim_max, map_trace, map_retrace)

    def toggle_colorbar_main(self):
        toggle_colorbar_main(self)

    def toggle_colorbar_ch1(self):
        toggle_colorbar_ch1(self)

    def toggle_colorbar_ch2(self):
        toggle_colorbar_ch2(self)

    def manual_goto_boolean_to_false(self):
        self.manual_goto_boolean = False

    def show_newer_image(self):
        if self.current_image_index > 1:
            self.current_image_index -= 1
            self.update_label_image_display_number()
    
    def show_older_image(self):
        if self.current_image_index < len(self.map_history) + 1:
            self.current_image_index += 1
            self.update_label_image_display_number()

    def add_image_to_history(self):
        self.map_history.append({
            'map_trace': deepcopy(self.map_trace),
            'map_retrace': deepcopy(self.map_retrace),
        })
        if self.current_image_index > 1:
            self.current_image_index += 1
        self.update_label_image_display_number()
    
    def update_label_image_display_number(self):
        if self.current_image_index == 1:
            self.label_image_display_number.setText("1 (Imaging) / " + str(len(self.map_history) + 1))
        else:
            self.label_image_display_number.setText(str(self.current_image_index) + " / " + str(len(self.map_history) + 1))
        self.update_graphs()

def distance(p_A, p_B):
    return np.sqrt((p_A[0] - p_B[0]) ** 2 + (p_A[1] - p_B[1]) ** 2)


class Scan(QObject):
    finished = pyqtSignal()

    def __init__(self, parent):  # curr_coords, XX, YY, frequency, signal, scan_on_boolean_in_list):
        super(Scan, self).__init__()
        self.parent = parent
        self.isRunning = True
        self.x_array = parent.XX[0]
        self.y_array = parent.YY[0]
        self.p_start = np.array([self.x_array[0], self.y_array[0]])
        self.counts = 0
        self.extra_time = 0

    def run(self):
        print("start scan")
        self.parent.label_lines.setText("")
        moving_text = "Moving to Scan starting point..."
        if self.parent.curr_coords[0] != self.p_start[0] or self.parent.curr_coords[1] != self.p_start[1]:
            self.parent.label_lines.setText(moving_text)
            self.move_to_p_start()  # move to beginning before scan
            self.parent.label_lines.setText("")
        while self.parent.scan_on_boolean:
            self.parent.line_trace['X'].clear()
            self.parent.line_trace['ch1'].clear()
            self.parent.line_trace['ch2'].clear()
            self.parent.line_retrace['X'].clear()
            self.parent.line_retrace['ch1'].clear()
            self.parent.line_retrace['ch2'].clear()
            # self.parent.update_line_graph()
            # trace:
            for i in range(len(self.x_array)):
                if not self.parent.scan_on_boolean:
                    break
                t0 = time()
                self.single_time = 1 / self.parent.frequency / 2 / len(self.x_array)
                self.mod_unit = np.max([1, int(0.1 / (self.single_time + self.extra_time))])
                self.counts += 1
                self.parent.curr_coords[0] = self.x_array[i]
                self.parent.curr_coords[1] = self.y_array[i]
                # Below: self.single_time_old and 0.002 are used to ensure the sudden change of self.single_time
                # due to sudden change of self.parent.frequency does not inappropriately change the waiting time
                sleep_time = np.max([self.single_time - self.extra_time, 0.002])
                sleep(sleep_time)
                # self.parent.output_voltage_signal.emit()
                # tt1 = time()
                self.parent.output_voltage()
                # tt2 = time()
                if self.counts % self.mod_unit == 0 or i == len(self.x_array) - 1:
                    self.parent.update_graphs_signal.emit()
                # tt3 = time()
                ch1_ch2 = self.parent.get_voltage_ch1_ch2() ##(self.parent.lockin_top.get_output(), self.parent.lockin_bottom.get_output())#
                # tt4 = time()
                # print(tt2 - tt1, tt4 - tt3, (tt4 - tt3) / (tt2 - tt1 + 1e-10), (tt2 - tt1) / (tt4 - tt3 + 1e-10))
                self.parent.line_trace['X'].append(self.parent.X_raw[i])
                self.parent.line_trace['ch1'].append(ch1_ch2[0])
                self.parent.line_trace['ch2'].append(ch1_ch2[1])
                self.extra_time = time() - t0 - sleep_time
                # self.parent.update_line_graph()
            # retrace:
            for i in reversed(range(len(self.x_array))):
                if not self.parent.scan_on_boolean:
                    break
                t0 = time()
                self.single_time = 1 / self.parent.frequency / 2 / len(self.x_array)
                self.mod_unit = np.max([1, int(0.1 / (self.single_time + self.extra_time))])
                self.counts += 1
                self.parent.curr_coords[0] = self.x_array[i]
                self.parent.curr_coords[1] = self.y_array[i]
                sleep_time = np.max([self.single_time - self.extra_time, 0.002]) #0.002 just for safety (~1s for 512 px)
                sleep(sleep_time)
                # self.parent.output_voltage_signal.emit()
                self.parent.output_voltage()
                if self.counts % self.mod_unit == 0 or i == 0:
                    self.parent.update_graphs_signal.emit()
                ch1_ch2 = self.parent.get_voltage_ch1_ch2()
                self.parent.line_retrace['X'].append(self.parent.X_raw[i])
                self.parent.line_retrace['ch1'].append(ch1_ch2[0])
                self.parent.line_retrace['ch2'].append(ch1_ch2[1])
                self.extra_time = time() - t0 - sleep_time
                # self.parent.update_line_graph()
            print("end scan")
        if self.parent.label_lines.text() == moving_text:
            self.parent.label_lines.setText("")
        self.finished.emit()

    def move_to_p_start(self):
        self.move = MoveToTarget(self.parent, self.p_start, manual_move=False)
        # self.move.started.connect(self.parent.on_off_button_list_turn_off)
        self.move.finished.connect(self.move.deleteLater)
        self.move.finished.connect(lambda: self.parent.on_off_button_list_turn_on(without_pushButton_image=True))
        self.move.move()

class Map(QObject):
    finished = pyqtSignal()
    lineFinished = pyqtSignal()
    finishedAfterMapping = pyqtSignal()

    def __init__(self, parent):
        super(Map, self).__init__()
        self.parent = parent
        self.isRunning = True
        self.x_array = parent.XX[0]
        self.y_array = parent.YY[0]
        self.p_start = np.array([self.x_array[0], self.y_array[0]])
        self.counts = 0
        self.extra_time = 0
        # self.filename_prefix =
        # x = 1 + 1
        self.define_filename()

    def define_filename(self):
        now = datetime.now()
        self.filename_trace_ch1 = self.parent.lineEdit_filename_trace_ch1.text().replace("{d}", now.strftime(
            "%Y%m%d")).replace("{t}", now.strftime("%H%M%S"))
        self.filename_trace_ch2 = self.parent.lineEdit_filename_trace_ch2.text().replace("{d}", now.strftime(
            "%Y%m%d")).replace("{t}", now.strftime("%H%M%S"))
        self.filename_retrace_ch1 = self.parent.lineEdit_filename_retrace_ch1.text().replace("{d}", now.strftime(
            "%Y%m%d")).replace("{t}", now.strftime("%H%M%S"))
        self.filename_retrace_ch2 = self.parent.lineEdit_filename_retrace_ch2.text().replace("{d}", now.strftime(
            "%Y%m%d")).replace("{t}", now.strftime("%H%M%S"))
        self.directory = self.parent.lineEdit_directory.text()

    def run(self):
        print("start scan")
        moving_text = "Moving to Image starting point..."
        if self.parent.map_trace['XX']:
            self.parent.add_image_to_history()
        self.parent.map_trace['XX'].clear()
        self.parent.map_trace['YY'].clear()
        self.parent.map_trace['ch1'].clear()
        self.parent.map_trace['ch2'].clear()
        self.parent.map_retrace['XX'].clear()
        self.parent.map_retrace['YY'].clear()
        self.parent.map_retrace['ch1'].clear()
        self.parent.map_retrace['ch2'].clear()
        self.parent.current_image_index = 1
        self.parent.update_label_image_display_number()
        if self.parent.curr_coords[0] != self.p_start[0] or self.parent.curr_coords[1] != self.p_start[1]:
            self.parent.label_lines.setText(moving_text)
            self.move_to_p_start()
            self.parent.label_lines.setText("")
        row_num = 0
        while self.parent.map_on_boolean and row_num < self.parent.XX.shape[0]:
            self.parent.label_lines.setText("Current Line: {} / {}".format(row_num + 1, self.parent.XX.shape[0]))
            self.x_array = self.parent.XX[row_num]
            self.y_array = self.parent.YY[row_num]
            self.parent.line_trace['X'].clear()
            self.parent.line_trace['ch1'].clear()
            self.parent.line_trace['ch2'].clear()
            self.parent.line_retrace['X'].clear()
            self.parent.line_retrace['ch1'].clear()
            self.parent.line_retrace['ch2'].clear()
            # trace:
            for i in range(len(self.x_array)):
                if not self.parent.map_on_boolean:
                    break
                t0 = time()
                self.single_time = 1 / self.parent.frequency / 2 / len(self.x_array)
                self.mod_unit = np.max([1, int(0.1 / (self.single_time + self.extra_time))])
                self.counts += 1
                self.parent.curr_coords[0] = self.x_array[i]
                self.parent.curr_coords[1] = self.y_array[i]
                sleep_time = np.max([self.single_time - self.extra_time, 0.002])
                sleep(sleep_time)
                # self.parent.output_voltage_signal.emit()
                self.parent.output_voltage()
                if self.counts % self.mod_unit == 0 or i == len(self.x_array) - 1:
                    self.parent.update_graphs_signal.emit()
                ch1_ch2 = self.parent.get_voltage_ch1_ch2()
                self.parent.line_trace['X'].append(self.parent.X_raw[i])
                self.parent.line_trace['ch1'].append(ch1_ch2[0])
                self.parent.line_trace['ch2'].append(ch1_ch2[1])
                self.extra_time = time() - t0 - sleep_time
            # list() converts array to list, also copying the data rather than using reference
            if self.parent.map_on_boolean:
                self.parent.map_trace['XX'].append(list(self.parent.XX[row_num]))
                self.parent.map_trace['YY'].append(list(self.parent.YY[row_num]))
                self.parent.map_trace['ch1'].append(self.parent.line_trace['ch1'].copy())
                self.parent.map_trace['ch2'].append(self.parent.line_trace['ch2'].copy())
                self.lineFinished.emit()

                self.parent.thread1 = QThread() # thread1 is assigned to self.parent to avoid abrupt killing of the saving thread while it's running
                self.save1 = SaveTiffFile(self.parent.map_trace['ch1'], self.parent.X_raw[-1], self.parent.Y_raw[len(self.parent.map_trace['ch1']) - 1],
                                          self.filename_trace_ch1, self.directory)
                self.save1.moveToThread(self.parent.thread1)
                self.parent.thread1.started.connect(self.save1.save)
                self.save1.finished.connect(self.save1.deleteLater)
                self.save1.finished.connect(self.parent.thread1.exit)
                self.parent.thread1.finished.connect(self.parent.thread1.deleteLater)

                self.parent.thread1.start()

                self.parent.thread2 = QThread()
                self.save2 = SaveTiffFile(self.parent.map_trace['ch2'], self.parent.X_raw[-1], self.parent.Y_raw[len(self.parent.map_trace['ch2']) - 1],
                                          self.filename_trace_ch2, self.directory)
                self.save2.moveToThread(self.parent.thread2)
                self.save2.finished.connect(self.parent.thread2.exit)
                self.save2.finished.connect(self.save2.deleteLater)
                self.parent.thread2.finished.connect(self.parent.thread2.deleteLater)
                self.parent.thread2.started.connect(self.save2.save)
                self.parent.thread2.start()

            # retrace:
            for i in reversed(range(len(self.x_array))):
                if not self.parent.map_on_boolean:
                    break
                t0 = time()
                self.single_time = 1 / self.parent.frequency / 2 / len(self.x_array)
                self.mod_unit = np.max([1, int(0.1 / (self.single_time + self.extra_time))])
                self.counts += 1
                self.parent.curr_coords[0] = self.x_array[i]
                self.parent.curr_coords[1] = self.y_array[i]
                sleep_time = np.max([self.single_time - self.extra_time, 0.002])
                sleep(sleep_time)
                # self.parent.output_voltage_signal.emit()
                self.parent.output_voltage()
                if self.counts % self.mod_unit == 0 or i == 0:
                    self.parent.update_graphs_signal.emit()
                ch1_ch2 = self.parent.get_voltage_ch1_ch2()
                self.parent.line_retrace['X'].append(self.parent.X_raw[i])
                self.parent.line_retrace['ch1'].append(ch1_ch2[0])
                self.parent.line_retrace['ch2'].append(ch1_ch2[1])
                self.extra_time = time() - t0 - sleep_time
            if self.parent.map_on_boolean:
                self.parent.map_retrace['XX'].append(list(self.parent.XX[row_num]))
                self.parent.map_retrace['YY'].append(list(self.parent.YY[row_num]))
                self.parent.map_retrace['ch1'].append(self.parent.line_retrace['ch1'][::-1])#.copy())
                self.parent.map_retrace['ch2'].append(self.parent.line_retrace['ch2'][::-1])#.copy())
                self.lineFinished.emit()

                self.parent.thread3 = QThread()
                self.save3 = SaveTiffFile(self.parent.map_retrace['ch1'], self.parent.X_raw[-1], self.parent.Y_raw[len(self.parent.map_retrace['ch1']) - 1],
                                          self.filename_retrace_ch1, self.directory)
                self.save3.moveToThread(self.parent.thread3)
                self.save3.finished.connect(self.parent.thread3.exit)
                self.save3.finished.connect(self.save3.deleteLater)
                self.parent.thread3.finished.connect(self.parent.thread3.deleteLater)
                self.parent.thread3.started.connect(self.save3.save)
                self.parent.thread3.start()

                self.parent.thread4 = QThread()
                self.save4 = SaveTiffFile(self.parent.map_retrace['ch2'], self.parent.X_raw[-1], self.parent.Y_raw[len(self.parent.map_retrace['ch2']) - 1],
                                          self.filename_retrace_ch2, self.directory)
                self.save4.moveToThread(self.parent.thread4)
                self.save4.finished.connect(self.parent.thread4.exit)
                self.save4.finished.connect(self.save4.deleteLater)
                self.parent.thread4.finished.connect(self.parent.thread4.deleteLater)
                self.parent.thread4.started.connect(self.save4.save)
                self.parent.thread4.start()
            row_num += 1
            print("end scan")
        if self.parent.label_lines.text() == moving_text or "Current Line" in self.parent.label_lines.text():
            self.parent.label_lines.setText("")
        if self.parent.map_on_boolean:
            self.finishedAfterMapping.emit()
        # self.parent.label_lines.setText("")
        self.finished.emit()

    def move_to_p_start(self):
        self.move = MoveToTarget(self.parent, self.p_start, manual_move=False)
        # self.move.started.connect(self.parent.on_off_button_list_turn_off)
        self.move.finished.connect(self.move.deleteLater)
        self.move.finished.connect(lambda: self.parent.on_off_button_list_turn_on(without_pushButton_scan=True))
        self.move.move()

class MoveToTarget(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, parent, target, manual_move=False):
        super(MoveToTarget, self).__init__()
        self.parent = parent
        self.target = target
        self.manual_move = manual_move
        self.counts = 0

    def move(self):
        if self.manual_move:
            self.parent.manual_goto_boolean = True
        print("start move-to-target")
        self.started.emit()
        ratio = distance(self.parent.curr_coords, self.target) / \
                distance(np.array([self.parent.XX[0][0], self.parent.YY[0][0]]),
                         np.array([self.parent.XX[0][-1], self.parent.YY[0][-1]]))

        # for w in self.parent.on_off_button_list:
        #     w.setDisabled(True)

        steps = np.max([int(len(self.parent.XX[0]) * ratio), 10]) # for safety, we set minimal steps as 10
        x_array = np.round(np.linspace(self.parent.curr_coords[0], self.target[0], steps), 6)
        y_array = np.round(np.linspace(self.parent.curr_coords[1], self.target[1], steps), 6)
        # print(steps, x_array, y_array)
        for i in range(len(x_array)):
            # TODO: if halted, stop for loop
            if (not self.manual_move) and (not self.parent.scan_on_boolean) and (not self.parent.map_on_boolean):
                break
            if self.manual_move and not self.parent.manual_goto_boolean:
                break
            total_time = 1 / self.parent.frequency / 2 * ratio
            single_time = total_time / steps
            self.parent.curr_coords[0] = x_array[i]
            self.parent.curr_coords[1] = y_array[i]
            sleep(single_time)
            self.single_time = 1 / self.parent.frequency / 2 / len(x_array)
            self.mod_unit = np.max([1, int(0.1 / self.single_time)])
            # self.parent.output_voltage_signal.emit()
            self.parent.output_voltage()
            if self.counts % self.mod_unit == 0:
                self.parent.update_graphs_signal.emit()
            self.counts += 1
            # print(self.parent.curr_coords)
        print("end move-to-target")
        # print(self.parent.curr_coords)
        self.parent.update_graphs_signal.emit()
        # for w in self.parent.on_off_button_list:
        #     w.setDisabled(False)
        self.finished.emit()

class SaveTiffFile(QObject):
    finished = pyqtSignal()
    def __init__(self, data, xmax, ymax, filename, directory):
        super(SaveTiffFile, self).__init__()
        self.data = np.asanyarray(data)
        self.filename = filename
        self.directory = directory
        self.xmax = xmax
        self.ymax = ymax

    def save(self):
        SaveParkTiff(data=self.data, X_scan_size=self.xmax, Y_scan_size=self.ymax,
                     file_path=self.directory + '/' + self.filename + ".tiff")
        np.savetxt(self.directory + '/' + self.filename + ".txt", self.data)
        self.finished.emit()
        print('save done')

    