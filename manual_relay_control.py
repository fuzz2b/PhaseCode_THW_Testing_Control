#===============================================================================
# Initialzing and that sort of thing
#===============================================================================

import time
import dae_RelayBoard   

import os
import pandas as pd
import numpy as np

dr = dae_RelayBoard.DAE_RelayBoard(dae_RelayBoard.DAE_RELAYBOARD_TYPE_16)

pinSelect1 = 1 # REPLACED BY GUI
pinSelect2 = 2 # REPLACED BY GUI

#import power_supply
#===============================================================================
# Toggling between different wires and turning the appropraite wires on and off                                                                                                                                                                                                                                                                                                                                                                                                             
#===============================================================================

dr = dae_RelayBoard.DAE_RelayBoard(dae_RelayBoard.DAE_RELAYBOARD_TYPE_16)
rootDir = os.path.dirname(__file__) 
df = pd.read_csv(rootDir + '/data/PinsToRelay.csv')

try:
    def pins_to_relays(pin1, pin2):
        """
        Given two selected pin numbers, returns a set of 4 integers corresponding to
        the voltage and sense relays associated with the pins.
        """
        pinNo = df['Pin No'].values
        vRelays = df['Voltage'].values
        sRelays = df['Sense'].values

        # Find the index of each pin number in the pinNo array
        idx1 = np.where(pinNo == pin1)[0]
        idx2 = np.where(pinNo == pin2)[0]

        if len(idx1) == 0: # in case pin dont exist
            raise ValueError(f"Pin number {pin1} not found")
        if len(idx2) == 0:
            raise ValueError(f"Pin number {pin2} not found")

        idx1 = idx1[0]
        idx2 = idx2[0]

        return {int(vRelays[idx1]), int(sRelays[idx1]),
                int(vRelays[idx2]), int(sRelays[idx2])}


    COMPORT = "COM3" #virtual COM port - check device manager to set
    dr.initialise(COMPORT)


    dr.setAllStatesOff()

    selectedRelays = {}
    selectedRelays = {relay: (relay in pins_to_relays(pinSelect1,pinSelect2)) for relay in range(1, dr.getNumRelays() + 1)} ## Get Amirs help with this - maybe long

    dr.setStates(selectedRelays)
    time.sleep(0.5)
    print (dr.getStates())

finally:
    # dr.setAllStatesOff() 
    dr.disconnect()
