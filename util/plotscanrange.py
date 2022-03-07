import numpy as np

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
                                           cmap='afmhot', shading='auto')
                    else:
                        subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch1'],
                                           cmap='afmhot', vmin=self.doubleSpinBox_colorbar_manual_min_main.value(),
                                           vmax=self.doubleSpinBox_colorbar_manual_max_main.value(), shading='auto')
                else:
                    if len(self.map_retrace['XX']) != 0:
                        if not self.colorbar_manual_main:
                            subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'],
                                               cmap='afmhot', shading='auto')
                        else:
                            subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'],
                                               cmap='afmhot', vmin=self.doubleSpinBox_colorbar_manual_min_main.value(),
                                               vmax=self.doubleSpinBox_colorbar_manual_max_main.value(), shading='auto')
            else:
                if self.radioButton_main_trace.isChecked():
                    if not self.colorbar_manual_main:
                        subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'],
                                           cmap='afmhot', shading='auto')
                    else:
                        subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'],
                                           cmap='afmhot', vmin=self.doubleSpinBox_colorbar_manual_min_main.value(),
                                           vmax=self.doubleSpinBox_colorbar_manual_max_main.value(), shading='auto')
                else:
                    if len(self.map_retrace['XX']) != 0:
                        if not self.colorbar_manual_main:
                            subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'],
                                               cmap='afmhot', shading='auto')
                        else:
                            subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'],
                                               cmap='afmhot', vmin=self.doubleSpinBox_colorbar_manual_min_main.value(),
                                               vmax=self.doubleSpinBox_colorbar_manual_max_main.value(), shading='auto')
        elif widget == self.widget_display_scan_window_ch1:
            if self.radioButton_ch1_trace.isChecked():
                if not self.colorbar_manual_ch1:
                    subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch1'], cmap='afmhot', shading='auto')
                else:
                    subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch1'], cmap='afmhot',
                                       vmin=self.doubleSpinBox_colorbar_manual_min_ch1.value(),
                                       vmax=self.doubleSpinBox_colorbar_manual_max_ch1.value(), shading='auto')
            else:
                if len(self.map_retrace['XX']) != 0:
                    if not self.colorbar_manual_ch1:
                        subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'],
                                           cmap='afmhot', shading='auto')
                    else:
                        subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch1'],
                                           cmap='afmhot',vmin=self.doubleSpinBox_colorbar_manual_min_ch1.value(),
                                           vmax=self.doubleSpinBox_colorbar_manual_max_ch1.value(), shading='auto')
        elif widget == self.widget_display_scan_window_ch2:
            if self.radioButton_ch2_trace.isChecked():
                if not self.colorbar_manual_ch2:
                    subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'], cmap='afmhot', shading='auto')
                else:
                    subplot.pcolormesh(self.map_trace['XX'], self.map_trace['YY'], self.map_trace['ch2'], cmap='afmhot',
                                       vmin=self.doubleSpinBox_colorbar_manual_min_ch2.value(),
                                       vmax=self.doubleSpinBox_colorbar_manual_max_ch2.value(), shading='auto')
            else:
                if len(self.map_retrace['XX']) != 0:
                    if not self.colorbar_manual_ch2:
                        subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'],
                                            cmap='afmhot', shading='auto')
                    else:
                        subplot.pcolormesh(self.map_retrace['XX'], self.map_retrace['YY'], self.map_retrace['ch2'],
                                           cmap='afmhot', vmin=self.doubleSpinBox_colorbar_manual_min_ch2.value(),
                                           vmax=self.doubleSpinBox_colorbar_manual_max_ch2.value(), shading='auto')

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
        update_graphs(self, single='main')
        self.doubleSpinBox_colorbar_manual_min_main.setDisabled(False)
        self.doubleSpinBox_colorbar_manual_max_main.setDisabled(False)
    else:
        self.colorbar_manual_main = False
        update_graphs(self, single='main')
        self.doubleSpinBox_colorbar_manual_min_main.setDisabled(True)
        self.doubleSpinBox_colorbar_manual_max_main.setDisabled(True)

def toggle_colorbar_ch1(self):
    if self.radioButton_colorbar_manual_ch1.isChecked():
        self.colorbar_manual_ch1 = True
        update_graphs(self, single='ch1')
        self.doubleSpinBox_colorbar_manual_min_ch1.setDisabled(False)
        self.doubleSpinBox_colorbar_manual_max_ch1.setDisabled(False)
    else:
        self.colorbar_manual_ch1 = False
        update_graphs(self, single='ch1')
        self.doubleSpinBox_colorbar_manual_min_ch1.setDisabled(True)
        self.doubleSpinBox_colorbar_manual_max_ch1.setDisabled(True)

def toggle_colorbar_ch2(self):
    if self.radioButton_colorbar_manual_ch2.isChecked():
        self.colorbar_manual_ch2 = True
        update_graphs(self, single='ch2')
        self.doubleSpinBox_colorbar_manual_min_ch2.setDisabled(False)
        self.doubleSpinBox_colorbar_manual_max_ch2.setDisabled(False)
    else:
        self.colorbar_manual_ch2 = False
        update_graphs(self, single='ch2')
        self.doubleSpinBox_colorbar_manual_min_ch2.setDisabled(True)
        self.doubleSpinBox_colorbar_manual_max_ch2.setDisabled(True)
def update_graphs(self, single='all'):
        xlim_min = np.min([self.p1[0], self.p2[0], self.p3[0], self.p4[0]])
        xlim_max = np.max([self.p1[0], self.p2[0], self.p3[0], self.p4[0]])
        ylim_min = np.min([self.p1[1], self.p2[1], self.p3[1], self.p4[1]])
        ylim_max = np.max([self.p1[1], self.p2[1], self.p3[1], self.p4[1]])
        if single == 'all' or single == 'main':
                plot_scan_range(self, self.widget_display_piezo_limit, xlim_min=0, xlim_max=self.piezo_limit_x, ylim_min=0,
                                        ylim_max=self.piezo_limit_y)
        if single == 'all' or single == 'ch1':
                plot_scan_range(self, self.widget_display_scan_window_ch1, xlim_min=xlim_min, xlim_max=xlim_max,
                                        ylim_min=ylim_min,
                                        ylim_max=ylim_max)
        if single == 'all' or single == 'ch2':
                plot_scan_range(self, self.widget_display_scan_window_ch2, xlim_min=xlim_min, xlim_max=xlim_max,
                                        ylim_min=ylim_min,
                                        ylim_max=ylim_max)