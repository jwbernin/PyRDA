#!/usr/bin/python3

# Class for data importation
import os.path
import csv
from datamodel import TrackSession
import pprint

def getFileImporter(filename):
    if not os.path.isfile(filename):
        return False
    with open(filename, "r") as sourceFile:
        line = sourceFile.readline()
        sourceFile.close()
    if "AiM CSV File" in line:
        return AiMImporter(filename)
    elif "RaceRender Data: TrackAddict" in line: 
        return TrackAddictImporter()
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
            "throttle":"TPS"
        }

    def readSessionData(self):
        unparsedData = []

        with open(self.dataFile, "r") as fileHandle:
            reader = csv.reader(fileHandle)
            for row in reader:
                unparsedData.append(row)

        # Parse through the in-memory array for metadata
        self.session.addSessionInfo(trackName = unparsedData[1][1])
        self.session.addSessionInfo(sessionDate = unparsedData[6][1])

        self.session.loadTrack()

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
            self.session.addMeasurement(row[columnHeaders.index(self.dataLogPoints["time"])],
                GPSlat = row[columnHeaders.index(self.dataLogPoints["GPSlat"])],
                GPSlng = row[columnHeaders.index(self.dataLogPoints["GPSlng"])],
                throttle = row[columnHeaders.index(self.dataLogPoints["throttle"])]
            )
                
        return self.session

class TrackAddictImporter():
    def __init__(self):
        self.sesion = TrackSession()

    def readSessionData(self):
        unparsedData = []

        with open(self.dataFile, "r") as fileHandle:
            reader = csv.reader(fileHandle)
            for row in reader:
                unparsedData.append(row)

        # Parse through the in-memory array for metadata
        self.session.addSessionInfo(unparsedData[1])
        self.session.addSessionInfo(unparsedData[6])

        # remove the metadata from the in-memory array
        for i in range(13):
            del unparsedData[0]

        assert 0 == len(unparsedData[0])
        
        return self.session