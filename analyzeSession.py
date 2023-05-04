#!/usr/bin/python3

# Main file for track session analysis.

from dataImporter import *
from datamodel import TrackSession
import sys
import math
import pprint


def main():
    sessionFile = sys.argv[1]
    if sessionFile is None or sessionFile == '':
        sys.exit(1)

    inputObject = getFileImporter(sessionFile)
    session = inputObject.readSessionData()

    session.dumpMetadata()

    for lap in session.getLapTimes():
        print(f"{math.trunc(lap/60):02}:{lap%60:0>6.3f}")

if __name__ == '__main__':
    main()