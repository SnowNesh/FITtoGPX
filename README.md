# FITtoGPX

Generiert aus einer FIT-Datei eine GPX-Datei.  
Grund des Projekts: Bei langen Garminaktivitäten lassen sich neuerdings keine GPX-Dateien mehr herunterladen, da sie laut Garmin "zu groß" sind.

Übernommen wird:
- Koordinate  
- Höhe  
- Zeit  
- Herzfrequenz  
- Trittfrequenz

Garmin Dateinamen werden umgedreht "GarminNumber_ACTIVITY.fit" → "activity_GarminNumber.gpx". Da die gpx Dateien von Garmin beim herunterladen so benannt werden.  
