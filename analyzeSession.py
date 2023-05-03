#!/usr/bin/python3

# Main file for track session analysis.

from dataImporter import *
from datamodel import TrackSession
import sys
import pprint


def main():
    sessionFile = sys.argv[1]
    if sessionFile is None or sessionFile == '':
        sys.exit(1)

    inputObject = getFileImporter(sessionFile)
    session = inputObject.readSessionData()

    session.dumpMetadata()

if __name__ == '__main__':
    main()