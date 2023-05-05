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
gengroup = parser.add_argument_group("General analysis options")
gengroup.add_argument('--laps', action=argparse.BooleanOptionalAction, help='Show / don\'t show lap data (default: TRUE)', default=True)
gengroup.add_argument('--segments', action=argparse.BooleanOptionalAction, help='Show / don\'t show segment data (default: FALSE)')
gengroup.add_argument('--list-datapoints', action='store_true', help='List the data points available in the file(s) and exit')
segparser = parser.add_argument_group('Segment analysis options')
segparser.add_argument('--delta', action=argparse.BooleanOptionalAction, help='Show segment time deltas from best segment time')

args = parser.parse_args()

def analyze(session):
    # Tell us which session we're looking at
    print(f'Analyzing data from { session.getSessionInfo("sourcefile") }')
    if session.getSessionInfo('trackName') is not None:
        print(f'Track name: { session.getSessionInfo("trackName") }') 
    if session.getSessionInfo('trackDescription') is not None:
        print(f'Track description: { session.getSessionInfo("trackDescription") }') 

    if args.list_datapoints:
        print('These datapoints are available:')
        for point in session.getDataPoints():
            print (f"- {point}")
        return

    if args.laps:    
        print("Lap times:")
        for count,lap in enumerate(session.getLapTimes()):
            print(f"Lap { count }: {math.trunc(lap/60):02}:{lap%60:0>6.3f}")

def main():
    runs = []
    for file in args.file:
        dataReader = getFileImporter(file)
        runs.append(dataReader.readSessionData())
        runs[-1].addSessionInfo(sourcefile = file)

    for run in runs:
        analyze(run)

if __name__ == '__main__':
    main()