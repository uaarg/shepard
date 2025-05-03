from dataclasses import dataclass
import copy
from typing import List, Optional

@dataclass
class LatLong:
    latitude: float
    longitude: float

class KMLGenerator:

    def __init__(self) -> None:
        self.hotspots: List[LatLong]= []
        self.length = 0
        self.source = ""
        self.source_coords: LatLong


    def push(self, coords: LatLong):
        """push hotspot onto stack"""

        self.hotspots.append(coords)
        self.length += 1

    def pop(self):
        """remove a hotspot from the stack"""

        if len(self.hotspots) != 0:
            self.hotspots.pop()
            self.length -= 1

    def read(self, index:int) -> Optional[LatLong]:
        """reads value in stack at index position
        return None if index does not exist"""

        try:
            return copy.deepcopy(self.hotspots[index]) 

        except IndexError:
            return None

    def set_source(self, source: str, coords: LatLong):

        self.source = source
        self.source_coords = coords

    def generate(self, path: str):
        """generate KML file at given path"""

        with open(path, 'w') as f:

            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
            f.write('  <Document>\n')
    
            # add source
            f.write('    <Placemark>\n')
            f.write('      <name>Source</name>\n')
            f.write(f'     <description>{self.source}</description>\n')
            f.write('      <Point>\n')
            f.write('\n')
            f.write(f'<coordinates>{self.source_coords.latitude},{self.source_coords.longitude},0</coordinates>\n')
            f.write('      </Point>\n')
            f.write('    </Placemark>\n')

            # add hotspots
            for i, coords in enumerate(self.hotspots, start=1):
                f.write('    <Placemark>\n')
                f.write(f'      <name>Hotspot {i}</name>\n')
                f.write('    <Point>\n')
                f.write(f'      <coordinates>{coords.longitude},{coords.latitude},0</coordinates>\n')
                f.write('    </Point>\n')
                f.write('\n')
                f.write('  </Placemark>\n')

            f.write('</Document>\n')
            f.write('</kml>\n')


