from src.modules.imaging.kml import KMLGenerator, LatLong


kml = KMLGenerator()

hotspot_1 = LatLong(1,1)
hotspot_2 = LatLong(1,2)
hotspot_3 = LatLong(0,0)

kml.push(hotspot_1)
kml.push(hotspot_2)
kml.push(hotspot_3)

print(kml.read(-1).latitude, kml.read(-1).longitude)
kml.pop()

print(kml.read(-1).latitude, kml.read(-1).longitude)

kml.set_source("Crashed Drone", LatLong(24, 24))

kml.generate("out.kml")
