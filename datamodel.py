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

class TrackSession:
    def __init__(self):
        self.laps = []
        self.sessioninfo = {}
        self.numLaps = 0

    # Add session metadata
    def addSessionInfo(self, **kwargs):
        for k,v in kwargs.iteritems():
            self.sessioninfo[k] = v

    def addLap(self):
        newLap = []
        self.laps.append(newLap)
        self.numLaps += 1
        assert self.numLaps = len(self.laps)

    def addMeasurement(self, timeChop, **kwargs):
        measurement = {"time":timechop}
        for k,v in kwargs.iteritems():
            measurement[k]=v
        self.laps[-1].append(measurement)

    def getLastLocation(self):
        measurement = self.laps[-1][-1]
        return (measurement.GPSlat, measurement.GPSlong)
