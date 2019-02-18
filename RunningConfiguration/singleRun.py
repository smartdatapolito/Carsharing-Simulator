import sys
import os
p = os.path.abspath('..')
sys.path.append(p+"/")

import pickle
from Support.DataCreation import assingVariables
import Simulator.Globals.GlobalVar as gv
from Simulator.Simulator import *


import pprint
pp = pprint.PrettyPrinter()

city = 'Torino'
gv.init()
assingVariables(city)

WalkingTreshold = 1000000
city = "Torino"
zones = sf.numberOfZones(city)
algorithm = "max-parking"
numberOfStations = 20
TankThreshold = 100
PolesPerStation = 4
BestEffort = True
pThreshold = 1
randomInitLvl = False
return_dict = {}
Gamma=1
Zone_Cars = pickle.load( open( "../input/"+ city + "_" + gv.provider +"_ZoneCars.p", "rb" ) )
Zone_DistanceFromZones = pickle.load( open( "../input/"+ city + "_" + gv.provider + "_ZoneDistances.p", "rb" ) )
Stamps_Events = pickle.load( open( "../events/"+ city + "_" + gv.provider + "_sorted_dict_events_obj.pkl", "rb" ) )

ChargingStationsZones = sf.loadRecharing(algorithm, numberOfStations, city)
# RechargingStation_Zones = [1,2,3,4,6]
print(ChargingStationsZones)

zzz = RunSim(BestEffort,
      algorithm,
      PolesPerStation,
      TankThreshold,
      WalkingTreshold,
      Zone_Cars,
      ChargingStationsZones,
      Stamps_Events,
      Zone_DistanceFromZones,
      46,
      pThreshold,
      2.0,
      Gamma,
      randomInitLvl,
      None,
      6,
      1,
      city)



for k in zzz.keys():
    print(k, zzz[k])
