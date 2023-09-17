#!/usr/bin/python3

# Class for data importation
import os.path
import csv
from datamodel import TrackSession
import pprint

def getFileImporter(filename):
    if not os.path.isfile(filename):
        print("Not a file!")
        return False
    with open(filename, "r") as sourceFile:
        line = sourceFile.readline()
        sourceFile.close()
    if "AiM CSV File" in line:
        return AiMImporter(filename)
    elif "RaceRender Data: TrackAddict" in line: 
        return TrackAddictImporter(filename)
    else:
        return False

class AiMImporter():
    def __init__(self, filename):
        self.session = TrackSession()
        self.dataFile = filename
        self.dataLogPoints = {
            "time":"Time",
            "GPSlat":"GPS Latitude",
            "GPSlng":"GPS Longitude",
            "throttle":"PPS",
            "brake":"BrakePress", 
            "heading":"GPS Heading",
            "steer":"SteerAngle",
            "lateralAccel":"LateralAcc",
            "inlineAccel":"InlineAcc"
        }

    def readSessionData(self, args):
        unparsedData = []

        with open(self.dataFile, "r") as fileHandle:
            reader = csv.reader(fileHandle)
            for row in reader:
                unparsedData.append(row)

        # Parse through the in-memory array for metadata
        self.session.addSessionInfo(trackName = unparsedData[1][1])
        self.session.addSessionInfo(sessionDate = unparsedData[6][1])
        self.session.addSessionInfo(sessionTime = unparsedData[7][1])
        self.session.addSessionInfo(vehicle = unparsedData[2][1])
        self.session.addSessionInfo(driverName = unparsedData[3][1])
        
        if args.trackname:
            self.session.addSessionInfo(trackName = args.trackname)
            
        self.session.loadTrack(args)

        # remove the metadata from the in-memory array
        for i in range(13):
            del unparsedData[0]

        assert 0 == len(unparsedData[0])
        del unparsedData[0]
        # first array entry right now is data headers
        columnHeaders = unparsedData[0]
        units = unparsedData[1]
        # delete the headers and blank line, trim to only the actual session data
        del unparsedData[0]
        del unparsedData[0]
        del unparsedData[0]

        # Process all datapoints
        for row in unparsedData:
            if args.gps_only:
                self.session.addMeasurement(row[columnHeaders.index(self.dataLogPoints["time"])],
                    GPSlat = float(row[columnHeaders.index(self.dataLogPoints["GPSlat"])]),
                    GPSlng = float(row[columnHeaders.index(self.dataLogPoints["GPSlng"])]),
                    heading = float(row[columnHeaders.index(self.dataLogPoints["heading"])]),
                    lateralAccel = float(row[columnHeaders.index(self.dataLogPoints["lateralAccel"])]),
                    inlineAccel = float(row[columnHeaders.index(self.dataLogPoints["inlineAccel"])])
                )
            else:
                self.session.addMeasurement(row[columnHeaders.index(self.dataLogPoints["time"])],
                    GPSlat = float(row[columnHeaders.index(self.dataLogPoints["GPSlat"])]),
                    GPSlng = float(row[columnHeaders.index(self.dataLogPoints["GPSlng"])]),
                    throttle = float(row[columnHeaders.index(self.dataLogPoints["throttle"])]),
                    brake = float(row[columnHeaders.index(self.dataLogPoints["brake"])]),
                    heading = float(row[columnHeaders.index(self.dataLogPoints["heading"])]),
                    steer = float(row[columnHeaders.index(self.dataLogPoints["steer"])]),
                    lateralAccel = float(row[columnHeaders.index(self.dataLogPoints["lateralAccel"])]),
                    inlineAccel = float(row[columnHeaders.index(self.dataLogPoints["inlineAccel"])])
                )
                
        return self.session

class TrackAddictImporter():
    def __init__(self, filename):
        self.session = TrackSession()
        self.dataFile = filename
        self.dataLogPoints = {
            "time":"Time",
            "GPSlat":"Latitude",
            "GPSlng":"Longitude",
            "throttle":"Accelerator Pedal (%) *OBD",
            "brake":"Brake (calculated)",
            "heading":"Heading",
            "lateralAccel":"Accel X",
            "inlineAccel":"Accel Y"
        }

    def readSessionData(self):
        unparsedData = []

        with open(self.dataFile, "r") as fileHandle:
            reader = csv.reader(fileHandle)
            for row in reader:
                unparsedData.append(row)

        # Parse through the in-memory array for metadata
        # TODO: Get track name from cmd line options
        #    For now, default to VIR Full
        self.session.addSessionInfo(trackName = "VIR Full")
        self.session.loadTrack()

        # remove the metadata from the in-memory array
        for i in range(16):
            del unparsedData[0]

        # first array entry right now is data headers
        columnHeaders = unparsedData[0]
        del unparsedData[0]
        # Process all datapoints
        for row in unparsedData:
            if row[0].startswith('#'):
                continue
            self.session.addMeasurement(row[columnHeaders.index(self.dataLogPoints["time"])],
                GPSlat = float(row[columnHeaders.index(self.dataLogPoints["GPSlat"])]),
                GPSlng = float(row[columnHeaders.index(self.dataLogPoints["GPSlng"])]),
                throttle = float(row[columnHeaders.index(self.dataLogPoints["throttle"])]),
                brake = float(row[columnHeaders.index(self.dataLogPoints["brake"])]),
                heading = float(row[columnHeaders.index(self.dataLogPoints["heading"])]),
                lateralAccel = float(row[columnHeaders.index(self.dataLogPoints["lateralAccel"])]),
                inlineAccel = float(row[columnHeaders.index(self.dataLogPoints["inlineAccel"])])
            )

        return self.session
