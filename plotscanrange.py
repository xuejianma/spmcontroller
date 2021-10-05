

def plot_scan_range(self, widget, xlim_min, xlim_max, ylim_min, ylim_max):
    widget.getFigure().clear()
    subplot = widget.getFigure().subplots()
    subplot.set_aspect(1)
    subplot.set_facecolor('black')
    subplot.set_xlim(xlim_min, xlim_max)
    subplot.set_ylim(ylim_min, ylim_max)
    subplot.invert_xaxis()
    subplot.invert_yaxis()
    subplot.plot([0, self.piezo_limit_x], [0, 0], '--', c='white')
    subplot.plot([self.piezo_limit_x, self.piezo_limit_x], [0, self.piezo_limit_y], '--', c='white')
    subplot.plot([self.piezo_limit_x, 0], [self.piezo_limit_y, self.piezo_limit_y], '--', c='white')
    subplot.plot([0, 0], [self.piezo_limit_y, 0], '--', c='white')
    if (len(self.data_store) > 0):
        subplot.pcolormesh(self.data_store[self.data_choose][0], self.data_store[self.data_choose][1],
                           self.data_store[self.data_choose][self.channel_choose + 1], cmap="afmhot")

    exceeds_limit = False

    for p in [self.p1, self.p2, self.p3, self.p4]:
        if p[0] > self.piezo_limit_x or p[0] < 0 or p[1] > self.piezo_limit_y or p[1] < 0:
            exceeds_limit = True
    if widget == self.widget_display_piezo_limit:
        if exceeds_limit:
            self.error_lock = True
            self.label_error.setText(self.error_lock_text)
        else:
            self.error_lock = False
            self.label_error.setText("")
    if len(self.map_trace['XX']) != 0:
        if widget == self.widget_display_piezo_limit:
            if self.radioButton_main_ch1.isChecked():
                if self.radioButton_main_trace.isChecked():
                    if not self.colorbar_manual_main:
                        subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch1'],
                                           cmap='afmhot')
                    else:
                        subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch1'],
                                           cmap='afmhot', vmin=self.doubleSpinBox_colorbar_manual_min_main.value(),
                                           vmax=self.doubleSpinBox_colorbar_manual_max_main.value())
                else:
                    if not self.colorbar_manual_main:
                        subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'],
                                           cmap='afmhot')
                    else:
                        subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'],
                                           cmap='afmhot', vmin=self.doubleSpinBox_colorbar_manual_min_main.value(),
                                           vmax=self.doubleSpinBox_colorbar_manual_max_main.value())
            else:
                if self.radioButton_main_trace.isChecked():
                    if not self.colorbar_manual_main:
                        subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'],
                                           cmap='afmhot')
                    else:
                        subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'],
                                           cmap='afmhot', vmin=self.doubleSpinBox_colorbar_manual_min_main.value(),
                                           vmax=self.doubleSpinBox_colorbar_manual_max_main.value())
                else:
                    if not self.colorbar_manual_main:
                        subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'],
                                           cmap='afmhot')
                    else:
                        subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'],
                                           cmap='afmhot', vmin=self.doubleSpinBox_colorbar_manual_min_main.value(),
                                           vmax=self.doubleSpinBox_colorbar_manual_max_main.value())
        elif widget == self.widget_display_scan_window_ch1:
            if self.radioButton_ch1_trace.isChecked():
                if not self.colorbar_manual_ch1:
                    subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch1'], cmap='afmhot')
                else:
                    subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch1'], cmap='afmhot',
                                       vmin=self.doubleSpinBox_colorbar_manual_min_ch1.value(),
                                       vmax=self.doubleSpinBox_colorbar_manual_max_ch1.value())
            else:
                if not self.colorbar_manual_ch1:
                    subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'],
                                       cmap='afmhot')
                else:
                    subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'],
                                       cmap='afmhot',vmin=self.doubleSpinBox_colorbar_manual_min_ch1.value(),
                                       vmax=self.doubleSpinBox_colorbar_manual_max_ch1.value())
        elif widget == self.widget_display_scan_window_ch2:
            if self.radioButton_ch2_trace.isChecked():
                if not self.colorbar_manual_ch2:
                    subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'], cmap='afmhot')
                else:
                    subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'], cmap='afmhot',
                                       vmin=self.doubleSpinBox_colorbar_manual_min_ch2.value(),
                                       vmax=self.doubleSpinBox_colorbar_manual_max_ch2.value())
            else:
                if not self.colorbar_manual_ch2:
                    subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'],
                                        cmap='afmhot')
                else:
                    subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'],
                                       cmap='afmhot', vmin=self.doubleSpinBox_colorbar_manual_min_ch2.value(),
                                       vmax=self.doubleSpinBox_colorbar_manual_max_ch2.value())

    subplot.plot([self.p1[0], self.p2[0]], [self.p1[1], self.p2[1]], '--', linewidth=3,
                 c='red' if exceeds_limit else 'orange')
    subplot.plot([self.p2[0], self.p3[0]], [self.p2[1], self.p3[1]], '--', linewidth=3,
                 c='red' if exceeds_limit else 'green')
    subplot.plot([self.p3[0], self.p4[0]], [self.p3[1], self.p4[1]], '--', linewidth=3,
                 c='red' if exceeds_limit else 'green')
    subplot.plot([self.p4[0], self.p1[0]], [self.p4[1], self.p1[1]], '--', linewidth=3,
                 c='red' if exceeds_limit else 'green')
    subplot.plot([self.p1[0]], [self.p1[1]], '.', markersize=20, c='red')
    widget.draw()

def toggle_colorbar_main(self):
    if self.radioButton_colorbar_manual_main.isChecked():
        self.colorbar_manual_main = True
        self.update_graphs(single='main')
        self.doubleSpinBox_colorbar_manual_min_main.setDisabled(False)
        self.doubleSpinBox_colorbar_manual_max_main.setDisabled(False)
    else:
        self.colorbar_manual_main = False
        self.update_graphs(single='main')
        self.doubleSpinBox_colorbar_manual_min_main.setDisabled(True)
        self.doubleSpinBox_colorbar_manual_max_main.setDisabled(True)

def toggle_colorbar_ch1(self):
    if self.radioButton_colorbar_manual_ch1.isChecked():
        self.colorbar_manual_ch1 = True
        self.update_graphs(single='ch1')
        self.doubleSpinBox_colorbar_manual_min_ch1.setDisabled(False)
        self.doubleSpinBox_colorbar_manual_max_ch1.setDisabled(False)
    else:
        self.colorbar_manual_ch1 = False
        self.update_graphs(single='ch1')
        self.doubleSpinBox_colorbar_manual_min_ch1.setDisabled(True)
        self.doubleSpinBox_colorbar_manual_max_ch1.setDisabled(True)

def toggle_colorbar_ch2(self):
    if self.radioButton_colorbar_manual_ch2.isChecked():
        self.colorbar_manual_ch2 = True
        self.update_graphs(single='ch2')
        self.doubleSpinBox_colorbar_manual_min_ch2.setDisabled(False)
        self.doubleSpinBox_colorbar_manual_max_ch2.setDisabled(False)
    else:
        self.colorbar_manual_ch2 = False
        self.update_graphs(single='ch2')
        self.doubleSpinBox_colorbar_manual_min_ch2.setDisabled(True)
        self.doubleSpinBox_colorbar_manual_max_ch2.setDisabled(True)