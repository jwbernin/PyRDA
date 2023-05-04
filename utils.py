#!/usr/bin/python3

# Utility functions
import geopy.distance
import pprint

def calculateGPSdistance(location1, location2):
  distanceInFeet = geopy.distance.distance(location1, location2).feet
  return distanceInFeet

if __name__ == '__main__':
  print("This file should not be called directly.")