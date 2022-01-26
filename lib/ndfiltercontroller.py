from time import sleep

from PyQt5.QtCore import QObject, pyqtSignal


class NDFilterController:
    def __init__(self):
        self.angle = 0
    def get_angle(self):
        return self.angle

class NDFilterChange(QObject):
    finished = pyqtSignal()
    progress_update = pyqtSignal()
    def __init__(self, parent, ndfilter_controller, angle):
        super(NDFilterChange, self).__init__()
        self.ndfilter_controller = ndfilter_controller
        self.parent = parent
        self.angle = angle
        self.progress = 100

    def set_angle(self):
        sleep_time = 0.1 * abs(self.angle - self.ndfilter_controller.angle) # simulate hardware response time
        for i in range(20):
            if not self.parent.laser_ndfilter_changing:
                self.progress = 100
                self.progress_update.emit()
                self.finished.emit()
                return
            sleep(sleep_time / 20)
            self.progress = (i + 1) * 5
            self.progress_update.emit()

        # if not self.parent.ndfilter_controller_changing:
        #   return
        self.ndfilter_controller.angle = self.angle

        self.finished.emit()
