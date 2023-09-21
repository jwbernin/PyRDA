#!/usr/bin/python3

# Main file for track session analysis.

from dataImporter import *
from datamodel import TrackSession
import folium
import math
import argparse
import os, os.path, shutil, io
import utils
import base64

outputDir = "../RDA-output"

parser = argparse.ArgumentParser(description='Run analysis on track data file')
parser.add_argument('-f', '--file', action='append', help='Filename with data to be analyzed. Can be specified multiple times.')
parser.add_argument('-v', '--verbose', action='count')
parser.add_argument('-t', '--trackname', action='store', help='Name of track data is from, if not present in file (e.g. TrackAddict data). Can only analyze one track per run unless track name is present in datafile.')

args = parser.parse_args()

def debugout(debuglevel, text):
    if debuglevel >= args.verbose:
        print(text)

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

    if args.gg_maps:
        x = []
        y = []
        for lap in session.getLaps():
            for measurement in lap:
                x.append(measurement["lateralAccel"])
                y.append(measurement["inlineAccel"])
        plt.plot(np.array(x), np.array(y), '.k')
        imgBuf = io.BytesIO()
        plt.savefig(imgBuf, format='png')
        imgBuf.seek(0)
        mapsList["sessionGGMap"] = base64.b64encode(imgBuf.read()).decode("utf-8")

    if args.individual_lap_maps:
        boundingBox = session.getImageBoundaries()
        location = session.getMapLocation()

        lapMaps = []
        lapGGMaps = []
        for lap in session.getLaps():
            map = folium.Map(location=location, zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community")
            map.fit_bounds(boundingBox)
            mapPoints = []
            x = []
            y = []
            for measurement in lap:
                mapPoints.append([measurement["GPSlat"], measurement["GPSlng"]])
                x.append(measurement["lateralAccel"])
                y.append(measurement["inlineAccel"])
            folium.PolyLine(mapPoints).add_to(map)
            imgData = map._to_png(3)
            lapMaps.append(base64.b64encode(imgData).decode("utf-8"))
            plt.plot(np.array(x), np.array(y), '.k')
            imgData = io.BytesIO()
            plt.savefig(imgData, format='png')
            imgData.seek(0)
            lapGGMaps.append(base64.b64encode(imgData.read()).decode("utf-8"))
        mapsList["individualLapMaps"] = lapMaps
        mapsList["individualGGmaps"] = lapGGMaps

    if args.segments:
        # Generate individual segment traces, plot on different maps.
        segmentMaps = []
        brakeMaps = []
        throttleMaps = []
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

            if not args.gps_only:
                # Work on fastest segment only (traces[0]) for brake/throttle maps
                brakeMap = folium.Map(location=session.getSeriesCenterpoint(traces[0]["path"]), zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community")
                for point in traces[0]["path"]:
                    if point["brake"] > 0:
                        folium.CircleMarker(location=[point["GPSlat"], point["GPSlng"]], radius=1, color="red").add_to(brakeMap)
                brakeMap.fit_bounds(session.getSeriesBoundaries(traces[0]["path"]))
                imgData = brakeMap._to_png(3)
                brakeMaps.append(base64.b64encode(imgData).decode("utf-8"))

                throttleMap = folium.Map(location=session.getSeriesCenterpoint(traces[0]["path"]), zoom_start=15, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community")
                for point in traces[0]["path"]:
                    # Even at idle, there is some throttle positive position. This value may require adjustment.
                    if point["throttle"] > 5:
                        if point["throttle"] > 75:
                            folium.CircleMarker(location=[point["GPSlat"], point["GPSlng"]], radius=1, color="orange").add_to(throttleMap)
                        elif point["throttle"] > 35:
                            folium.CircleMarker(location=[point["GPSlat"], point["GPSlng"]], radius=1, color="lightgreen").add_to(throttleMap)
                        else:
                            folium.CircleMarker(location=[point["GPSlat"], point["GPSlng"]], radius=1, color="green").add_to(throttleMap)
                throttleMap.fit_bounds(session.getSeriesBoundaries(traces[0]["path"]))
                imgData = throttleMap._to_png(3)
                throttleMaps.append(base64.b64encode(imgData).decode("utf-8"))


        mapsList["segmentMaps"] = segmentMaps
        if not args.gps_only:
            mapsList["brakeMaps"] = brakeMaps
            mapsList["throttleMaps"] = throttleMaps
        

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