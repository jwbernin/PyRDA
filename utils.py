#!/usr/bin/python3

# Utility functions
import geopy.distance
import pprint

def calculateGPSdistace(location1, location2):
  distanceInFeet = geopy.distance.distance(location1, location2).feet
  return distanceInFeet

def DEBUG(level, debugString):
  global debuglevel
  if debuglevel >= level:
    print (debugString)

if __name__ == '__main__':
  print("This file should not be called directly.")