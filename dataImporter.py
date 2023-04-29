#!/usr/bin/python3

# Class for data importation

from importers import *

class DataImporter:
    def __init__(self):
        self.dataFile = ''

    def readSessionData(self):
        pass

    def getFileImporter(self, filename):
        if not is_file(filename):
            return False
        with open(filename, "r") as sourceFile:
            line = sourceFile.readline()
            sourceFile.close()
        if "AiM CSV File" in line:
            self.dataFile = filename
            return AiMImporter(self)
        else if "RaceRender Data: TrackAddict" in line: 
            self.dataFile = filename
            return TrackAddictImporter(self)
        else:
            return False