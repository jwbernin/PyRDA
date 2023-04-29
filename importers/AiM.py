#!/usr/bin/python3

# This file imports from an AiM RaceStudio 3 generated CSV file
from datamodel import TrackSession
import csv

class AiMImporter(DataImporter):
    def __init__(self):
        super(AiMImporter, self).__init__()

    def readSessionData(self):
        session = TrackSession()

        unparsedData = []

        with open(self.dataFile), "r" as fileHandle:
            reader = csv.reader(fileHandle)
            for row in reader:
                unparsedData.append(row)

        // Parse through the in-memory array for metadata
        session.addSessionInfo(unparsedData[1])
        session.addSessionInfo(unparsedData[6])

        // remove the metadata from the in-memory array
        for i in range(13):
            del unparsedData[0]

        assert 0 == len(unparsedData[0])
        
        return session