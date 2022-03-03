"""
Created by Xuejian Ma at 10/22/2021.
All rights reserved.
"""
import pyvisa as visa
import json

name_dict = {
    'up': "GPIB0::9",
    'down': "GPIB0::8"
}
try:
    with open('../config.json') as f:
        data = json.load(f)
    name_dict['up'] = data['lockin_top_name']
    name_dict['down'] = data['lockin_bottom_name']
    print("lockin top and bottom names changed to up: {} and down: {}".format(name_dict['up'], name_dict['down']))
except:
    print("No lockin substitute names found in ../config.json")
class SR8x0():
    def __init__(self, up_or_down):
        # COM_number = name_dict[up_or_down]
        # # COM_number = 9 for SR830 Top, 8 for SR830 Bottom
        # COM_number = 1 for SR830 Bottom
        rm = visa.ResourceManager()
        # tempstr = "GPIB0::" + str(COM_number)

        # tempstr = "ASRL" + str(COM_number) + "::INSTR"
        print(rm.list_resources())
        # for string in rm.list_resources():
        #     if tempstr in string:
        #         tempstr = string
        #         break
        tempstr = name_dict[up_or_down]
        self.instrument = rm.open_resource(tempstr)
        print(tempstr, self.instrument)
        self.model = 'SR830' if 'SR830' in self.get_identification() else 'SR860'
        print(self.model)



    def set_time_constant(self, index):
        if self.model == 'SR830':
            self.instrument.write("OFLT " + str(max(index, 0)))
        else: # SR860
            self.instrument.write("OFLT " + str(index + 2))


    def set_display(self, channel, index):
        # the last digit is ratio: 0 none, 1 Aux In 1, 2 Aus In 2
        if self.model == 'SR830':
            self.instrument.write("DDEF " + str(channel) + "," + str(index) + ",0")
        else:
            self.instrument.write("COUT " + str(channel - 1) + "," + str(index))


    def set_output(self, channel, index):
        self.instrument.write("FPOP " + str(channel) + "," + str(index))



    def set_reference_source(self, index):
        if self.model == 'SR830':
            self.instrument.write("FMOD " + str(index))
        else:
            self.instrument.write("RSRC " + str(1 - index))


    def set_frequency(self, freq):
        self.instrument.write("FREQ " + str(freq))

    def get_identification(self):
        return self.instrument.query("*IDN?")