import json
import sys
import os
import time

import traceback

import statistics #Used for mean
from math import hypot #Used for pythagorean theorem

# Globally define the Out Lists so they can be accessed within scheduled functions
tofOut = []
accOut = []
micOut = []
humOut = []
tmpOut = []
wtrOut = []

# Create serial port object for interfacing with Arduino
import serial
ser = serial.Serial('/dev/ttyS0', baudrate=38400, parity=serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE)

sys.path.insert(0, os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')))

import notecard  # noqa: E402

productUID = "com.gmail.ejlewis02:test1"

if sys.implementation.name != 'cpython':
    raise Exception("Please run this example in a CPython environment.")

from periphery import I2C  # noqa: E402


def NotecardExceptionInfo(exception):
    """Construct a formatted Exception string.

    Args:
        exception (Exception): An exception object.

    Returns:
        string: a summary of the exception with line number and details.
    """
    s1 = '{}'.format(sys.exc_info()[-1].tb_lineno)
    s2 = exception.__class__.__name__
    return "line " + s1 + ": " + s2 + ": " + ' '.join(map(str, exception.args))


def configure_notecard(card):
    """Submit a simple JSON-based request to the Notecard.

    Args:
        card (object): An instance of the Notecard class

    """
    req = {"req": "hub.set"}
    req["product"] = productUID
    req["mode"] = "periodic"
    req["outbound"] = 1 # Sync every minute

    try:
        card.Transaction(req)
    except Exception as exception:
        print("Transaction error: " + NotecardExceptionInfo(exception))
        time.sleep(5)


def get_temp_and_voltage(card):
    """Submit a simple JSON-based request to the Notecard.

    Args:
        card (object): An instance of the Notecard class

    """
    temp = 0
    voltage = 0

    try:
        req = {"req": "card.temp"}
        rsp = card.Transaction(req)
        temp = rsp["value"]

        req = {"req": "card.voltage"}
        rsp = card.Transaction(req)
        voltage = rsp["value"]
    except Exception as exception:
        print("Transaction error: " + NotecardExceptionInfo(exception))
        time.sleep(5)

    return temp, voltage

def read_serial(port):
    rcv = port.readline()
    #Remove bad characters from string
    rcv = rcv[0:-2]
#     print(rcv)
    return(rcv)

def parse_json(input):
    data = json.loads(input)
    return(data)
    
def isJSON(input):
    try:
        json.loads(input)
    except:
        return False
    return True

#This "work" function does everything we need to do for a list during the loop
def work(listIn : list, iterIn : int, meanIn : float, data, listOut : list):
    #Add latest value to list
    if len(listIn) < 250:
        #Insert sensor values to list for first 250 values
        listIn.append(data)
    else:
        #Overwrite existing value at this location
        listIn[iterIn] = data
        #Determine if the newest value exists outside of the mean
        if ((abs((meanIn - data)) >= (meanIn * 0.05)) and (data != None) ):
            #Send data to Notecard as it is unusual
            listOut.append(data)
        #Compute average value from list (used on next loop)
        meanIn = statistics.fmean(listIn)
    #Increment iterator by one
    iterIn += 1
    #Check if list is "full"
    if (iterIn >= 250):
        #List is "full" so reset iterator to 0 position
        iterIn = 0
    #Lists are mutable, so they do not need to be returned after being modified in the function.
    #Integers and floats are immutable, so they must be returned after being modified in the function
    return iterIn, meanIn

def scheduledEvent(card):
    print("Running scheduledEvent")
    # Declare Out Lists as global so we can edit them in here
    # Lists:
    global tofOut
    global accOut
    global micOut
    global humOut
    global tmpOut
    global wtrOut

    # Create request
    req = {"req": "note.add"}
    req["sync"] = True
    
    # Append a null value to each list in case they are empty
    tofOut.append(None)
    accOut.append(None)
    micOut.append(None)
    humOut.append(None)
    tmpOut.append(None)
    wtrOut.append(None)

    # Determine if water level is True
    if (wtrOut[0] == True):
        wtrValue = True
    else:
        wtrValue = False
    # Create the JSON locations for each sensor in the request
    req["body"] = {"tof": tofOut[0], "acc": accOut[0], "mic": micOut[0], "hum": humOut[0], "tmp": tmpOut[0], "wtr" : wtrValue}

    # Clear out the lists after grabbing an element from them.
    tofOut.clear()
    accOut.clear()
    micOut.clear()
    humOut.clear()
    tmpOut.clear()
    wtrOut.clear()

    # Complete transaction
    try:
        card.Transaction(req)
    except Exception as exception:
        print("Transaction error: " + NotecardExceptionInfo(exception))
        time.sleep(5)
    
    
    
    
    

def main():
    """Connect to Notcard and run a transaction test."""
    print("Opening port...")
    try:
        port = I2C("/dev/i2c-1")
    except Exception as exception:
        raise Exception("error opening port: "
                        + NotecardExceptionInfo(exception))

    print("Opening Notecard...")
    try:
        card = notecard.OpenI2C(port, 0, 0, debug=True)
    except Exception as exception:
        raise Exception("error opening notecard: "
                        + NotecardExceptionInfo(exception))

    # If success, configure the Notecard and send some data
    configure_notecard(card)

    # Count up to a certain number. When reached, run the scheduledEvent.
    scheduledCount = 0
    
    ##########################################################################
    #JSON Parsing and Object Generating
    
    #Initialize each of the sensors' lists to be used for data processing during the loop.
    #Time-of-Flight
    tofList = []
    tofIter = 0
    tofMean = 0
    #Acceleration
    accList = []
    accIter = 0
    accMean = 0
    #Microphone
    micList = []
    micIter = 0
    micMean = 0
    #Humidity
    humList = []
    humIter = 0
    humMean = 0
    #Temperature
    tmpList = []
    tmpIter = 0
    tmpMean = 0
    #Water doesn't have lists or math because it's a binary value

    

    # loopRunning = True
    
    while True:
        jsonData = read_serial(ser)
        if (isJSON(jsonData)):
            data = parse_json(jsonData.decode("utf-8"))
        else:
            #Error Handling
            print("Error occurred, restarting loop")
            continue
        
        #Now that we have an array of objects from our JSON input, we can store and process the items before sending them to the Notecard.
        #Array Items: "tof", "acc", "mic", "hum", "tmp"
        #Initialize each of the sensors' lists to be used for data processing during the loop.
        
        #Now that we have an array of objects from our JSON input, we can store and process the items before sending them to the Notecard.
        #Sensors: "tof", "acc", "mic", "hum", "tmp"

        #Run work on newest value from Time-of-Flight
        tofIter, tofMean = work(tofList, tofIter, tofMean, data["tof"]["data"][0], tofOut)

        #Compute Euclidean Distance for newest values from Acceleration
        accMag = hypot(data["acc"]["data"][0], data["acc"]["data"][1], data["acc"]["data"][2])
        #Run work on newest magnitude from Acceleration
        accIter, accMean = work(accList, accIter, accMean, accMag, accOut)

        #Run work on newest values from Microphones
        micIter, micMean = work(micList, micIter, micMean, data["mic"]["data"][0], micOut)
        micIter, micMean = work(micList, micIter, micMean, data["mic"]["data"][1], micOut)
        micIter, micMean = work(micList, micIter, micMean, data["mic"]["data"][2], micOut)
        
        #Run work on newest value from Humidity
        humIter, humMean = work(humList, humIter, humMean, data["hum"]["data"][0], humOut)

        #Run work on newest value from Temperature
        tmpIter, tmpMean = work(tmpList, tmpIter, tmpMean, data["tmp"]["data"][0], tmpOut)
        
        #Obtain water level detections
        if ((data["wtr"]["data"][0] == True) or (data["wtr"]["data"][1] == True) or (data["wtr"]["data"][2] == True)):
            #Add the water level detection to the outList
            wtrOut.append(True)

        #Print list size
        print("List size: " + str(len(tofList)))
        
        #Debug tof
#         print("tof: " + str(tofList))

        #If scheduledCount is greater than or equal to 50, run the scheduledEvent
        if (scheduledCount >= 50):
            scheduledCount = 0
            scheduledEvent(card)
            #Don't increment scheduledCount, end this loop iteration here.
            continue

        #Increment scheduledCount by 1
        scheduledCount += 1
    


main()


