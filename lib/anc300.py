"""
Created by Xiaoyu Wu / Yuan Ren pre-2018

One point worth mentioning:
for all "get..." commands, we should use read() twice as the complete cycle of response. 
For example, write(geto 1) -> read() -> read() will give us two returns after splitting: ['voltage', '=', '0.000000', 'V'] and ['OK]
That's why "while (tempstr.strip() != 'OK'):" is needed, or actually we could use two read() such as "tempstr = self.instrument.read(); status = self.instrument.read();",
where "tempstr" is the real out with valid information. status can be "OK" or "ERROR".
"""


from time import sleep
import pyvisa as visa

# Attention: AID range {1, 2, 3, 4}. Not starting from 0!

class ANC300():

    def __init__(self, COM_number):
        #COM_number = 3 for ST-500 system
        rm = visa.ResourceManager()
        tempstr = "ASRL" + str(COM_number)
        self.instrument = rm.open_resource(tempstr)
        self.instrument.write("echo off\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()


    def getser(self, AID):
        self.instrument.write("getser "+str(AID)+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr0 = tempstr
            tempstr = self.instrument.read()
        return tempstr0.strip()


    def measure_cap(self, AID):
        self.instrument.write("setm "+str(AID)+" cap\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()

        self.instrument.write("capw "+str(AID)+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()

        self.instrument.write("getc "+str(AID)+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr0 = tempstr
            tempstr = self.instrument.read()
        return tempstr0.strip()

    def setm(self, AID, AMODE):
        self.instrument.write("setm "+str(AID)+" "+AMODE+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()

    def setdci(self, AID, onoff):
        # onoff should be a string with two options "on" and "off"
        self.instrument.write("setdci "+str(AID)+" "+onoff+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()

    def setaci(self, AID, onoff):
        # onoff should be a string with two options "on" and "off"
        self.instrument.write("setaci "+str(AID)+" "+onoff+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()

    def setf(self, AID, FRQ):
        self.instrument.write("setf "+str(AID)+" "+str(FRQ)+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()

    def getf(self, AID):
        self.instrument.write("getf "+str(AID)+"\n")
        tempstr = self.instrument.read()
        return tempstr.split()[2]


    def setv(self, AID, VOL):
        self.instrument.write("setv "+str(AID)+" "+str(VOL)+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()


    def getv(self, AID):
        self.instrument.write("getv "+str(AID)+"\n")
        tempstr0 = self.instrument.read()
        status = self.instrument.read()
        return tempstr0.split()[2]

        self.instrument.write("getv "+str(AID)+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr0 = tempstr
            tempstr = self.instrument.read()
        return tempstr0.strip()

    def geto(self, AID):
        # onoff should be a string with two options "on" and "off"
        self.instrument.write("geto "+str(AID)+"\n")
        tempstr0 = self.instrument.read()
        status = self.instrument.read() 
        # sleep(0.1)
        return float(tempstr0.split()[2])



    def stepu(self, AID, C):
    # C = 'c' for continuous stepping; 1,2,3,... for fixed number of steps
    #     self.setm(AID, "stp")
        self.instrument.write("stepu "+str(AID)+" "+str(C)+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()


    def stepd(self, AID, C):
    # C = 'c' for continuous stepping; 1,2,3,... for fixed number of steps
    #     self.setm(AID, "stp")
        self.instrument.write("stepd "+str(AID)+" "+str(C)+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()

    def stop(self, AID):
        self.instrument.write("stop "+str(AID)+"\n")
        tempstr = self.instrument.read()
        while (tempstr.strip() != 'OK'):
            tempstr = self.instrument.read()