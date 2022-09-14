import numpy as np
class Connect:
    
    def connect_all(self):
        '''
        keyboardTracking of all edges has been set to False in form.ui. Thus valueChanged is only triggered after Enter.
        '''
        self.doubleSpinBox_piezo_limit_x.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_piezo_limit_y.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_x_min.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_x_max.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_y_min.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_y_max.valueChanged.connect(self.determine_scan_window)
        self.spinBox_x_pixels.valueChanged.connect(self.determine_scan_window)
        self.spinBox_y_pixels.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_frequency.valueChanged.connect(self.determine_scan_window)
        self.doubleSpinBox_rotation.valueChanged.connect(self.determine_scan_window)
        self.update_graphs_signal.connect(self.update_voltage)
        # self.output_voltage_signal.connect(self.output_voltage)
        self.pushButton_scan.clicked.connect(self.toggle_scan_button)
        self.pushButton_goto0.clicked.connect(lambda: self.goto_position(np.array([0, 0])))
        self.pushButton_goto.clicked.connect(lambda: self.goto_position(np.array([self.doubleSpinBox_goto_x.value(),
                                                                                  self.doubleSpinBox_goto_y.value()])))
        self.pushButton_stop_goto.clicked.connect(self.manual_goto_boolean_to_false)
        self.checkBox_maintenance.toggled.connect(self.toggle_maintenance)
        self.doubleSpinBox_current_x.editingFinished.connect(self.update_voltage_maintenance_x)
        self.doubleSpinBox_current_y.editingFinished.connect(self.update_voltage_maintenance_y)
        self.pushButton_image.clicked.connect(self.toggle_map_button)
        self.pushButton_show_newer.clicked.connect(self.show_newer_image)
        self.pushButton_show_older.clicked.connect(self.show_older_image)
        self.buttonGroup.buttonToggled.connect(lambda: self.update_graphs(single='main'))
        self.buttonGroup_2.buttonToggled.connect(lambda: self.update_graphs(single='main'))
        self.buttonGroup_3.buttonToggled.connect(lambda: self.update_graphs(single='ch1'))
        self.buttonGroup_4.buttonToggled.connect(lambda: self.update_graphs(single='ch2'))

        self.buttonGroup_5.buttonToggled.connect(self.toggle_colorbar_main)
        self.doubleSpinBox_colorbar_manual_min_main.valueChanged.connect(self.toggle_colorbar_main)
        self.doubleSpinBox_colorbar_manual_max_main.valueChanged.connect(self.toggle_colorbar_main)

        self.buttonGroup_6.buttonToggled.connect(self.toggle_colorbar_ch1)
        self.doubleSpinBox_colorbar_manual_min_ch1.valueChanged.connect(self.toggle_colorbar_ch1)
        self.doubleSpinBox_colorbar_manual_max_ch1.valueChanged.connect(self.toggle_colorbar_ch1)

        self.buttonGroup_7.buttonToggled.connect(self.toggle_colorbar_ch2)
        self.doubleSpinBox_colorbar_manual_min_ch2.valueChanged.connect(self.toggle_colorbar_ch2)
        self.doubleSpinBox_colorbar_manual_max_ch2.valueChanged.connect(self.toggle_colorbar_ch2)

        self.pushButton_directory.clicked.connect(self.selectDirectory)
        self.doubleSpinBox_z.valueChanged.connect(self.output_voltage_z_direction)
        self.doubleSpinBox_z_piezo_limit.valueChanged.connect(self.set_z_max)
        self.pushButton_reconnect_hardware.clicked.connect(self.hardware_io)

        # self.comboBox_anc300.currentIndexChanged.connect(self.choose_anc300)
        self.pushButton_reconnect_anc300.clicked.connect(self.reconnect_anc300)
        self.pushButton_positioner_on.clicked.connect(lambda: self.anc_controller.setm(4, "stp"))
        self.pushButton_positioner_off.clicked.connect(lambda: self.anc_controller.setm(4, "gnd"))
        self.pushButton_positioner_off.clicked.connect(
            lambda: self.move_positioner_toggle() if self.positioner_moving else None)
        self.pushButton_scanner_x_dc_on.clicked.connect(lambda: self.anc_controller.setdci(1, "on"))
        self.pushButton_scanner_x_dc_off.clicked.connect(lambda: self.anc_controller.setdci(1, "off"))
        self.pushButton_scanner_y_dc_on.clicked.connect(lambda: self.anc_controller.setdci(2, "on"))
        self.pushButton_scanner_y_dc_off.clicked.connect(lambda: self.anc_controller.setdci(2, "off"))
        self.pushButton_scanner_z_dc_on.clicked.connect(lambda: self.anc_controller.setdci(3, "on"))
        self.pushButton_scanner_z_dc_off.clicked.connect(lambda: self.anc_controller.setdci(3, "off"))
        self.pushButton_scanner_x_ac_on.clicked.connect(lambda: self.anc_controller.setaci(1, "on"))
        self.pushButton_scanner_x_ac_off.clicked.connect(lambda: self.anc_controller.setaci(1, "off"))
        self.pushButton_scanner_y_ac_on.clicked.connect(lambda: self.anc_controller.setaci(2, "on"))
        self.pushButton_scanner_y_ac_off.clicked.connect(lambda: self.anc_controller.setaci(2, "off"))
        self.pushButton_scanner_z_ac_on.clicked.connect(lambda: self.anc_controller.setaci(3, "on"))
        self.pushButton_scanner_z_ac_off.clicked.connect(lambda: self.anc_controller.setaci(3, "off"))

        self.pushButton_positioner_move.clicked.connect(self.move_positioner_toggle)
        self.spinBox_positioner_frequency.valueChanged.connect(
            lambda: self.anc_controller.setf(4, self.spinBox_positioner_frequency.value()))
        self.doubleSpinBox_positioner_amplitude.valueChanged.connect(
            lambda: self.anc_controller.setv(4, self.doubleSpinBox_positioner_amplitude.value()))

        self.pushButton_reconnect_lockin.clicked.connect(self.reconnect_lockin)
        #SR830 Top:
        self.spinBox_lockin_top_reference.valueChanged.connect(
            lambda: self.lockin_top.set_reference_source(self.spinBox_lockin_top_reference.value()))
        self.doubleSpinBox_lockin_top_reference_internal_frequency.valueChanged.connect(
            lambda: self.lockin_top.set_frequency(self.doubleSpinBox_lockin_top_reference_internal_frequency.value()))
        self.spinBox_lockin_top_time_constant.valueChanged.connect(
            lambda: self.lockin_top.set_time_constant(self.spinBox_lockin_top_time_constant.value()))
        self.spinBox_lockin_top_display.valueChanged.connect(
            lambda: self.lockin_top.set_display(1, self.spinBox_lockin_top_display.value()))
        self.spinBox_lockin_top_output_mode.valueChanged.connect(
            lambda: self.lockin_top.set_output(1, self.spinBox_lockin_top_output_mode.value()))
        #SR830 Bottom:
        self.spinBox_lockin_bottom_reference.valueChanged.connect(
            lambda: self.lockin_bottom.set_reference_source(self.spinBox_lockin_bottom_reference.value()))
        self.doubleSpinBox_lockin_bottom_reference_internal_frequency.valueChanged.connect(
            lambda: self.lockin_bottom.set_frequency(self.doubleSpinBox_lockin_bottom_reference_internal_frequency.value()))
        self.spinBox_lockin_bottom_time_constant.valueChanged.connect(
            lambda: self.lockin_bottom.set_time_constant(self.spinBox_lockin_bottom_time_constant.value()))
        self.spinBox_lockin_bottom_display.valueChanged.connect(
            lambda: self.lockin_bottom.set_display(1, self.spinBox_lockin_bottom_display.value()))
        self.spinBox_lockin_bottom_output_mode.valueChanged.connect(
            lambda: self.lockin_bottom.set_output(1, self.spinBox_lockin_bottom_output_mode.value()))

        # self.pushButton_reconnect_lockin.clicked.connect(self.reconnect_anc300) # commented since it may be typo
        # start display for approach
        self.pushButton_approach_monitor.clicked.connect(self.toggle_display_approach_button)
        self.pushButton_approach_monitor_clear.clicked.connect(self.clear_approach_monitor)
        self.radioButton_channel_source_niboard_in_approach_page.toggled.connect(self.set_channel_signal_source_in_approach_page)
        self.radioButton_channel_source_niboard_in_scan_page.toggled.connect(self.set_channel_signal_source_in_scan_page)
        self.radioButton_channel_source_niboard_in_laser_page.toggled.connect(self.set_channel_signal_source_in_laser_page)


        self.update_display_approach_signal.connect(self.update_display_approach)
        self.doubleSpinBox_encoder.valueChanged.connect(
            lambda: self.output_voltage_encoder.outputVoltage(self.doubleSpinBox_encoder.value()))

        self.checkBox_encoder_reading.stateChanged.connect(self.real_time_encoder)

        self.pushButton_z_goto.clicked.connect(
            lambda: self.goto_position_z(self.doubleSpinBox_z_goto.value()))
        self.pushButton_z_goto0.clicked.connect(
            lambda: self.goto_position_z(0.0))
        self.pushButton_z_stop_goto.clicked.connect(self.manual_z_goto_boolean_to_false)

        self.pushButton_approach_auto_start.clicked.connect(self.toggle_auto_approach_button)
        self.pushButton_laser_calibration_load.clicked.connect(self.load_calibration_form)
        self.pushButton_laser_calibration_directory.clicked.connect(self.select_directory_laser_calibration)

        for i in range(len(self.plane_fit_list[0])):
            plane_fit_x, plane_fit_y, plane_fit_z, plane_fit_checked = self.plane_fit_list[0][i],\
            self.plane_fit_list[1][i], self.plane_fit_list[2][i], self.plane_fit_list[3][i]
            plane_fit_x.valueChanged.connect(self.update_plane_fit)
            plane_fit_y.valueChanged.connect(self.update_plane_fit)
            plane_fit_z.valueChanged.connect(self.update_plane_fit)
            plane_fit_checked.toggled.connect(self.update_plane_fit)

        self.checkBox_read_power.stateChanged.connect(self.real_time_power)
        self.checkBox_laser_shutter.stateChanged.connect(lambda: self.laser_controller.openShutter() if self.checkBox_laser_shutter.isChecked() else self.laser_controller.closeShutter())
        self.pushButton_laser_controller.clicked.connect(self.reconnect_opa)
        self.pushButton_laser_set_wavelength.clicked.connect(
            lambda: self.opa_set_wavelength(self.doubleSpinBox_laser_set_wavelength.value()))
        self.pushButton_ndfilter_controller.clicked.connect(self.reconnect_ndfilter)
        self.pushButton_ndfilter.clicked.connect(
            lambda: self.ndfilter_set_angle(self.doubleSpinBox_ndfilter.value())
        )
        self.pushButton_power.clicked.connect(self.reconnect_power)
        self.pushButton_laser_calibration.clicked.connect(self.toggle_calibration)

        self.pushButton_laser_calibration_abort.clicked.connect(self.abort_calibration)

        self.pushButton_laser_calibration_save.clicked.connect(self.save_calibration_form_with_dialog)

        self.pushButton_laser_measurement_data_save_directory.clicked.connect(self.select_directory_laser_measurement)
        self.pushButton_laser_measurement.clicked.connect(self.toggle_laser_measurement)
        self.pushButton_laser_measurement_abort.clicked.connect(self.abort_laser_measurement)
