"""
Created by Xuejian Ma at 10/22/2021.
All rights reserved.
"""
import pyvisa as visa

class SR830():
    def __init__(self, COM_number):
        # COM_number = 9 for SR830 Top, 8 for SR830 Bottom
        rm = visa.ResourceManager()
        tempstr = "GPIB0::" + str(COM_number)
        self.instrument = rm.open_resource(tempstr)



    def set_time_constant(self, index):
        self.instrument.write("OFLT " + str(index))


    def set_display(self, channel, index):
        # the last digit is ratio: 0 none, 1 Aux In 1, 2 Aus In 2
        self.instrument.write("DDEF " + str(channel) + "," + str(index) + ",0")


    def set_output(self, channel, index):
        self.instrument.write("FPOP " + str(channel) + "," + str(index))


    def set_reference_source(self, index):
        self.instrument.write("FMOD " + str(index))


    def set_frequency(self, freq):
        self.instrument.write("FREQ " + str(freq))
