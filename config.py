"""
config.py containes what appears in the power supply and joulescope dropdowns. 
Read by main_gui.py on startup.

DROPDOWN_GROUPS is a list of dicts, one per dropdown. 
"""

from pathlib import Path

BASE = Path(__file__).parent

DROPDOWN_GROUPS = [
    {
        "label": "Power Supply Configurations",               
        "tools": [
            {
                "name":  "Set Power",
                "path":  str("tools/power_supply_tools/set_power.py"),
            },
            # {
            #     "name":  "Transient Hot Wire",
            #     "path":  str("tools/power_supply_tools/thw_power.py"),
            # },
        ],
    },
    {
        "label": "Joulescope Tests",              
        "tools": [
            {
                "name":  "Quick Measure",
                "path":  str("tools/joulescope_tools/quick_measure.py"),
            },
            {
                "name":  "Long Measure",
                "path":  str("tools/joulescope_tools/long_measure.py"),
            },
        ],
    },
]