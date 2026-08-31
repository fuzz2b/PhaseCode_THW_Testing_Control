import pyvisa #I imorted pyvisa-py which is ...
import time

import subprocess

import os
import sys
# ==============================================================================
# Connecting to the Supply

# To find the VISA address
# import pyvisa
# rm = pyvisa.ResourceManager()
# print(rm.list_resources())


# I got AI to implment the handshake situation thus that now confuses me
# ==============================================================================
rm = pyvisa.ResourceManager()
VISA_ADDRESS = "USB0::0x05E6::0x2280::4099235::INSTR" # Got to Check for VISA ADDRESS


ROOT_DIR = os.path.dirname(__file__) + '/../'
JS_TOOL_PATH = os.path.join(ROOT_DIR + "joulescope_tools/long_measure.py") # I need to pass the argument of the tool path chosen into here but I dont want to do that rn

extra_args = ["--contiguous", "60", '--plot']
def set():
    js_proc = None
    try:
        
        # Setting Values
        voltage = 10  # Volts
        current = 0.4  # Amps

        keithley = rm.open_resource(VISA_ADDRESS)

        # idn = keithley.query("*IDN?")
        # print(f"Connected to: {idn}")

        keithley.write("*RST")
        time.sleep(1)  

        # Protection & Limits 
        print("Configuring safety limits...")
        keithley.write(f":VOLT:PROT:LEV {voltage}*1.2")  #
        keithley.write(f":CURR:PROT:LEV {current}*1.2")  


        print(f"Setting output to {voltage}V with a {current}A limit...")
    
        keithley.write(f":VOLT {voltage}")

        keithley.write(f":CURR {current}")

        current_env = os.environ.copy()

        js_proc = subprocess.Popen( 
            ["python", JS_TOOL_PATH] + extra_args,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
            env=current_env
        )

        print("Waiting for Joulescope to arm...")
        for line in js_proc.stdout:
            print(f"[js_tool @ {time.time()}]:", line, end="")
            if "READY" in line:
                #time.sleep(1)
                break

        print(f"OUTP ON at {time.time()}")
        keithley.write(":OUTP ON")  
        
        for line in js_proc.stdout:
            print(line, end="")
        js_proc.wait()  # until capture finishes

    finally:
    # Clean up 
        if "keithley" in locals():
            print("\nTurning output OFF and closing connection...")
            keithley.write(":OUTP OFF")
            keithley.close()
        rm.close()

        if js_proc is not None and js_proc.poll() is None:
            js_proc.terminate()

        print("Disconnected.")

if __name__ == '__main__':
    set()