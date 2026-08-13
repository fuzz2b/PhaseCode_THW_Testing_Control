Hi

This contains all the code I use to control the Keithley power supply, relay module and joulescope.

The tools I use for interacting with the joulescope are mostly located in the tools -> joulescope_tools. These are mostly just upgraded scripts from a developer at JS (there tools had deprecated slightly). The long and quick measure contain a handshake to interact with the power supply, but they should be able to be run independently. These use a plotting tool developed by JS (which is located in Joulescope import) as well as producing a huge .csv file. the long measure is limited to 120 seconds.

If you are interested in plotting, I have something separate for that which works with feather files.
