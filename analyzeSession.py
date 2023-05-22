#!/usr/bin/python3

# Main file for track session analysis.

from dataImporter import *
from datamodel import TrackSession
import folium
import math
import argparse
from jinja2 import Environment, FileSystemLoader
from pdfkit import from_string
import os, os.path, shutil, io
from PIL import Image
import utils
import base64

outputDir = "../RDA-output"

parser = argparse.ArgumentParser(description='Run analysis on track data file')
parser.add_argument('-f', '--file', action='append', help='Filename with data to be analyzed. Can be specified multiple times.')
parser.add_argument('-v', '--verbose', action='count')
parser.add_argument('-t', '--trackname', action='store', help='Name of track data is from, if not present in file (e.g. TrackAddict data). Can only analyze one track per run unless track name is present in datafile.')
parser.add_argument('--text-results', action=argparse.BooleanOptionalAction, help='Show results in text in terminal (default: FALSE)', default=False)
gengroup = parser.add_argument_group("General analysis options")
gengroup.add_argument('--laps', action=argparse.BooleanOptionalAction, help='Show / don\'t show lap data (default: TRUE)', default=True)
gengroup.add_argument('--segments', action=argparse.BooleanOptionalAction, help='Show / don\'t show segment data (default: FALSE)')
gengroup.add_argument('--list-datapoints', action='store_true', help='List the data points available in the file(s)')
gengroup.add_argument('--combined-lap-map', action=argparse.BooleanOptionalAction, help='Show a map of all laps driven (default: TRUE)', default=True)
gengroup.add_argument('--individual-lap-maps', action=argparse.BooleanOptionalAction, help='Show maps of the individual laps (default: FALSE)', default=False)
segparser = parser.add_argument_group('Segment analysis options')
segparser.add_argument('--delta', action=argparse.BooleanOptionalAction, help='Show segment time deltas from best segment time')

args = parser.parse_args()

def textout(text):
    if args.text_results:
        print(text)

def analyze(session):
    mapsList = {}
    outputFilename = '-'.join([session.getSessionInfo("driverName"),
                               session.getSessionInfo("trackName"),
                               session.getSessionInfo("sessionDate"),
                               session.getSessionInfo("sessionTime")])
    if os.path.exists(outputFilename+'.pdf'):
        increment=1
        while os.path.exists(outputFilename+"-"+str(increment)+'.pdf'):
            increment+=1
        outputFilename += '-'+str(increment)
    outputFilename += '.pdf'

    # Tell us which session we're looking at
    textout(f'Analyzing data from { session.getSessionInfo("sourcefile") }')
    if session.getSessionInfo('trackName') is not None:
        textout(f'Track name: { session.getSessionInfo("trackName") }') 
    if session.getSessionInfo('trackDescription') is not None:
        textout(f'Track description: { session.getSessionInfo("trackDescription") }') 
    if session.getSessionInfo('sessionDate') is not None:
        textout(f'Session date: { session.getSessionInfo("sessionDate") }') 
    if session.getSessionInfo('sessionTime') is not None:
        textout(f'Session time: { session.getSessionInfo("sessionTime") }') 

    textout ("")
    if args.list_datapoints:
        textout('These datapoints are available:')
        for point in session.getDataPointsAvail():
            textout (f"- {point}")
        return

    if args.laps:    
        textout("Lap times")
        textout("---------")
        for count,lap in enumerate(session.getLapTimes()):
            textout(f"Lap { count }: {math.trunc(lap/60):02}:{lap%60:0>6.3f}")

    if args.combined_lap_map:
        boundingBox = session.getImageBoundaries()
        location = session.getMapLocation()
        mapPoints = []
        sessionMap = folium.Map(location=location, zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community")
        sessionMap.fit_bounds(boundingBox)
        for lap in session.getLaps():
            for measurement in lap:
                mapPoints.append([measurement["GPSlat"], measurement["GPSlng"]])
        folium.PolyLine(mapPoints).add_to(sessionMap)
        imgData = sessionMap._to_png(3)
        mapsList['combinedLapMap'] = base64.b64encode(imgData).decode("utf-8")

    if args.individual_lap_maps:
        boundingBox = session.getImageBoundaries()
        location = session.getMapLocation()

        lapMaps = []
        for lap in session.getLaps():
            map = folium.Map(location=location, zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community")
            map.fit_bounds(boundingBox)
            mapPoints = []
            for measurement in lap:
                mapPoints.append([measurement["GPSlat"], measurement["GPSlng"]])
            folium.PolyLine(mapPoints).add_to(map)
            imgData = map._to_png(3)
            lapMaps.append(base64.b64encode(imgData).decode("utf-8"))
        mapsList["individualLapMaps"] = lapMaps

    if args.segments:
        # Generate individual segment traces, plot on different maps.
        segmentMaps = []
        for segment in range(1, len(session.waypoints)+2):
            segmentNum = segment
            traces = sorted(session.getSegmentsByTime(segmentNum), key=lambda x: x['time'])

            # if this is the last segment and the fastest lap is the last lap, discard it because that's the in-segment
            # and we want to see the actual fastest during-segment. The in-segment is likely to be the fastest simply because
            # it's so much shorter, even if we are slower
            if segmentNum == len(session.waypoints)+1 and session.numLaps == int(traces[0]["lap"]):
                del traces[0]

            map = folium.Map(location=session.getSeriesCenterpoint(traces[0]["path"]), zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community")

            for trace in traces:
                mapPoints = []
                for pt in trace["path"]:
                    mapPoints.append([pt["GPSlat"], pt["GPSlng"]])
                folium.PolyLine(mapPoints, smooth_factor=0.0).add_to(map)

            mapPoints = []
            for pt in traces[0]["path"]:
                mapPoints.append([pt["GPSlat"], pt["GPSlng"]])
            folium.PolyLine(mapPoints, color="red", smooth_factor=0.0).add_to(map)
            map.fit_bounds(session.getSeriesBoundaries(traces[1]["path"]))
            imgData = map._to_png(3)
            segmentMaps.append(base64.b64encode(imgData).decode("utf-8"))
            mapsList["segmentMaps"] = segmentMaps

    fileLoader = FileSystemLoader('templates')
    env = Environment(loader=fileLoader)
    env.filters['floataverage'] = utils.averageFilter
    env.filters['stddev'] = utils.stdDevFilter
    template = env.get_template('render.j2')
    output = template.render(session=session, args=args, maps=mapsList)
    file_content = from_string(output, False)
    try:
        with open(outputDir+'/'+outputFilename, 'wb+') as file:
            file.write(file_content)

    except Exception as error:
        textout (f'Error encountered: {error}')

def main():
    runs = []
    for file in args.file:
        dataReader = getFileImporter(file)
        runs.append(dataReader.readSessionData())
        runs[-1].addSessionInfo(sourcefile = file)
        runs[-1].trimEnds()

    # Prepare the output directory - create if necessary, clean up if necessary
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    for run in runs:
        analyze(run)

if __name__ == '__main__':
    main()