import json
from src.modules.autopilot.lander import Lander
from src.modules.georeference import inference_georeference

with open('./samples/geofence.json', 'r') as f:
    geofence = json.load(f)['features'][0]['geometry']['coordinates'][0]


origin = [-113.54815575690603, 53.495546666117804]

geofence = inference_georeference.Geofence_to_XY(origin, geofence)
print(geofence)

lander = Lander(0, 0, geofence)
'''
point1 = [53.4958, -113.5477]
point2 = [53.4956, -113.5481]
point3 = [53.4956, -113.5475]
point4 = [53.4955, -113.5488]
point5 = [53.4955, -113.5488]
'''
point1 = [0, 0]
point2 = [5, 5]
point3 = [10, 10]
point4 = [-5, -5]
point5 = [-10, 10]
point6 = [30.4,
          30.4]
point7 = [-113.54827877970348,
          53.49573842746909]


print(lander.geofence_check(point1))
print(lander.geofence_check(point2))
print(lander.geofence_check(point3))
print(lander.geofence_check(point4))
print(lander.geofence_check(point5))
print(lander.geofence_check(point6))
print(lander.geofence_check(point7))


