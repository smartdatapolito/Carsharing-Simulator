import sys
import os
p = os.path.abspath('..')
sys.path.append(p+"/")



import pickle
import operator
from Simulator.Classes.Distance import Distance
from Simulator.Classes.Car import Car
from Simulator.Classes.Zone import Zone
from geopy.geocoders import Nominatim
from math import *
import Simulator.Globals.SupportFunctions as sf
import Simulator.Globals.GlobalVar as gv
import Support.DataCreation as dc



def EvalDistance(i,j):
    Xi =  i % gv.NColumns
    Yi = int(i / gv.NColumns)
    
    Xj = j % gv.NColumns
    Yj = int( j/ gv.NColumns)

    CentalLoni = (Xi + 0.5) * gv.ShiftLon + gv.minLon
    CentalLati = (Yi + 0.5) * gv.ShiftLat + gv.minLat
    CentalLonj = (Xj + 0.5) * gv.ShiftLon + gv.minLon
    CentalLatj = (Yj + 0.5) * gv.ShiftLat + gv.minLat
        
    dh = sf.haversine(CentalLoni, CentalLati, CentalLonj, CentalLatj)

    de = sqrt(pow((Xi-Xj),2)+pow((Yi-Yj),2)) 

    return de,dh

def AppendCaselle(i,ZoneDistances):

    Xi = i % gv.NColumns
    Yi = int(i / gv.NColumns)
    CentalLon = (Xi + 0.5) * gv.ShiftLon + gv.minLon
    CentalLat = (Yi + 0.5) * gv.ShiftLat + gv.minLat
    Caselle = gv.NColumns * gv.NRows
    de, dh = EvalDistance(i, Caselle*3)
    # dh = haversine(CentalLon, CentalLat, CaselleCentralLon, CaselleCentralLat)
    RealDistance = dh
    if (de not in ZoneDistances[i]) :
        ZoneDistances[i][de] = Distance(RealDistance) 
    ZoneDistances[i][de].appendZone(Caselle)
    if(i!=Caselle):
        if(de not in ZoneDistances[Caselle]):
            ZoneDistances[Caselle][de] = Distance(RealDistance) 
        ZoneDistances[Caselle][de].appendZone(i)

    return

def main():

    if(os.path.isfile("creating.txt") == False):
        print("missing creating file")
        exit(0)

    city_config = open("creating.txt","r")
    city = city_config.readline().strip()
    city_config.close()
    gv.init()
    dc.assingVariables(city)
    

    #ZoneID_Zone = {}   
    ZoneDistances = {}
    ZoneNumCars = [0 for i in range(0, gv.NColumns * gv.NRows + 1)]


    DictPlates = pickle.load( open( "../input/"+ gv.city + "_" + gv.provider + "_plates_appeareance_obj.pkl", "rb" ) )
    for plate in DictPlates:
        CellIndex = sf.coordinates_to_index(DictPlates[plate].coordinates)
        ZoneNumCars[CellIndex]+=1

    k = 0   
    ZoneCars = {} 
    for i in range(0, gv.NColumns * gv.NRows + 1):
        ZoneDistances[i]={}
        
        CarVector = []
        for j in range(0,ZoneNumCars[i]):
            
            CarVector.append(Car(gv.provider, k))
            k+=1        
        ZoneCars[i] = CarVector
        
    pickle.dump( ZoneCars, open( "../input/"+ gv.city + "_" + gv.provider +"_ZoneCars.p", "wb" ) )

    print("CPZD, ", "Col:", gv.NColumns, "Row,", gv.NRows)

    for i in range(0, gv.NColumns * gv.NRows + 1):
        for j in range(i, gv.NColumns * gv.NRows):
            de, dh = EvalDistance(i, j)
            RealDistance = dh
            if de not in ZoneDistances[i]:
                ZoneDistances[i][de] = Distance(RealDistance) 
            ZoneDistances[i][de].appendZone(j)
            if(i!=j):
                if(de not in ZoneDistances[j]):
                    ZoneDistances[j][de] = Distance(RealDistance) 
                ZoneDistances[j][de].appendZone(i)
    
    for i in range(0,len(ZoneDistances)):
        
        ZoneDistances[i] = sorted(ZoneDistances[i].items(), key=operator.itemgetter(0))

    pickle.dump( ZoneDistances, open( "../input/"+ gv.city + "_" + gv.provider + "_ZoneDistances.p", "wb" ) )
    
    print("CPZD, End")
    return

main()
