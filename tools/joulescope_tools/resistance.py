
import os
import sys
import csv
import time

import pandas as pd
import numpy as np
import statistics as stat
from collections import deque


from datetime import datetime
from joulescope import scan_require_one

import pyvisa #I imorted pyvisa-py which is ...

CSV_PATH = 'resistance_log.csv'
N_measure = 5 #

rm = pyvisa.ResourceManager()
VISA_ADDRESS = "USB0::0x05E6::0x2280::4099235::INSTR" # Got to Check for VISA ADDRESS

keithley = rm.open_resource(VISA_ADDRESS)

rootDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/"

def create_csv(path):
    if not os.path.exists(path):
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'measurement_index', 'current_A', 'voltage_V', 'resistance_ohm'])

def append_row(path, index, current, voltage, resistance):
    with open(path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().isoformat(), index, current, voltage, resistance])

def run():

    try:
        device = scan_require_one(config='auto')
        voltage = 10  # Volts
        current = 0.4  # Amps
        create_csv(CSV_PATH)

        with device:
            for i in range(1, N_measure + 1):
                
                keithley.write(f":VOLT 10")
                keithley.write(f":CURR 0.4")
                keithley.write(":OUTP ON")
                time.sleep(1)

                data = device.read(contiguous_duration=0.001)
                current, voltage = data[-1, :]
                resistance = voltage/current

                append_row(CSV_PATH, i, current, voltage, resistance)
                print(f'[{i}/{N_measure}] {current} A, {voltage} V, {resistance} Ω')

                keithley.write(f":VOLT 0")
                keithley.write(f":CURR 0")
                time.sleep(10)

        
        df = pd.read_csv(rootDir + CSV_PATH)

        t = df['resistance_ohm'].tail(N_measure).tolist()


        mean = stat.mean(t)
        std = stat.pstdev(t)

        print(f"The resistance is {mean} ± {std}")

    finally:
        keithley.write(":OUTP OFF")
        keithley.close()
    
if __name__ == '__main__':
    sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None
    run()