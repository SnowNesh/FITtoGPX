import os
import sys
import subprocess
import xml.etree.ElementTree as ET

# Bibliotheken bei Bedarf installieren
for pkg in ("fitparse", "gpxpy"):
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

from fitparse import FitFile
import gpxpy
import gpxpy.gpx

INPUT_DIR = "_FIT"
OUTPUT_DIR = "_GPX"
os.makedirs(OUTPUT_DIR, exist_ok=True)

for fname in os.listdir(INPUT_DIR):
    if not fname.lower().endswith(".fit"):
        continue

    fitfile = FitFile(os.path.join(INPUT_DIR, fname))
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)
    gpx.tracks.append(track)

    for record in fitfile.get_messages("record"):
        data = {f.name: f.value for f in record.fields}
        lat_s = data.get("position_lat")
        lon_s = data.get("position_long")
        if lat_s is None or lon_s is None:
            continue
        lat = lat_s * (180.0 / 2**31)
        lon = lon_s * (180.0 / 2**31)
        pt = gpxpy.gpx.GPXTrackPoint(
            latitude=lat,
            longitude=lon,
            elevation=data.get("position_altitude"),
            time=data.get("timestamp")
        )
        hr = data.get("heart_rate")
        cad = data.get("cadence")
        if hr is not None or cad is not None:
            ext = ET.Element("extensions")
            tpe = ET.SubElement(ext, "gpxtpx:TrackPointExtension")
            if hr is not None:
                e_hr = ET.SubElement(tpe, "gpxtpx:hr"); e_hr.text = str(hr)
            if cad is not None:
                e_cad = ET.SubElement(tpe, "gpxtpx:cad"); e_cad.text = str(cad)
            pt.extensions = ext

        segment.points.append(pt)

    out_path = os.path.join(OUTPUT_DIR, os.path.splitext(fname)[0] + ".gpx")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(gpx.to_xml())