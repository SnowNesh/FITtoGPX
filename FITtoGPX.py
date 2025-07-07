import os
import sys
import xml.etree.ElementTree as ET
import re
from fitparse import FitFile
import gpxpy
import gpxpy.gpx

INPUT_DIR, OUTPUT_DIR = "_FIT", "_GPX"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Garmin GPXTpx-Namespace
GPTP_NS = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
EXT_SCHEMA = "http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd"

for fname in os.listdir(INPUT_DIR):
    if not fname.lower().endswith(".fit"):
        continue

    fit = FitFile(os.path.join(INPUT_DIR, fname))
    gpx, trk, seg = gpxpy.gpx.GPX(), gpxpy.gpx.GPXTrack(), gpxpy.gpx.GPXTrackSegment()
    trk.segments.append(seg); gpx.tracks.append(trk)

    for rec in fit.get_messages("record"):
        d = {f.name: f.value for f in rec.fields}
        lat_s, lon_s = d.get("position_lat"), d.get("position_long")
        if lat_s is None or lon_s is None:
            continue
        lat = lat_s * (180.0 / 2**31); lon = lon_s * (180.0 / 2**31)
        ele = d.get("position_altitude") or d.get("altitude") or d.get("enhanced_altitude")
        pt = gpxpy.gpx.GPXTrackPoint(latitude=lat, longitude=lon, elevation=ele, time=d.get("timestamp"))

        hr, cad = d.get("heart_rate"), d.get("cadence")
        if hr is not None or cad is not None:
            ext = ET.Element("extensions")
            tpe = ET.SubElement(ext, "gpxtpx:TrackPointExtension")
            if hr  is not None: ET.SubElement(tpe, "gpxtpx:hr").text  = str(hr)
            if cad is not None: ET.SubElement(tpe, "gpxtpx:cad").text = str(cad)
            pt.extensions = ext

        seg.points.append(pt)

    # Create XML and change TimeFormat and add 'Z'
    xml = gpx.to_xml()
    # Zeitformat angleichen
    xml = re.sub(
        r'(<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.\d+)?(?:Z|[+\-]\d{2}:\d{2})?(</time>)',
        r'\1.000Z\2',
        xml
    )
    # GPXTpx-Namespace root insert
    xml = xml.replace(
        '<gpx xmlns="http://www.topografix.com/GPX/1/1"',
        f'<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxtpx="{GPTP_NS}"'
    )
    # Extend SchemaLocation
    xml = re.sub(
        r'(xsi:schemaLocation="[^"]+)"',
        lambda m: f"{m.group(1)} http://www.garmin.com/xmlschemas/TrackPointExtension/v1 {EXT_SCHEMA}" + '"',
        xml
    )

    # Meet Garmin GPX Filename convention: "00000000000_ACTIVITY.fit" → "activity_00000000000.gpx"
    base = os.path.splitext(fname)[0]
    id_part, act_part = base.split("_", 1)
    new_name = f"{act_part.lower()}_{id_part}.gpx"

    with open(os.path.join(OUTPUT_DIR, new_name), "w", encoding="utf-8") as f:
        f.write(xml)
