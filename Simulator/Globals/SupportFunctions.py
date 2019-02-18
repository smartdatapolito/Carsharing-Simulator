'''
Created on 13/nov/2017

@author: dgiordan
'''

from math import *
import sys
import os
p = os.path.abspath('..')
sys.path.append(p+"/")

import pandas as pd
import numpy as np
import random
import csv
import subprocess

from pathlib import Path

import Simulator.Globals.GlobalVar as GlobalVar
import Simulator.Classes.Distance


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6367 * c

    return int(km*1000)

###############################################################################

def numberOfZones(city):
    c2id={"Vancouver":510, "Torino":251, "Berlino":833, "Milano":549}
    if city in c2id.keys():
        return c2id[city]


    command = 'ssh -t d046373@polito.it@tlcdocker1.polito.it wc -l %s_sim3.0/input/%s_car2go_ValidZones.csv' % (city,city)
    zones = int(str(subprocess.check_output(command, shell=True)).split(" ")[0][2:5]) - 1

    return zones

###############################################################################

def createListConfig(BestEffort_list, AvaiableChargingStations_list, algorithm_list,
    numberOfStations_list, tankThresholds_list, pThresholds, kwh_list, gamma_list):

    settings_list = []

    for BestEffort in BestEffort_list:
        for AvaiableChargingStations in AvaiableChargingStations_list:
            for algorithm in algorithm_list:
                for numberOfStations in numberOfStations_list:
                    for tankThreshold in tankThresholds_list:
                        for pt in pThresholds:

                            if validSimulation(BestEffort, tankThreshold, pt) == False:
                                continue

                            for kwh in kwh_list:
                                for gamma in gamma_list:
                                    d = { 
                                    'BestEffort': BestEffort,
                                    'AvaiableChargingStations': AvaiableChargingStations,
                                    'Algorithm' : algorithm,
                                    'numberOfStations': numberOfStations,
                                    'tankThreshold': tankThreshold,
                                    'pt': pt,
                                    'kwh': kwh, 
                                    'gamma': gamma
                                    }
                                    settings_list.append(d)
    return settings_list


###############################################################################


def validSimulation(BestEffort, tankThreshold_valid, pThresholdCheck) :

    '''
    
    :param BestEffort: True -> car goes to park if ends trip in a CS
    :param tankThreshold_valid: percentage of battery below with a car can recharge
    :param pThresholdCheck: 0-> people charge only needed, 1 -> charge every time
    :return:
    '''
    
    #Station Based and IMP2
    if tankThreshold_valid == 100:
        return False

    #IMP1
    if BestEffort==False and tankThreshold_valid==-1 :
        return False

    #Needed only p=0
    if BestEffort == False \
    and tankThreshold_valid >= 0 \
    and tankThreshold_valid < 100 \
    and pThresholdCheck != 0 :
    #print(BestEffort, tankThreshold, p)
        return False

    ##free Floating only and p=100
    if BestEffort == True \
    and tankThreshold_valid == -1 \
    and pThresholdCheck != 1 :
    #print(BestEffort, tankThreshold, p)
        return False
    
    return True


###############################################################################


def coordinates_to_index(coords):

    lon = coords[0]
    lat = coords[1]

    ind = int((lat - GlobalVar.minLat) / GlobalVar.ShiftLat) * \
          GlobalVar.NColumns + \
          int((lon - GlobalVar.minLon) / GlobalVar.ShiftLon)
    if(ind<=GlobalVar.MaxIndex): return int(ind)

    return -1

###############################################################################


def checkPerimeter(lat,lon):

    if(lon > GlobalVar.minLon  and  lon < GlobalVar.MaxLon and lat > GlobalVar.minLat  and  lat< GlobalVar.MaxLat): return True

    return False

def checkCasellePerimeter(lon,lat):

    if(lon > GlobalVar.CaselleminLon
       and lon < GlobalVar.CaselleMaxLon
       and lat > GlobalVar.CaselleminLat
       and lat < GlobalVar.CaselleMaxLat):

        return True
    return False

