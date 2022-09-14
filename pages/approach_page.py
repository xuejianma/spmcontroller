from lib.anc300 import ANC300
from lib.niboard import InputVoltageEncoder
from lib.sr8x0 import SR8x0
from pyqtgraph import mkPen
from PyQt5.QtCore import QThread, QTimer, QObject, pyqtSignal
import numpy as np
from time import sleep

class ApproachPage:
    def update_display_approach(self):
        self.widget_linescan_approach_ch1.clear()
        self.widget_linescan_approach_ch2.clear()
        self.widget_linescan_approach_ch1.plot(self.display_list_ch1, pen=mkPen(color=(0, 0, 0)))
        self.widget_linescan_approach_ch2.plot(self.display_list_ch2, pen=mkPen(color=(0, 0, 0)))

    def toggle_display_approach_button(self):
        if self.display_approach_on:
            self.display_approach_on = not self.display_approach_on
            self.pushButton_approach_monitor.setText("START  Display Channel 1 and Channel 2")
        else:
            self.label_error_approach_channels.setText("")
            self.display_approach_on = not self.display_approach_on
            self.pushButton_approach_monitor.setText("STOP  Display Channel 1 and Channel 2")
            self.start_display_approach()

    def toggle_auto_approach_button(self):
        if self.auto_approach_on_boolean:
            self.auto_approach_on_boolean = not self.auto_approach_on_boolean

            self.pushButton_approach_auto_start.setText("START Auto Approach")
        else:
            self.auto_approach_on_boolean = not self.auto_approach_on_boolean
            self.pushButton_approach_auto_start.setText("STOP Auto Approach")
            self.auto_approach()

    def start_display_approach(self):
        self.thread_display_approach = QThread()
        self.approach_display = ApproachDisplay(self)
        self.approach_display.moveToThread(self.thread_display_approach)
        self.thread_display_approach.started.connect(self.approach_display.run)
        self.approach_display.finished.connect(self.approach_display.deleteLater)
        self.approach_display.finished.connect(self.thread_display_approach.exit)
        self.thread_display_approach.finished.connect(self.thread_display_approach.deleteLater)
        self.thread_display_approach.start()

    def clear_approach_monitor(self):
        self.label_error_approach_channels.setText("")
        self.display_list_ch1.clear()
        self.display_list_ch2.clear()
        self.update_display_approach_signal.emit()

    def output_voltage_z_direction(self):
        self.curr_coord_z = np.round(self.doubleSpinBox_z.value(), 6)
        self.output_voltage_z.outputVoltage(self.curr_coord_z +
                                            self.plane_fit.get_delta_z_plane_fitted(self.curr_coords[0],
                                                                                    self.curr_coords[1]))

    def real_time_encoder(self):
        print(self.checkBox_encoder_reading.isChecked())
        if self.checkBox_encoder_reading.isChecked():
            self.thread_encoder = QThread()
            self.input_voltage_encoder = InputVoltageEncoder(
                label_error=self.label_error_encoder, lcdNumber_encoder_reading = self.lcdNumber_encoder_reading,
                checkBox_encoder_reading = self.checkBox_encoder_reading)
            self.input_voltage_encoder.moveToThread(self.thread_encoder)
            self.thread_encoder.started.connect(self.input_voltage_encoder.run)
            # self.input_voltage_encoder.update.connect(
            #     lambda: self.lcdNumber_encoder_reading.display(self.input_voltage_encoder.curr_value))
            self.input_voltage_encoder.finished.connect(self.input_voltage_encoder.deleteLater)
            self.input_voltage_encoder.finished.connect(self.thread_encoder.exit)
            self.thread_encoder.finished.connect(self.thread_encoder.deleteLater)
            self.thread_encoder.start()
        else:
            self.checkBox_encoder_reading.setEnabled(False)
            # the 1100ms delay (disable checkbox) makes sure the self.input_voltage_encoder.run function does not crash
            # as time.sleep(1) in it is lower than 1.05 second, such that
            # "while self.checkBox_encoder_reading.isChecked()" can be checked without a problem when someone try to
            # check and uncheck the checkbox in a very high frequency.
            QTimer.singleShot(1100, lambda: self.checkBox_encoder_reading.setEnabled(True))

    def goto_position_z(self, target):
        self.thread_goto_position_z = QThread()
        self.move = MoveToTargetZ(self, target)
        self.move.moveToThread(self.thread_goto_position_z)
        self.thread_goto_position_z.started.connect(self.move.move)
        self.move.started.connect(lambda: self.goto_position_z_buttons_off(exception=self.pushButton_z_stop_goto))
        self.move.finished.connect(lambda: self.goto_position_z_buttons_on(exception=self.pushButton_z_stop_goto))

        self.move.finished.connect(self.move.deleteLater)
        self.move.finished.connect(self.thread_goto_position_z.exit)
        self.thread_goto_position_z.finished.connect(self.thread_goto_position_z.deleteLater)
        self.thread_goto_position_z.start()

    def goto_position_z_buttons_off(self, exception = None):
        buttons = [
            self.pushButton_z_goto, self.pushButton_z_goto0, self.doubleSpinBox_z, self.doubleSpinBox_z_goto, self.pushButton_positioner_move,
            self.checkBox_auto_approach_tracking_ch1, self.checkBox_auto_approach_tracking_ch2, self.radioButton_auto_approach_up, 
            self.radioButton_auto_approach_down, self.pushButton_approach_auto_start, self.checkBox_positioner_up, self.checkBox_positioner_down,
            self.pushButton_z_stop_goto
        ]
        for w in buttons:
            if w != exception:
                w.setDisabled(True)

    def goto_position_z_buttons_on(self, exception = None):
        buttons = [
            self.pushButton_z_goto, self.pushButton_z_goto0, self.doubleSpinBox_z, self.doubleSpinBox_z_goto, self.pushButton_positioner_move,
            self.checkBox_auto_approach_tracking_ch1, self.checkBox_auto_approach_tracking_ch2, self.radioButton_auto_approach_up, 
            self.radioButton_auto_approach_down, self.pushButton_approach_auto_start, self.checkBox_positioner_up, self.checkBox_positioner_down,
            self.pushButton_z_stop_goto
        ]
        for w in buttons:
            if w != exception:
                w.setEnabled(True)

    def auto_approach(self):
        self.thread_approach = QThread()
        self.approach_auto = AutoApproach(self)
        self.approach_auto.moveToThread(self.thread_approach)
        self.thread_approach.started.connect(self.approach_auto.move)
        self.approach_auto.approached.connect(self.approached_sound.play)
        self.approach_auto.finished.connect(self.approach_auto.deleteLater)
        self.approach_auto.finished.connect(self.thread_approach.exit)
        # self.approach_auto.finishedAfterApproach.connect(self.toggle_auto_approach_button)
        self.thread_approach.finished.connect(self.thread_approach.deleteLater)
        self.thread_approach.start()

    def reconnect_anc300(self):
        try:
            self.anc_controller = ANC300(3)
            self.label_error_approach.setText("")
        except:
            self.anc_controller = None
            self.label_error_approach.setText("🚫 Error: ANC300 hardware not detected!")
            
    def reconnect_lockin(self):
        try:
            self.lockin_top = SR8x0('up')
            self.label_error_lockin_top.setText("")
            self.initialize_lockin_top()
        except:
            self.lockin_top = None
            self.label_error_lockin_top.setText("🚫 SR830/860 (Top) hardware not detected!")

        try:
            self.lockin_bottom = SR8x0('down')
            self.label_error_lockin_bottom.setText("")
            self.initialize_lockin_bottom()
        except Exception as e:
            print(e)
            self.lockin_bottom = None
            self.label_error_lockin_bottom.setText("🚫 SR830/860 (Bottom) hardware not detected!")
            
    def initialize_lockin_top(self):
        self.lockin_top.set_reference_source(self.spinBox_lockin_top_reference.value())
        self.lockin_top.set_frequency(self.doubleSpinBox_lockin_top_reference_internal_frequency.value())
        self.lockin_top.set_time_constant(self.spinBox_lockin_top_time_constant.value())
        self.lockin_top.set_display(1, self.spinBox_lockin_top_display.value())
        self.lockin_top.set_output(1, self.spinBox_lockin_top_output_mode.value())

    def initialize_lockin_bottom(self):
        self.lockin_bottom.set_reference_source(self.spinBox_lockin_bottom_reference.value())
        self.lockin_bottom.set_frequency(self.doubleSpinBox_lockin_bottom_reference_internal_frequency.value())
        self.lockin_bottom.set_time_constant(self.spinBox_lockin_bottom_time_constant.value())
        self.lockin_bottom.set_display(1, self.spinBox_lockin_bottom_display.value())
        self.lockin_bottom.set_output(1, self.spinBox_lockin_bottom_output_mode.value())

    def move_positioner_toggle(self):
        if self.positioner_moving:
            self.anc_controller.stop(4)
            self.checkBox_positioner_up.setDisabled(False)
            self.checkBox_positioner_down.setDisabled(False)
            self.label_positioner_running.setText("")
            self.pushButton_positioner_move.setText("Move")
            self.positioner_moving = False
        else:
            self.pushButton_positioner_move.setDisabled(True)
            self.repaint()
            self.checkBox_positioner_up.setDisabled(True)
            self.checkBox_positioner_down.setDisabled(True)
            self.pushButton_positioner_move.setText("Stop")
            self.positioner_moving = True
            try:
                if self.checkBox_positioner_up.isChecked():
                    self.anc_controller.stepu(4, 'c')
                else:
                    self.anc_controller.stepd(4, 'c')
                self.label_positioner_running.setText("Moving...")
            except:
                self.label_positioner_running.setText("🚫 Error: Positioner Off")
                # to stop auto approach when Moving positioner is excuted in AutoApproach module
                self.auto_approach_on_boolean = False
                self.checkBox_positioner_up.setDisabled(False)
                self.checkBox_positioner_down.setDisabled(False)
                self.pushButton_positioner_move.setText("Move")
                self.positioner_moving = False
            self.pushButton_positioner_move.setDisabled(False)
    
    def manual_z_goto_boolean_to_false(self):
        self.manual_z_goto_boolean = False
    
    def set_z_max(self):
        self.doubleSpinBox_z.setMaximum(self.doubleSpinBox_z_piezo_limit.value())
        self.doubleSpinBox_z_goto.setMaximum(self.doubleSpinBox_z_piezo_limit.value())
        self.doubleSpinBox_scanner_voltage_per_turn.setMaximum(self.doubleSpinBox_z_piezo_limit.value())

