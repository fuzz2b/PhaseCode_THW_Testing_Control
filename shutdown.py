"""
Connects to the Keithley power supplys, Joulescope and Relay board to turn everything off.

This script should be improved to execute each step regardless of if one fails.

"""

import pyvisa

import dae_RelayBoard  
from joulescope import scan_require_one

def run():
    rm = pyvisa.ResourceManager()
    VISA_ADDRESS = "USB0::0x05E6::0x2280::4099235::INSTR" # Got to Check for VISA ADDRESS

    k = rm.open_resource(VISA_ADDRESS)
    k.write(":OUTP OFF")
    k.close()
    print("KEITHLEY OFF DISCONNECTED")

    device = scan_require_one(config='auto')
    device.stop()
    print("JOULESCOPE DISCONNECTED")
    
    dr = dae_RelayBoard.DAE_RelayBoard(dae_RelayBoard.DAE_RELAYBOARD_TYPE_16)
    COMPORT = "COM3" #virtual COM port - check device manager to set
    
    dr.initialise(COMPORT)
    dr.setAllStatesOff() 
    dr.disconnect()
    print("RELAYS OFF AND DISCONNECTED")    
    
if __name__ == '__main__':
    run()    