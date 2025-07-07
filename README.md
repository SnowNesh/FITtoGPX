# FITtoGPX

## English

This tool converts a `.fit` file into a `.gpx` file.

**Background:**  
For long Garmin activities, it is no longer possible to download GPX files directly from Garmin, as they are now considered "too large".

The following data is included in the conversion:
- Coordinates  
- Elevation  
- Time  
- Heart rate  
- Cadence  

Garmin filenames are renamed from `GarminNumber_ACTIVITY.fit` to `activity_GarminNumber.gpx`, matching the naming convention Garmin uses when exporting GPX files.

**Requirements** 

- Python 3.6 or higher
- Required Python packages are listed in `requirements.txt`

---

## Deutsch

Dieses Tool konvertiert eine `.fit`-Datei in eine `.gpx`-Datei.

**Hintergrund:**  
Bei langen Garmin-Aktivitäten ist es neuerdings nicht mehr möglich, GPX-Dateien direkt von Garmin herunterzuladen, da sie laut Garmin „zu groß“ sind.

Folgende Daten werden übernommen:
- Koordinaten  
- Höhe  
- Zeit  
- Herzfrequenz  
- Trittfrequenz  

Garmin-Dateinamen werden umbenannt von `GarminNumber_ACTIVITY.fit` zu `activity_GarminNumber.gpx`, entsprechend der Benennung, die Garmin beim GPX-Export verwendet.

**Voraussetzungen**

- Python 3.6 oder höher
- Benötigte Python-Pakete stehen in `requirements.txt`
