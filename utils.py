#!/usr/bin/python3

# Utility functions
import geopy.distance
import pprint

def calculateGPSdistance(location1, location2):
  distanceInFeet = geopy.distance.distance(location1, location2).feet
  return distanceInFeet

# The normal Python list sorting functions are behaving strangely. I think because the list is a complex type.
# So, we're going back to basics and doing a recursive sort here.
def sortSegments(listToSort):
  if len(listToSort) == 1:
    return listToSort

  shortestSegmentIndex = 0
  try:
    for idx, [time, points] in listToSort:
      if time < listToSort[shortestSegmentIndex][0]:
        shortestSegmentIndex = idx
  except ValueError:
    pprint.pprint(listToSort)
    
  savePoints = listToSort[shortestSegmentIndex][1]

  del listToSort[shortestSegmentIndex]

  saveItem = [time, savePoints]

  return [saveItem].append(sortSegments(listToSort))


    





if __name__ == '__main__':
  print("This file should not be called directly.")