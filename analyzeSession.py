#!/usr/bin/python3

# Main file for track session analysis.

from dataImporter import DataImporter
from datamodel import TrackSession
from importers import *
import sys
import pprint

def main():
    sessionFile = sys.argv[1]
    if sessionFile is None or sessionFile == '':
        sys.exit(1)

    inputObject = DataImporter().getFileImporter(sessionFile)
    session = inputObject.readSessionData()
    

if __name__ == '__main__':
    main()