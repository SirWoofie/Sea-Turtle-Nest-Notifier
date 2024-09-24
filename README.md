# Pi_4B_Notecard
The Raspberry Pi-based software component of a system to monitor sea turtle nests and notify interested parties
# Hardware
* Raspberry Pi 4B 2GB
* Sparkfun Qwiic Cellular Notecarrier - Blues Wireless
# What it does
Upon waking up, the Raspberry Pi will launch a system service that runs and manages a Python script. This script will listen for data over serial from an Arduino and collate that data into a series of arrays for later processing.

The Rasperry Pi can compute the mean of each array and determine if any new data points are within a certain percentage of the mean. If not, those data points will be sent to the cloud for further analysis and later notification of interested parties.
