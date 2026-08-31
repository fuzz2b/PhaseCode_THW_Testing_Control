"""
thw_power.py

Pre-bias version of set_power.py.

Instead of stepping the supply straight from 0 A -> test current (which
produced the underdamped dip/spike/overshoot transient you captured),
this holds the supply ON at a small pre-bias current first, lets it
settle, then steps to the test current. The step happens while the
Joulescope (long_measure_thw.py) is already actively capturing, so the
step itself -- including any residual transient -- ends up IN the data,
where it can be seen and its timing detected, instead of happening
before/blind to the capture.

Pairs with tools/joulescope_tools/long_measure_thw.py.
"""

import pyvisa
import time
import subprocess
import os
import sys

rm = pyvisa.ResourceManager()
VISA_ADDRESS = "USB0::0x05E6::0x2280::4099235::INSTR"  # Got to check for VISA address

ROOT_DIR = os.path.dirname(__file__) + '/../'
JS_TOOL_PATH = os.path.join(ROOT_DIR + "joulescope_tools/long_measure_prebias.py")

# Settings
VOLTAGE = 10          # [Volts]
PREBIAS_CURRENT = 0.01  # [Amps] "hold" current the supply sits at before the step
TEST_CURRENT = 0.4      # [Amps] -- the actual test current

PREBIAS_SETTLE_S = 0.5  # time to let the supply settle at the pre-bias current
                         # before arming the Joulescope

extra_args = [
    "--contiguous", "2",
    "--plot",
    "--out-prefix", "",
]

def set():
    js_proc = None
    try:
        keithley = rm.open_resource(VISA_ADDRESS)

        keithley.write("*RST")
        time.sleep(1)

        print("Configuring safety limits...")
        keithley.write(f":CURR:PROT:LEV {TEST_CURRENT * 1.2}")

        keithley.write(f":CURR:RANG {TEST_CURRENT}")

        print(f"Setting output to {VOLTAGE}V, pre-biasing at {PREBIAS_CURRENT}A...")
        keithley.write(f":VOLT {VOLTAGE}")
        keithley.write(f":CURR {PREBIAS_CURRENT}")

        keithley.write(":OUTP ON")
        prebias_on_time = time.time()
        print(f"OUTP ON at pre-bias ({PREBIAS_CURRENT} A) at {prebias_on_time}")

        # 
        time.sleep(PREBIAS_SETTLE_S)

        current_env = os.environ.copy()
        js_proc = subprocess.Popen(
            ["python", JS_TOOL_PATH] + extra_args,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=current_env
        )

        print("Waiting for Joulescope to start capturing...")
        #removed handshake
        arm_delay_s = 1.0
        time.sleep(arm_delay_s)

        step_time = time.time()
        keithley.write(f":CURR {TEST_CURRENT}")
        print(f"Stepped to test current ({TEST_CURRENT} A) at {step_time}")

        time.sleep(0.5)
        measured = keithley.query(":MEAS:CURR?")
        print(f"Keithley's own measured current after step: {measured.strip()}")

        for line in js_proc.stdout:
            print(line, end="")
        js_proc.wait()

    finally:
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