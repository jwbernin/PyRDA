#!/usr/bin/python3

# This file describes the data model of a track session
# Each session is composed of 0 or 1 "out lap", and 0 or more "track laps"
# The final lap sensed will be designated the "out lap" for discussion purposes
# Each lap is a time-series of measurements.
# Each measurement is a "timechop" - number of second since the start of data recording - and an 
#  arbitrary number of keyword arguments. Possbilities include GPS position (longitude and latitude),
#  engine RPM, GPS heading, brake pressure, wheel speeds (FR, FL, RR, RL), and others. The specific
#  keyword argument datapoints will be determined by the data reading function. In here, we don't
#  (yet) care about what they actually are.

import pprint
import utils
class TrackSession:
    def __init__(self):
        self.laps = []
        self.sessioninfo = {}
        self.numLaps = 0
        self.trackStartFinish = ()
        self.waypoints = []
        self.curLap = 0
        self.curSegment = 0

    # Add session metadata
    def addSessionInfo(self, **kwargs):
        for k,v in kwargs.items():
            self.sessioninfo[k] = v

    def loadTrack(self):
        trackName = self.sessioninfo["trackName"]
        if "VIR" in trackName.upper():
            from tracks import VIRfull
            self.sessioninfo["trackDescription"] = VIRfull.description
            self.trackStartFinish = VIRfull.startpoint
            self.waypoints = VIRfull.sectorEnds
            print ("Waypoints:")
            pprint.pprint(self.waypoints)

    def addLap(self):
        newLap = []
        self.laps.append(newLap)
        self.numLaps += 1
        assert self.numLaps == len(self.laps)

    def addMeasurement(self, timeChop, **kwargs):
        if 0 == len(self.laps):
            self.addLap()
            
        measurement = {"time":timeChop}
        measurement["lap"] = self.curLap
        measurement["segment"] = self.curSegment
        for k,v in kwargs.items():
            measurement[k]=v


        # Have we crossed the start/finish boundary?
        prevPoint = self.getLastLocation()
        # If this is our first point, don't do any of these calculations.
        if None != prevPoint:
            curPoint = (measurement["GPSlat"], measurement["GPSlng"])
            # Are we within 30 feet of the start/finish point?
            if utils.calculateGPSdistace(curPoint, self.trackStartFinish) < 30:
                # We are decreasing coming in. When we cross, we will start increasing.
                if utils.calculateGPSdistace(curPoint, self.trackStartFinish) > utils.calculateGPSdistace(prevPoint, self.trackStartFinish):
                    # We have crossed the boundary, but only add a new lap if the current lap has
                    # over 100 datapoints.
                    if len(self.laps[-1]) > 100:
                        self.addLap()
                        self.curLap += 1
                        self.curSegment = 1

            # TODO: Have we crossed a segment boundary?
            if 0 != self.curSegment:
                # Figure out if we need to increment the segment number
                if self.curSegment == len(self.waypoints):
                    nextWaypoint = self.trackStartFinish
                else:
                    nextWaypoint = self.waypoints[self.curSegment-1]
                # Are we within 30 feet of the next waypoint?
                if utils.calculateGPSdistace(curPoint, nextWaypoint) < 25:
                    # Distance is decreasing until we cross. When distance increases, we have crossed
                    if utils.calculateGPSdistace(curPoint, nextWaypoint) > utils.calculateGPSdistace(prevPoint, nextWaypoint):
                        self.curSegment += 1

        measurement["segment"] = self.curSegment
        self.laps[-1].append(measurement)

    def getLastLocation(self):
        if 0 == len(self.laps):
            return None
        if 0 == len(self.laps[-1]):
            return None
        measurement = self.laps[-1][-1]
        return (measurement["GPSlat"], measurement["GPSlng"])

    def getLastDistanceTraversed(self):
        point1 = measurement(self.laps[-1][-2])
        point2 = self.getLastLocation()
        return utils.calculateGPSdistace( (point1["GPSlat"], point1["GPSlng"]), (point2["GPSlat"], point2["GPSlng"]) )

    def dumpMetadata(self):
        pprint.pprint(self.sessioninfo)
        print ("Number of laps:", len(self.laps))

    def dumpLap(self, lapNumber):
        pprint.pprint(self.laps[lapNumber])