"""
Created by Xuejian Ma at 10/2/2021.
All rights reserved.
"""
from pyparktiff import SaveParkTiff
from time import sleep
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from datetime import datetime

import numpy as np


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

    def run(self):
        print("start scan")
        if self.parent.curr_coords[0] != self.p_start[0] or self.parent.curr_coords[1] != self.p_start[1]:
            self.move_to_p_start()  # move to beginning before scan
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
                self.single_time = 1 / self.parent.frequency / 2 / len(self.x_array)
                self.mod_unit = np.max([1, int(0.1 / self.single_time)])
                self.counts += 1
                self.parent.curr_coords[0] = self.x_array[i]
                self.parent.curr_coords[1] = self.y_array[i]
                sleep(self.single_time)
                self.parent.output_voltage_signal.emit()
                if self.counts % self.mod_unit == 0 or i == len(self.x_array) - 1:
                    self.parent.update_graphs_signal.emit()
                ch1_ch2 = self.parent.get_voltage_ch1_ch2()
                self.parent.line_trace['X'].append(self.parent.X_raw[i])
                self.parent.line_trace['ch1'].append(ch1_ch2[0])
                self.parent.line_trace['ch2'].append(ch1_ch2[1])
                # self.parent.update_line_graph()
            # retrace:
            for i in reversed(range(len(self.x_array))):
                if not self.parent.scan_on_boolean:
                    break
                self.single_time = 1 / self.parent.frequency / 2 / len(self.x_array)
                self.mod_unit = np.max([1, int(0.1 / self.single_time)])
                self.counts += 1
                self.parent.curr_coords[0] = self.x_array[i]
                self.parent.curr_coords[1] = self.y_array[i]
                sleep(self.single_time)
                self.parent.output_voltage_signal.emit()
                if self.counts % self.mod_unit == 0 or i == 0:
                    self.parent.update_graphs_signal.emit()
                ch1_ch2 = self.parent.get_voltage_ch1_ch2()
                self.parent.line_retrace['X'].append(self.parent.X_raw[i])
                self.parent.line_retrace['ch1'].append(ch1_ch2[0])
                self.parent.line_retrace['ch2'].append(ch1_ch2[1])
                # self.parent.update_line_graph()
            print("end scan")
        self.finished.emit()

    def move_to_p_start(self):
        self.move = MoveToTarget(self.parent, self.p_start, manual_move=False)
        self.move.started.connect(self.parent.on_off_button_list_turn_off)
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
        # self.filename_prefix =
        # x = 1 + 1
        self.define_filename()

    def define_filename(self):
        now = datetime.now()
        self.filename_trace_ch1 = self.parent.lineEdit_filename_trace_ch1.text().replace("{d}", now.strftime(
            "%Y%m%d")).replace("{t}", now.strftime("%H%M%S")) + ".tiff"
        self.filename_trace_ch2 = self.parent.lineEdit_filename_trace_ch2.text().replace("{d}", now.strftime(
            "%Y%m%d")).replace("{t}", now.strftime("%H%M%S")) + ".tiff"
        self.filename_retrace_ch1 = self.parent.lineEdit_filename_retrace_ch1.text().replace("{d}", now.strftime(
            "%Y%m%d")).replace("{t}", now.strftime("%H%M%S")) + ".tiff"
        self.filename_retrace_ch2 = self.parent.lineEdit_filename_retrace_ch2.text().replace("{d}", now.strftime(
            "%Y%m%d")).replace("{t}", now.strftime("%H%M%S")) + ".tiff"
        self.directory = self.parent.lineEdit_directory.text()

    def run(self):
        print("start scan")
        self.parent.map_trace['XX'].clear()
        self.parent.map_trace['YY'].clear()
        self.parent.map_trace['ch1'].clear()
        self.parent.map_trace['ch2'].clear()
        self.parent.map_retrace['XX'].clear()
        self.parent.map_retrace['YY'].clear()
        self.parent.map_retrace['ch1'].clear()
        self.parent.map_retrace['ch2'].clear()
        if self.parent.curr_coords[0] != self.p_start[0] or self.parent.curr_coords[1] != self.p_start[1]:
            self.move_to_p_start()
        row_num = 0
        while self.parent.map_on_boolean and row_num < self.parent.XX.shape[0]:
            self.x_array = self.parent.XX[row_num]
            self.y_array = self.parent.YY[row_num]
            print(self.y_array[0])
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
                self.single_time = 1 / self.parent.frequency / 2 / len(self.x_array)
                self.mod_unit = np.max([1, int(0.1 / self.single_time)])
                self.counts += 1
                self.parent.curr_coords[0] = self.x_array[i]
                self.parent.curr_coords[1] = self.y_array[i]
                sleep(self.single_time)
                self.parent.output_voltage_signal.emit()
                if self.counts % self.mod_unit == 0 or i == len(self.x_array) - 1:
                    self.parent.update_graphs_signal.emit()
                ch1_ch2 = self.parent.get_voltage_ch1_ch2()
                self.parent.line_trace['X'].append(self.parent.X_raw[i])
                self.parent.line_trace['ch1'].append(ch1_ch2[0])
                self.parent.line_trace['ch2'].append(ch1_ch2[1])
            # list() converts array to list, also copying the data rather than using reference
            if self.parent.map_on_boolean:
                self.parent.map_trace['XX'].append(list(self.parent.XX[row_num]))
                self.parent.map_trace['YY'].append(list(self.parent.YY[row_num]))
                self.parent.map_trace['ch1'].append(self.parent.line_trace['ch1'].copy())
                self.parent.map_trace['ch2'].append(self.parent.line_trace['ch2'].copy())
                self.lineFinished.emit()

                self.parent.thread1 = QThread() # thread1 is assigned to self.parent to avoid abrupt killing of the saving thread while it's running
                self.save1 = SaveTiffFile(self.parent.map_trace['ch1'], self.parent.X_raw[-1], self.parent.Y_raw[-1],
                                          self.filename_trace_ch1, self.directory)
                self.save1.moveToThread(self.parent.thread1)
                self.parent.thread1.started.connect(self.save1.save)
                self.save1.finished.connect(self.save1.deleteLater)
                self.save1.finished.connect(self.parent.thread1.exit)
                self.parent.thread1.finished.connect(self.parent.thread1.deleteLater)

                self.parent.thread1.start()

                self.parent.thread2 = QThread()
                self.save2 = SaveTiffFile(self.parent.map_trace['ch2'], self.parent.X_raw[-1], self.parent.Y_raw[-1],
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
                self.single_time = 1 / self.parent.frequency / 2 / len(self.x_array)
                self.mod_unit = np.max([1, int(0.1 / self.single_time)])
                self.counts += 1
                self.parent.curr_coords[0] = self.x_array[i]
                self.parent.curr_coords[1] = self.y_array[i]
                sleep(self.single_time)
                self.parent.output_voltage_signal.emit()
                if self.counts % self.mod_unit == 0 or i == 0:
                    self.parent.update_graphs_signal.emit()
                ch1_ch2 = self.parent.get_voltage_ch1_ch2()
                self.parent.line_retrace['X'].append(self.parent.X_raw[i])
                self.parent.line_retrace['ch1'].append(ch1_ch2[0])
                self.parent.line_retrace['ch2'].append(ch1_ch2[1])
            if self.parent.map_on_boolean:
                self.parent.map_retrace['XX'].append(list(self.parent.XX[row_num]))
                self.parent.map_retrace['YY'].append(list(self.parent.YY[row_num]))
                self.parent.map_retrace['ch1'].append(self.parent.line_retrace['ch1'].copy())
                self.parent.map_retrace['ch2'].append(self.parent.line_retrace['ch2'].copy())
                self.lineFinished.emit()

                self.parent.thread3 = QThread()
                self.save3 = SaveTiffFile(self.parent.map_retrace['ch1'], self.parent.X_raw[-1], self.parent.Y_raw[-1],
                                          self.filename_retrace_ch1, self.directory)
                self.save3.moveToThread(self.parent.thread3)
                self.save3.finished.connect(self.parent.thread3.exit)
                self.save3.finished.connect(self.save3.deleteLater)
                self.parent.thread3.finished.connect(self.parent.thread3.deleteLater)
                self.parent.thread3.started.connect(self.save3.save)
                self.parent.thread3.start()

                self.parent.thread4 = QThread()
                self.save4 = SaveTiffFile(self.parent.map_retrace['ch2'], self.parent.X_raw[-1], self.parent.Y_raw[-1],
                                          self.filename_retrace_ch2, self.directory)
                self.save4.moveToThread(self.parent.thread4)
                self.save4.finished.connect(self.parent.thread4.exit)
                self.save4.finished.connect(self.save4.deleteLater)
                self.parent.thread4.finished.connect(self.parent.thread4.deleteLater)
                self.parent.thread4.started.connect(self.save4.save)
                self.parent.thread4.start()
            row_num += 1
            print("end scan")
        if self.parent.map_on_boolean:
            self.finishedAfterMapping.emit()
        self.finished.emit()

    def move_to_p_start(self):
        self.move = MoveToTarget(self.parent, self.p_start, manual_move=False)
        self.move.started.connect(self.parent.on_off_button_list_turn_off)
        self.move.finished.connect(self.move.deleteLater)
        self.move.finished.connect(lambda: self.parent.on_off_button_list_turn_on(without_pushButton_scan=True))
        self.move.move()


def distance(p_A, p_B):
    return np.sqrt((p_A[0] - p_B[0]) ** 2 + (p_A[1] - p_B[1]) ** 2)


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
        print("start move-to-target")
        self.started.emit()
        ratio = distance(self.parent.curr_coords, self.target) / \
                distance(np.array([self.parent.XX[0][0], self.parent.YY[0][0]]),
                         np.array([self.parent.XX[0][-1], self.parent.YY[0][-1]]))

        # for w in self.parent.on_off_button_list:
        #     w.setDisabled(True)

        steps = np.max([int(len(self.parent.XX[0]) * ratio), 1])
        x_array = np.round(np.linspace(self.parent.curr_coords[0], self.target[0], steps), 6)
        y_array = np.round(np.linspace(self.parent.curr_coords[1], self.target[1], steps), 6)
        for i in range(len(x_array)):
            # TODO: if halted, stop for loop
            if (not self.manual_move) and (not self.parent.scan_on_boolean) and (not self.parent.map_on_boolean):
                break
            total_time = 1 / self.parent.frequency / 2 * ratio
            single_time = total_time / steps
            self.parent.curr_coords[0] = x_array[i]
            self.parent.curr_coords[1] = y_array[i]
            sleep(single_time)
            self.single_time = 1 / self.parent.frequency / 2 / len(x_array)
            self.mod_unit = np.max([1, int(0.1 / self.single_time)])
            self.parent.output_voltage_signal.emit()
            if self.counts % self.mod_unit == 0:
                self.parent.update_graphs_signal.emit()
            self.counts += 1
        print("end move-to-target")
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
                     file_path=self.directory + '/' + self.filename)
        self.finished.emit()
        print('save done')