class ApproachDisplay(QObject):
    finished = pyqtSignal()
    def __init__(self, parent):
        super(ApproachDisplay, self).__init__()
        self.max_count = 600
        self.parent = parent
    def run(self):
        while self.parent.display_approach_on:
            sleep(0.1)
            ch1, ch2 = self.parent.get_voltage_ch1_ch2()
            # print(ch1, ch2)
            if len(self.parent.display_list_ch1) == self.max_count:
                self.parent.display_list_ch1.pop(0)
                self.parent.display_list_ch2.pop(0)
            self.parent.display_list_ch1.append(ch1)
            self.parent.display_list_ch2.append(ch2)
            self.parent.update_display_approach_signal.emit()
        self.finished.emit()


class AutoApproach(QObject):
    finished = pyqtSignal()
    finishedAfterApproach = pyqtSignal()
    approached = pyqtSignal()
    def __init__(self, parent):
        super(AutoApproach, self).__init__()
        self.parent = parent
        self.store_ch1 = []
        self.store_ch2 = []
        self.max_placeholder = 1e6
        self.average_ch1 = self.max_placeholder
        self.average_ch2 = self.max_placeholder
        self.threshold = 0.15
        self.counts = 10


    def move(self):
        if self.parent.radioButton_auto_approach_up.isChecked():
            self.move_up()
        else:
            self.move_down()

    def move_up(self):
        # print("auto start")
        self.parent.checkBox_positioner_up.setChecked(True)
        if not self.parent.display_approach_on:
            self.parent.toggle_display_approach_button()

        self.parent.goto_position_z_buttons_off(exception=self.parent.pushButton_approach_auto_start)
        self.parent.pushButton_approach_monitor.setDisabled(True)
        while self.parent.auto_approach_on_boolean:
            self.store_ch1 = []
            self.store_ch2 = []
            self.average_ch1 = self.max_placeholder
            self.average_ch2 = self.max_placeholder
            #scanner z moving up
            self.move = MoveToTargetZ(self.parent, self.parent.doubleSpinBox_scanner_voltage_per_turn.value(),
                                      auto_approach = True, parent_finished_signal = self.finished,
                                      parent_finishedAfterApproach_signal = self.finishedAfterApproach,
                                      auto_approach_obj = self)
            # self.finishedAfterApproach.connect(self.parent.toggle_auto_approach_button)
            self.move.move()
            #scanner z moving down
            sleep(0.2)
            if not self.parent.auto_approach_on_boolean:
                break
            self.move = MoveToTargetZ(self.parent, 0.0,
                                      auto_approach=True, parent_finished_signal=self.finished,
                                      parent_finishedAfterApproach_signal=self.finishedAfterApproach)
            # self.finishedAfterApproach.connect(self.parent.toggle_auto_approach_button)
            self.move.move()
            #positioner z moving up
            if not self.parent.auto_approach_on_boolean:
                break
            # self.parent.checkBox_positioner_up.setChecked(True)
            self.parent.move_positioner_toggle()
            if not self.parent.auto_approach_on_boolean:
                break
            sleep(self.parent.doubleSpinBox_positioner_time_per_turn.value())
            self.parent.move_positioner_toggle()
            sleep(0.2)
            # # positioner z moving down
            # if not self.parent.auto_approach_on_boolean:
            #     break
            # self.parent.checkBox_positioner_down.setChecked(True)
            # self.parent.move_positioner_toggle()
            # if not self.parent.auto_approach_on_boolean:
            #     break
            # time.sleep(self.parent.doubleSpinBox_positioner_time_per_turn.value())
            # self.parent.move_positioner_toggle()


        self.parent.goto_position_z_buttons_on(exception=self.parent.pushButton_approach_auto_start)
        if not self.parent.auto_approach_on_boolean:
            self.parent.auto_approach_on_boolean = True
            self.parent.toggle_auto_approach_button()
        self.parent.pushButton_approach_monitor.setEnabled(True)

        self.finished.emit()


    def move_down(self):
        self.parent.checkBox_positioner_down.setChecked(True)
        if not self.parent.display_approach_on:
            self.parent.toggle_display_approach_button()

        self.parent.goto_position_z_buttons_off(exception=self.parent.pushButton_approach_auto_start)
        self.parent.pushButton_approach_monitor.setDisabled(True)
        while self.parent.auto_approach_on_boolean:
            self.store_ch1 = []
            self.store_ch2 = []
            self.average_ch1 = self.max_placeholder
            self.average_ch2 = self.max_placeholder
            #scanner z moving down
            self.move = MoveToTargetZ(self.parent, 0.0,
                                      auto_approach = True, parent_finished_signal = self.finished,
                                      parent_finishedAfterApproach_signal = self.finishedAfterApproach,
                                      auto_approach_obj = self)
            self.move.move()
            #scanner z moving up
            sleep(0.2)
            if not self.parent.auto_approach_on_boolean:
                break
            self.move = MoveToTargetZ(self.parent, self.parent.doubleSpinBox_scanner_voltage_per_turn.value(),
                                      auto_approach=True, parent_finished_signal=self.finished,
                                      parent_finishedAfterApproach_signal=self.finishedAfterApproach)
            # self.finishedAfterApproach.connect(self.parent.toggle_auto_approach_button)
            self.move.move()
            #positioner z moving up
            if not self.parent.auto_approach_on_boolean:
                break
            # self.parent.checkBox_positioner_down.setChecked(True)
            self.parent.move_positioner_toggle()
            if not self.parent.auto_approach_on_boolean:
                break
            sleep(self.parent.doubleSpinBox_positioner_time_per_turn.value())
            self.parent.move_positioner_toggle()
            sleep(0.2)
        self.parent.goto_position_z_buttons_on(exception=self.parent.pushButton_approach_auto_start)
        if not self.parent.auto_approach_on_boolean:
            self.parent.auto_approach_on_boolean = True
            self.parent.toggle_auto_approach_button()
        self.parent.pushButton_approach_monitor.setEnabled(True)
        self.finished.emit()

    def check_approached(self):

        if len(self.parent.display_list_ch1) == 0:
            return False
        curr_ch1 = self.parent.display_list_ch1[-1]
        curr_ch2 = self.parent.display_list_ch2[-1]

        # print(self.average_ch1, self.average_ch2, np.abs((curr_ch1 - self.average_ch1) / self.average_ch1), np.abs((curr_ch2 - self.average_ch2) / self.average_ch2))
        # print(curr_ch1)
        if len(self.store_ch1) >= self.counts:
            if (self.parent.checkBox_auto_approach_tracking_ch1.isChecked() and
                np.abs((curr_ch1 - self.average_ch1) / self.average_ch1) > self.threshold) or \
                (self.parent.checkBox_auto_approach_tracking_ch2.isChecked() and
                 np.abs((curr_ch2 - self.average_ch2) / self.average_ch2) > self.threshold):
                self.parent.auto_approach_on_boolean = False
                return True
            out_ch1 = self.store_ch1.pop(0)
            out_ch2 = self.store_ch2.pop(0)
            self.store_ch1.append(curr_ch1)
            self.store_ch2.append(curr_ch2)
            self.average_ch1 = (self.average_ch1 * self.counts - out_ch1 + curr_ch1) / self.counts
            self.average_ch2 = (self.average_ch2 * self.counts - out_ch2 + curr_ch2) / self.counts
        else:
            self.store_ch1.append(curr_ch1)
            self.store_ch2.append(curr_ch2)
            if self.average_ch1 == self.max_placeholder:
                self.average_ch1 = curr_ch1
                self.average_ch2 = curr_ch2
            else:
                self.average_ch1 = (self.average_ch1 * (len(self.store_ch1) - 1) + curr_ch1) / len(self.store_ch1)
                self.average_ch2 = (self.average_ch2 * (len(self.store_ch2) - 1) + curr_ch2) / len(self.store_ch2)

        return False


