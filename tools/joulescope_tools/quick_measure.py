"""
quick_measure.py

Does a quick VI measurement using Joulescope including handshake to sync with 
power supply.
"""
import os
import sys
import time
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt

from joulescope import scan_require_one

def run():
    device = scan_require_one(config='auto')
    
    with device:
        time.sleep(0.09) # steady time
        print("READY", flush=True) # Handshake for power supply

        data = device.read(contiguous_duration=0.001)
        
    current, voltage = data[-1, :]
    print(f'{current} A, {voltage} V')
    return 0

if __name__ == '__main__':
 
    sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None
    run()