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
import math
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

    def getSessionInfo(self, item):
        if '' == item:
            return self.sessioninfo
        if item not in self.sessioninfo.keys():
            return None
        return self.sessioninfo[item]

    def loadTrack(self):
        trackName = self.sessioninfo["trackName"]
        if "VIR" in trackName.upper():
            if "full" in trackName.lower():
                from tracks import VIRfull as track
        elif "SEBRING" in trackName.upper():
            from tracks import Sebring as track
        if "track" not in dir():
            return
        self.sessioninfo["trackDescription"] = track.description
        self.trackStartFinish = track.startpoint
        self.waypoints = track.sectorEnds

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
            if utils.calculateGPSdistance(curPoint, self.trackStartFinish) < 30:
                # We are decreasing coming in. When we cross, we will start increasing.
                if utils.calculateGPSdistance(curPoint, self.trackStartFinish) > utils.calculateGPSdistance(prevPoint, self.trackStartFinish):
                    # We have crossed the boundary, but only add a new lap if the current lap has
                    # over 100 datapoints.
                    if len(self.laps[-1]) > 100:
                        self.addLap()
                        self.curLap += 1
                        self.curSegment = 1

            # Have we crossed a segment boundary?
            if 0 != self.curSegment:
                # Figure out if we need to increment the segment number
                if self.curSegment == len(self.waypoints):
                    nextWaypoint = self.trackStartFinish
                else:
                    nextWaypoint = self.waypoints[self.curSegment-1]
                # Are we within 25 feet of the next waypoint?
                if utils.calculateGPSdistance(curPoint, nextWaypoint) < 25:
                    # Distance is decreasing until we cross. When distance increases, we have crossed
                    if utils.calculateGPSdistance(curPoint, nextWaypoint) > utils.calculateGPSdistance(prevPoint, nextWaypoint):
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
        measurement = self.laps[-1][-2]
        point1 = (measurement["GPSlat"], measurement["GPSlng"])
        point2 = self.getLastLocation()
        return utils.calculateGPSdistance( (point1["GPSlat"], point1["GPSlng"]), (point2["GPSlat"], point2["GPSlng"]) )

    def dumpMetadata(self):
        pprint.pprint(self.sessioninfo)
        print ("Number of laps:", len(self.laps))

    def dumpLap(self, lapNumber):
        pprint.pprint(self.laps[lapNumber])

    def getLapTime(self, lapNumber):
        start = float(self.laps[lapNumber][0]["time"])
        end = float(self.laps[lapNumber][-1]["time"])
        elapsed = end - start
        return elapsed

    def getLapTimes(self):
        times = []
        for f in range(len(self.laps)):
            times.append(self.getLapTime(f))
        return times
    
    def getDataPoints(self):
        # TODO: Turn this into a comprehension. It feels like doing so would save some processing time.
        dataPoints = []
        for lap in self.laps:
            for measurement in lap:
                for point in measurement.keys():
                    if point not in dataPoints:
                        dataPoints.append(point)
        return dataPoints