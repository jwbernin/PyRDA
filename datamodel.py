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
        self.curLap = 1
        self.curSegment = 1

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

    def loadTrack(self, args):
        trackName = self.sessioninfo["trackName"]
        if args.verbose:
            print ("Searching for track: "+self.sessioninfo["trackName"]+".")
        if "VIR" in trackName.upper():
            if "full" in trackName.lower():
                from tracks import VIRfull as track
        elif "SEBRING" in trackName.upper():
            from tracks import Sebring as track
        if "track" not in dir():
            if args.verbose:
                print("No track found!")
            return
        
        self.sessioninfo["trackDescription"] = track.description
        self.trackStartFinish = track.startpoint
        self.waypoints = track.sectorEnds
        self.enterTrackPoint = track.enterTrackPoint
        self.exitTrackPoint = track.exitTrackPoint

    def addLap(self):
        newLap = []
        self.laps.append(newLap)
        self.numLaps += 1
        assert self.numLaps == len(self.laps)

    # TODO: This is buggy. Refactor.
    def addMeasurement(self, timeChop, **kwargs):
        if 0 == len(self.laps):
            self.addLap()
            
        measurement = {"time":float(timeChop)}
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
                if self.curSegment == len(self.waypoints)+1:
                    nextWaypoint = self.trackStartFinish
                else:
                    nextWaypoint = self.waypoints[self.curSegment-1]
                # Are we within 25 feet of the next waypoint?
                if utils.calculateGPSdistance(curPoint, nextWaypoint) < 25:
                    # Distance is decreasing until we cross. When distance increases, we have crossed
                    if utils.calculateGPSdistance(curPoint, nextWaypoint) > utils.calculateGPSdistance(prevPoint, nextWaypoint):
                        self.curSegment += 1

        measurement["lap"] = self.curLap
        measurement["segment"] = self.curSegment
        self.laps[-1].append(measurement)

    def trimEnds(self):
        # Trims the start of the out lap and the end of the last lap so that we don't have GPS tracks 
        # following us into and through the paddock.
        inLapPoints = len(self.laps[0])
        outLapPoints = len(self.laps[-1])
        # Starting at datapoint 0, if we are not within 10 feet of enterTrackPoint, we don't care about this datapoint
        while (15 < utils.calculateGPSdistance(self.enterTrackPoint, (self.laps[0][0]["GPSlat"], self.laps[0][0]["GPSlng"]))):
            del self.laps[0][0]

        # starting with the last datapoint and working backwards, if we're not within 10 feet of exitTrackPoint, we
        # get rid of the point
        while (15 < utils.calculateGPSdistance(self.exitTrackPoint, (self.laps[-1][-1]["GPSlat"], self.laps[-1][-1]["GPSlng"]))):
            del self.laps[-1][-1]

        assert len(self.laps[0]) < inLapPoints
        assert len(self.laps[-1]) < outLapPoints

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

    def getHotLapTimes(self):
        times = []
        for f in range(1, len(self.laps)-1):
            times.append(self.getLapTime(f))
        return times

    def getDataPointsAvail(self):
        dataPoints = []
        for lap in self.laps:
            for measurement in lap:
                for point in measurement.keys():
                    if point not in dataPoints:
                        dataPoints.append(point)
        return dataPoints
    
    def getSegments(self):
        sessRet = []
        for lap in self.laps:
            thisLap = []
            for segment in range(len(self.waypoints)):
                thisLap.append([])              
            for measurement in lap:
                thisLap[measurement["segment"]-1].append(measurement)
            sessRet.append(thisLap)
        return sessRet
    
    def getImageBoundaries(self):
        southWest = []
        northEast = []
        southWest = [self.trackStartFinish[0], self.trackStartFinish[1]]
        northEast = [self.trackStartFinish[0], self.trackStartFinish[1]]
        for lap in self.laps:
            for measurement in lap:
                if abs(measurement["GPSlat"]) < abs(southWest[0]):
                    southWest[0] = measurement["GPSlat"]
                if abs(measurement["GPSlat"]) > abs(northEast[0]):
                    northEast[0] = measurement["GPSlat"]
                if abs(measurement["GPSlng"]) > abs(southWest[1]):
                    southWest[1] = measurement["GPSlng"]
                if abs(measurement["GPSlng"]) < abs(northEast[1]):
                    northEast[1] = measurement["GPSlng"]
        return [southWest, northEast]

    def getSeriesBoundaries(self, measurements):
        southWest = []
        northEast = []
        southWest = [measurements[0]["GPSlat"], measurements[0]["GPSlng"]]
        northEast = [measurements[0]["GPSlat"], measurements[0]["GPSlng"]]
        for measurement in measurements:
            if abs(measurement["GPSlat"]) < abs(southWest[0]):
                southWest[0] = measurement["GPSlat"]
            if abs(measurement["GPSlat"]) > abs(northEast[0]):
                northEast[0] = measurement["GPSlat"]
            if abs(measurement["GPSlng"]) > abs(southWest[1]):
                southWest[1] = measurement["GPSlng"]
            if abs(measurement["GPSlng"]) < abs(northEast[1]):
                northEast[1] = measurement["GPSlng"]
        return [southWest, northEast]

    def getSeriesCenterpoint(self, measurements):
        [sw, ne] = self.getSeriesBoundaries(measurements)
        return [ (sw[0]+ne[0])/2, (sw[1]+ne[1])/2 ]

    def getMapLocation(self):
        return [self.trackStartFinish[0], self.trackStartFinish[1]]
    
    def getLaps(self):
        return self.laps
    
    def getSegmentsByTime(self, segNum):
        segments = []
        shortSegment = []
        lapNum = 0 
        for lap in self.laps:
            lapNum += 1
            for measurement in lap:
                if measurement["segment"] == segNum:
                    shortSegment.append(measurement)
            segTime = shortSegment[-1]["time"] - shortSegment[0]["time"]
            segments.append({"time": segTime, "path": shortSegment, "lap": lapNum})
            shortSegment=[]
        return segments
    
    def getSegmentTimes(self, segmentNum):
        segments = self.getSegmentsByTime(segmentNum)
        times = [float(item["time"]) for item in segments]
        return times
    
    def getSegmentHotTimes(self, segmentNum):
        segments = self.getSegmentsByTime(segmentNum)
        times = [float(item["time"]) for item in segments[1:-2]]
        return times
    
    def getSegmentMinimum(self, segmentNum):
        segments = self.getSegmentsByTime(segmentNum)
        times = [float(item["time"]) for item in segments]
        return min(times)
    
    def getSegmentHotMinimum(self, segmentNum):
        segments = self.getSegmentsByTime(segmentNum)
        times = [float(item["time"]) for item in segments[1:-2]]
        return min(times)
    
    def getSegmentMinDelta(self, segmentNum):
        segments = self.getSegmentsByTime(segmentNum)
        times = sorted([float(item["time"]) for item in segments])
        return times[1]-times[0]
    
    def getSegmentHotMinDelta(self, segmentNum):
        segments = self.getSegmentsByTime(segmentNum)
        times = sorted([float(item["time"]) for item in segments[1:-2]])
        return times[1]-times[0]