def checkBerlinZone(lon,lat):
    zone_id = coordinates_to_index([lon, lat])
    if(zone_id in GlobalVar.BerlinCriticalZone):
        return True
    return False


def zoneIDtoCoordinates(ID):

    Xi = ID % GlobalVar.NColumns
    Yi = int(ID / GlobalVar.NColumns)


    CentalLoni = (Xi + 0.5) * GlobalVar.ShiftLon + GlobalVar.minLon
    CentalLati = (Yi + 0.5) * GlobalVar.ShiftLat + GlobalVar.minLat

    return [CentalLoni, CentalLati]

def MatrixCoordinatesToID(Xi,Yi):

    ID = Yi * GlobalVar.NColumns + Xi

    return ID

def zoneIDtoMatrixCoordinates(ID):

    Xi = ID % GlobalVar.NColumns
    Yi = int(ID / GlobalVar.NColumns)

    CentalLoni = (Xi + 0.5) * GlobalVar.ShiftLon + GlobalVar.minLon
    CentalLati = (Yi + 0.5) * GlobalVar.ShiftLat + GlobalVar.minLat

    return (ID, Xi, Yi, CentalLoni, CentalLati)


def ReloadZonesCars(ZoneCars, ZoneID_Zone, AvaiableChargingStations):

    for ZoneI_ID in ZoneCars:
        ZoneI = Zone(ZoneI_ID,AvaiableChargingStations)
        ZoneID_Zone[ZoneI_ID] = ZoneI
        ZoneI.setCars(ZoneCars[ZoneI.ID])

    return


def loadRecharing(method, numberOfStations, city):
    Stations = []
    csvfilePath = p+"/input/"+ city + "_" + GlobalVar.provider + "_" + method + "500.csv"
    if (method == "rnd"):

        zones = pd.read_csv(p+"/input/"+ city + "_"  + GlobalVar.provider + "_ValidZones.csv", sep=" ", header=0)
        zones_list = list(zones.index)
        Stations2 = random.sample(zones_list, numberOfStations)
        for i in range(0, len(Stations2)):
            Stations.append(Stations2[i])


    else :
        coords = []
        with open(csvfilePath, 'rt') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=',')
                next(csvreader) # jump header
                for row in csvreader:
                    coords.insert(0, float(row[2])) #lon
                    coords.insert(1, float(row[1])) #lat
                    index = int(row[0])
                    Stations.append(index)
                    if len(Stations) == numberOfStations:
                        break

    return Stations

def SetSimulationParameter(BestEffort,algorithm,PolesPerStation,numberOfStations,
             tankThreshold,walkingTreshold, pThreshold, kwh, gamma):

    policy = ""


    if(tankThreshold==100):
        policy = "StationBased"
    if(tankThreshold>-1 and tankThreshold<100):
        if(BestEffort == True):
            policy="Hybrid"
        else:
            policy="Needed"
    if(tankThreshold<1):
        policy="FreeFloating"


    FileID = GlobalVar.provider+"_"+\
             policy +"_"+\
             algorithm+"_"+\
             str(numberOfStations)+"_"+\
             str(PolesPerStation)+"_"+\
             str(tankThreshold) +"_"+\
             str(walkingTreshold) + "_" +\
             str(int(kwh)) + "_" +\
             str(int(pThreshold*100)) + "_" +\
             str(int(gamma*100))


    SimulationParameters = { "Provider": GlobalVar.provider, "Policy": policy,                          
                        "Algorithm": algorithm, "ChargingStations":numberOfStations,
                        "PolesPerStation":PolesPerStation, 
                        "TankThreshold":tankThreshold, "WalkingTreshold":  walkingTreshold,
                        "pThreshold": pThreshold, "kwh": kwh, 
                        "gamma": gamma, "FileID": FileID}
                        
                        
    return SimulationParameters


