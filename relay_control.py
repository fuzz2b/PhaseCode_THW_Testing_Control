"""
Controls the back end of the Denkovi USB 16 relay board. 

Uses a CSV file that translates the pin numbers on the FT head of the sensors 
to the connected relays (this should be kept consistent between sensors) and 
the selected wire from the main GUI to turn on selected relays.
"""
import os
import time

import numpy as np
import pandas as pd

import dae_RelayBoard  

dr = dae_RelayBoard.DAE_RelayBoard(dae_RelayBoard.DAE_RELAYBOARD_TYPE_16)
rootDir = os.path.dirname(__file__) 
df = pd.read_csv(rootDir + '/data/PinsToRelay.csv')


def pins_to_relays(pin1, pin2):
    pinNo = df['Pin No'].values
    vRelays = df['Voltage'].values
    sRelays = df['Sense'].values

    idx1 = np.where(pinNo == pin1)[0]
    idx2 = np.where(pinNo == pin2)[0]

    if len(idx1) == 0: 
        raise ValueError(f"Pin number {pin1} not found")
    if len(idx2) == 0:
        raise ValueError(f"Pin number {pin2} not found")

    idx1 = idx1[0]
    idx2 = idx2[0]

    return {int(vRelays[idx1]), int(sRelays[idx1]),
            int(vRelays[idx2]), int(sRelays[idx2])}


def set_relays(pinSelect1, pinSelect2):
    COMPORT = "COM3"  # virtual COM port - check device manager to set
    
    try:
        dr.initialise(COMPORT)
        dr.setAllStatesOff()
        
        active_relays = pins_to_relays(pinSelect1, pinSelect2)
        
        selectedRelays = {
            relay: (relay in active_relays) 
            for relay in range(1, dr.getNumRelays() + 1)
        }
        
        dr.setStates(selectedRelays)
        time.sleep(0.5)
             
    finally:
        dr.disconnect()
