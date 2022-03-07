from pyqtgraph import mkPen

def update_display_approach(self):
    self.widget_linescan_approach_ch1.clear()
    self.widget_linescan_approach_ch2.clear()
    self.widget_linescan_approach_ch1.plot(self.display_list_ch1, pen=mkPen(color=(0, 0, 0)))
    self.widget_linescan_approach_ch2.plot(self.display_list_ch2, pen=mkPen(color=(0, 0, 0)))