class MoveToTargetZ(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    def __init__(self, parent, target, auto_approach = False, parent_finished_signal = None,
                 parent_finishedAfterApproach_signal = None, auto_approach_obj = None):
        super(MoveToTargetZ, self).__init__()
        self.target = target
        self.parent = parent
        self.auto_approach = auto_approach
        self.parent_finished_signal = parent_finished_signal
        self.parent_finishedAfterApproach_signal = parent_finishedAfterApproach_signal
        self.delta = 0.1 if self.target >= self.parent.curr_coord_z else -0.1
        self.array = np.round(np.arange(self.parent.curr_coord_z, self.target + self.delta, self.delta), 6)
        self.auto_approach_obj = auto_approach_obj
    def move(self):
        if not self.auto_approach:
            self.parent.manual_z_goto_boolean = True
        self.started.emit()
        for val in self.array:
            if self.auto_approach_obj is not None:
                if self.auto_approach_obj.check_approached():
                    self.auto_approach_obj.approached.emit()
            if self.auto_approach and not self.parent.auto_approach_on_boolean:
                break
            if not self.auto_approach and not self.parent.manual_z_goto_boolean:
                break
            # print(val)
            self.parent.curr_coord_z = val
            self.parent.doubleSpinBox_z.setValue(self.parent.curr_coord_z)
            self.parent.output_voltage_z_direction()
            sleep(0.05)
        # if self.parent_finished_signal is not None:
        #     self.parent_finished_signal.emit()
        # if self.parent_finished_signal is not None and self.parent.auto_approach_on_boolean:
        #     self.parent_finishedAfterApproach_signal.emit()

        self.finished.emit()
