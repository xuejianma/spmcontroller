"""
thorlab_apt package from https://github.com/qpit/thorlabs_apt
"""
try:
    # thorlab_apt package from https://github.com/qpit/thorlabs_apt.
    # Sometimes this will crash the program without giving any error
    # message even with print(e). Starting thorlab's Kinesis program 
    # and closing it can solve the problem.
    import thorlabs_apt as apt
except Exception as e:
    print(e)
from time import sleep

from PyQt5.QtCore import QObject, pyqtSignal


class NDFilterController:
    def __init__(self, serial_number = 55254094):
        try:
            self.motor = apt.Motor(serial_number)
        except Exception as e:
            print(e)
        # self.angle = 0
    def get_angle(self):
        return self.motor.position
    # def move_to_angle(self, target_angle):
    #     self.motor.move_to(target_angle)
    #     while self.motor.is_in_motion:
    #         pass
    #     return

class NDFilterChange(QObject):
    finished = pyqtSignal()
    progress_update = pyqtSignal()
    def __init__(self, parent, ndfilter_controller, angle, move_home = False):
        super(NDFilterChange, self).__init__()
        self.ndfilter_controller = ndfilter_controller
        self.parent = parent
        self.angle = angle
        self.progress = 100
        self.move_home = move_home

    def set_angle(self):
        # sleep_time = 0.1 * abs(self.angle - self.ndfilter_controller.angle) # simulate hardware response time
        # for i in range(20):
        #     if not self.parent.laser_ndfilter_changing:
        #         self.progress = 100
        #         self.progress_update.emit()
        #         self.finished.emit()
        #         return
        #     sleep(sleep_time / 20)
        #     self.progress = (i + 1) * 5
        #     self.progress_update.emit()
        # self.ndfilter_controller.move_to_angle(self.angle)
        prev_angle = self.ndfilter_controller.get_angle()
        self.ndfilter_controller.motor.move_to(self.angle)
        while self.ndfilter_controller.motor.is_in_motion:
            sleep(0.1)
            curr_angle = self.ndfilter_controller.get_angle()
            self.progress = int((curr_angle - prev_angle) / (self.angle - prev_angle) * 100) if self.angle != prev_angle else 0
            self.progress_update.emit()
        self.progress = 100
        self.progress_update.emit()
        # pass
        # if not self.parent.ndfilter_controller_changing:
        #   return
        # self.ndfilter_controller.angle = self.angle
        self.finished.emit()



# class NDFilterController:
#     def __init__(self):
#         self.angle = 0
#     def get_angle(self):
#         return self.angle

# class NDFilterChange(QObject):
#     finished = pyqtSignal()
#     progress_update = pyqtSignal()
#     def __init__(self, parent, ndfilter_controller, angle):
#         super(NDFilterChange, self).__init__()
#         self.ndfilter_controller = ndfilter_controller
#         self.parent = parent
#         self.angle = angle
#         self.progress = 100

#     def set_angle(self):
#         sleep_time = 0.1 * abs(self.angle - self.ndfilter_controller.angle) # simulate hardware response time
#         for i in range(20):
#             if not self.parent.laser_ndfilter_changing:
#                 self.progress = 100
#                 self.progress_update.emit()
#                 self.finished.emit()
#                 return
#             sleep(sleep_time / 20*2)
#             self.progress = (i + 1) * 5
#             self.progress_update.emit()

#         # if not self.parent.ndfilter_controller_changing:
#         #   return
#         self.ndfilter_controller.angle = self.angle

#         self.finished.emit()
