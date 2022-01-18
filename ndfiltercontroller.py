from time import sleep

from PyQt5.QtCore import QObject, pyqtSignal


class NDFilterController:
    def __init__(self):
        self.angle = 0
    def get_angle(self):
        return self.angle

class NDFilterChange(QObject):
    finished = pyqtSignal()
    def __init__(self, parent, ndfilter_controller, angle):
        super(NDFilterChange, self).__init__()
        self.ndfilter_controller = ndfilter_controller
        self.parent = parent
        self.angle = angle

    def set_angle(self):
        sleep(0.1 * (self.angle - self.ndfilter_controller.angle)) # simulate hardware response time
        # if not self.parent.ndfilter_controller_changing:
        #   return
        self.ndfilter_controller.angle = self.angle
        self.finished.emit()
