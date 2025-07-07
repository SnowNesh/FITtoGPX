import os
import sys
import xml.etree.ElementTree as ET
import re
import configparser
from fitparse import FitFile
import gpxpy
import gpxpy.gpx
from datetime import datetime

# Constants for input/output directories and log/config file names
INPUT_DIR, OUTPUT_DIR = "_FIT", "_GPX"
INFO_LOG_FILE = "info.log"
ERROR_LOG_FILE = "error.log"
CONFIG_FILE = "config.ini"

def load_config():
    """
    Loads configuration from config.ini.
    Returns: delete_fit (bool) - whether to delete the .fit file after conversion.
    """
    config = configparser.ConfigParser()
    # Default value is false
    defaults = {'delete_fit_after_conversion': 'false'}
    config['DEFAULT'] = defaults
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config.read_file(f)
    except Exception:
        # Use defaults if config.ini does not exist or is not readable
        pass
    # Always return boolean value for the flag
    return config.getboolean('DEFAULT', 'delete_fit_after_conversion', fallback=False)

# Read config at startup
delete_fit = load_config()

# Ensure output and input directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(INPUT_DIR, exist_ok=True)

def log_info(message, fitfile):
    """
    Logs informational messages with timestamp and fit filename.
    """
    with open(INFO_LOG_FILE, "a", encoding="utf-8") as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{now} [{fitfile}] {message}\n")

def log_error(message):
    """
    Logs error messages with timestamp.
    """
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{now} {message}\n")

# Iterate over all .fit files in the input directory
for fname in os.listdir(INPUT_DIR):
    if not fname.lower().endswith(".fit"):
        continue

    fit_path = os.path.join(INPUT_DIR, fname)
    try:
        fit = FitFile(fit_path)
    except Exception as e:
        log_error(f"Error opening FIT file {fname}: {e}")
        continue

    # Create GPX objects
    gpx = gpxpy.gpx.GPX()
    trk = gpxpy.gpx.GPXTrack()
    seg = gpxpy.gpx.GPXTrackSegment()
    trk.segments.append(seg)
    gpx.tracks.append(trk)

    records_converted = 0

    try:
        # Process each record in the FIT file
        for rec in fit.get_messages("record"):
            try:
                d = {f.name: f.value for f in rec.fields}
                lat_s, lon_s = d.get("position_lat"), d.get("position_long")
                if lat_s is None or lon_s is None:
                    continue
                # Convert FIT coordinates to degrees
                lat = lat_s * (180.0 / 2**31)
                lon = lon_s * (180.0 / 2**31)
                # Get elevation (try different possible fields)
                ele = d.get("position_altitude") or d.get("altitude") or d.get("enhanced_altitude")
                pt = gpxpy.gpx.GPXTrackPoint(
                    latitude=lat,
                    longitude=lon,
                    elevation=ele,
                    time=d.get("timestamp")
                )

                # Add heart rate and cadence as extensions if present
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
                records_converted += 1
            except Exception as e:
                # Log errors for individual records but continue processing
                log_error(f"Error processing record in {fname}: {e}")
                continue
    except Exception as e:
        # Log errors for the whole FIT file if parsing fails
        log_error(f"Error parsing messages in {fname}: {e}")
        continue

    try:
        # Create XML string and adjust time format by adding 'Z'
        xml = gpx.to_xml()
        xml = re.sub(
            r'(<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.\d+)?(?:Z|[+\-]\d{2}:\d{2})?(</time>)',
            r'\1.000Z\2',
            xml
        )
        # Add GPXTpx namespace and schema location
        GPTP_NS = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
        EXT_SCHEMA = "http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd"
        xml = xml.replace(
            '<gpx xmlns="http://www.topografix.com/GPX/1/1"',
            f'<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:gpxtpx="{GPTP_NS}"'
        )
        xml = re.sub(
            r'(xsi:schemaLocation="[^"]+)"',
            lambda m: f"{m.group(1)} http://www.garmin.com/xmlschemas/TrackPointExtension/v1 {EXT_SCHEMA}\"",
            xml
        )

        # Construct new output file name according to Garmin convention
        base = os.path.splitext(fname)[0]
        try:
            id_part, act_part = base.split("_", 1)
            new_name = f"{act_part.lower()}_{id_part}.gpx"
        except Exception as e:
            log_error(f"Error constructing output filename for {fname}: {e}")
            new_name = base + ".gpx"

        out_path = os.path.join(OUTPUT_DIR, new_name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(xml)
        log_info(f"Successfully converted to {new_name} ({records_converted} records).", fname)

        # Delete the FIT file after conversion if configured in config.ini
        if delete_fit:
            try:
                os.remove(fit_path)
                log_info(f"Deleted FIT file after conversion: {fname}", fname)
            except Exception as e:
                log_error(f"Error deleting FIT file {fname}: {e}")

    except Exception as e:
        log_error(f"Error creating or writing GPX for {fname}: {e}")
        continue
