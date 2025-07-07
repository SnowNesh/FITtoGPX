import os
import sys
import xml.etree.ElementTree as ET
import re
from fitparse import FitFile
import gpxpy
import gpxpy.gpx

INPUT_DIR, OUTPUT_DIR = "_FIT", "_GPX"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Garmin GPXTpx namespace and schema
GPTP_NS = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
EXT_SCHEMA = "http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd"

for fname in os.listdir(INPUT_DIR):
    if not fname.lower().endswith(".fit"):
        continue

    fit_path = os.path.join(INPUT_DIR, fname)
    try:
        # Try to open FIT file
        fit = FitFile(fit_path)
    except Exception as e:
        print(f"Error opening FIT file {fname}: {e}")
        continue

    gpx = gpxpy.gpx.GPX()
    trk = gpxpy.gpx.GPXTrack()
    seg = gpxpy.gpx.GPXTrackSegment()
    trk.segments.append(seg)
    gpx.tracks.append(trk)

    try:
        for rec in fit.get_messages("record"):
            try:
                d = {f.name: f.value for f in rec.fields}
                lat_s, lon_s = d.get("position_lat"), d.get("position_long")
                if lat_s is None or lon_s is None:
                    continue
                lat = lat_s * (180.0 / 2**31)
                lon = lon_s * (180.0 / 2**31)
                ele = d.get("position_altitude") or d.get("altitude") or d.get("enhanced_altitude")
                pt = gpxpy.gpx.GPXTrackPoint(
                    latitude=lat,
                    longitude=lon,
                    elevation=ele,
                    time=d.get("timestamp")
                )

                hr, cad = d.get("heart_rate"), d.get("cadence")
                if hr is not None or cad is not None:
                    ext = ET.Element("extensions")
                    tpe = ET.SubElement(ext, "gpxtpx:TrackPointExtension")
                    if hr is not None:
                        ET.SubElement(tpe, "gpxtpx:hr").text = str(hr)
                    if cad is not None:
                        ET.SubElement(tpe, "gpxtpx:cad").text = str(cad)
                    pt.extensions = ext

                seg.points.append(pt)
            except Exception as e:
                print(f"Error processing record in {fname}: {e}")
                continue
    except Exception as e:
        print(f"Error parsing messages in {fname}: {e}")
        continue

    try:
        # Create XML and adjust time format by adding 'Z'
        xml = gpx.to_xml()
        xml = re.sub(
            r'(<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.\d+)?(?:Z|[+\-]\d{2}:\d{2})?(</time>)',
            r'\1.000Z\2',
            xml
        )
        # Insert GPXTpx namespace in the root element
        xml = xml.replace(
            '<gpx xmlns="http://www.topografix.com/GPX/1/1"',
            f'<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxtpx="{GPTP_NS}"'
        )
        # Extend schemaLocation
        xml = re.sub(
            r'(xsi:schemaLocation="[^"]+)"',
            lambda m: f"{m.group(1)} http://www.garmin.com/xmlschemas/TrackPointExtension/v1 {EXT_SCHEMA}\"",
            xml
        )

        # Construct new file name according to Garmin convention
        base = os.path.splitext(fname)[0]
        try:
            id_part, act_part = base.split("_", 1)
            new_name = f"{act_part.lower()}_{id_part}.gpx"
        except Exception as e:
            print(f"Error constructing output filename for {fname}: {e}")
            new_name = base + ".gpx"

        out_path = os.path.join(OUTPUT_DIR, new_name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(xml)
    except Exception as e:
        print(f"Error creating or writing GPX for {fname}: {e}")
        continue