def FillDistancesFrom_Recharging_Zone_Ordered(DistancesFrom_Zone_Ordered, RechargingStation_Zones):


    Zone_DistanceFromChargingZones = {}
    for zoneI in DistancesFrom_Zone_Ordered:
        Zone_DistanceFromChargingZones[zoneI] = []
        for DistanceI in DistancesFrom_Zone_Ordered[zoneI]:
            RandomZones = DistanceI[1].getZones()
            DistanceValid=""
            for RandomZonesI in RandomZones:
                if(RandomZonesI in RechargingStation_Zones):
                    if(DistanceValid==""):
                        newZone = Simulator.Classes.Distance.Distance(DistanceI[1].getDistance())
                        DistanceValid = (DistanceI[0],newZone)

                    DistanceValid[1].appendZone(RandomZonesI)

            if(DistanceValid!=""):
                Zone_DistanceFromChargingZones[zoneI].append(DistanceValid)
    
    return Zone_DistanceFromChargingZones


def DumpStats(ReturnDict,ProcessID,Direction,OutputDir,FileID,lastS,NStart,NEnd,NRecharge,NDeath,MeterRerouteEnd,MeterRerouteStart):
    
    
    if ReturnDict == None:
        #should be optional
        os.system('scp %s bigdatadb:/data/03/Carsharing_data/output/Simulation_%d/%s'%(OutputDir+FileID+".txt",lastS,FileID+".txt"))
        os.system('cat %s | ssh bigdatadb hdfs dfs -put -f - Simulator/output/Simulation_%s/%s' %(OutputDir+FileID+".txt",lastS,FileID+".txt"))
        os.system('rm %s'%(OutputDir+FileID+".txt"))
        return

    if ReturnDict != None:

        PercRerouteEnd = len(MeterRerouteEnd)/NEnd*100
        PercRerouteStart = len(MeterRerouteStart)/NStart*100
        PercRecharge = NRecharge/NEnd*100
        PercDeath = NDeath/NEnd*100

        MedianMeterEnd = np.median(np.array(MeterRerouteEnd))
        MeanMeterEnd = np.mean(np.array(MeterRerouteEnd))

        MedianMeterStart = np.median(np.array(MeterRerouteStart))
        MeanMeterStart = np.mean(np.array(MeterRerouteStart))

        RetValues = {}
        RetValues["ProcessID"] = ProcessID
        RetValues["Direction"] = Direction
        RetValues["PercRerouteEnd"] = PercRerouteEnd
        RetValues["PercRerouteStart"] = PercRerouteStart
        RetValues["PercRecharge"] = PercRecharge
        RetValues["PercDeath"] = PercDeath
        RetValues["MedianMeterEnd"] = MedianMeterEnd
        RetValues["MeanMeterEnd"] = MeanMeterEnd
        RetValues["MedianMeterStart"] = MedianMeterStart
        RetValues["MeanMeterStart"] = MeanMeterStart
        RetValues["NEnd"] = NEnd
        RetValues["NStart"] = NStart
        RetValues['WeightedWalkedDistance'] = (MeanMeterEnd * PercRerouteEnd + ((PercRecharge - PercRerouteEnd) * 150))/100
        ReturnDict[ProcessID] = RetValues

    #do not use

    #current_folder = os.getcwd().split("/")
    #output_folder = ""
    #for i in range(0,len(current_folder)-1):
    #    output_folder += current_folder[i]+"/"
    #output_folder+="output/"

    #print('PID %d, time: %.3f'%(ProcessID, time.time()-time_init))
    #os.system('ssh bigdatadb hdfs dfs -put /data/03/Carsharing_data/output/Simulation_%d/%s Simulator/output/Simulation_%d/%s &' %(lastS,fname,lastS,fname))
    #os.system('ssh bigdatadb cat /data/03/Carsharing_data/output/Simulation_%d/%s | hdfs dfs -put -f - Simulator/output/Simulation_%s/%s &' %(lastS,fname,lastS,fname))

    
    return     
    
    
    
    return    


from Simulator.Classes.Zone import *
