#!/usr/bin/python3

# Main file for track session analysis.

from dataImporter import *
from datamodel import TrackSession
import sys
import math
import argparse
import pprint

parser = argparse.ArgumentParser(description='Run analysis on track data file')
parser.add_argument('-f', '--file', action='append', help='Filename with data to be analyzed. Can be specified multiple times.')
parser.add_argument('-v', '--verbose', action='count')
parser.add_argument('-t', '--trackname', action='store', help='Name of track data is from, if not present in file (e.g. TrackAddict data). Can only analyze one track per run unless track name is present in datafile.')
args = parser.parse_args()

def analyze(session):
    session.dumpMetadata()

    for lap in session.getLapTimes():
        print(f"{math.trunc(lap/60):02}:{lap%60:0>6.3f}")

def main():
    runs = []
    for file in args.file:
        dataReader = getFileImporter(file)
        runs.append(dataReader.readSessionData())

    for run in runs:
        analyze(run)

if __name__ == '__main__':
    main()