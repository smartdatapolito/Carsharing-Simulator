import sys
import os
import random

p = os.path.abspath('..')
sys.path.append(p+"/")
from Support.DataCreation import assingVariables
import Simulator.Globals.SupportFunctions as sf
import Simulator.Globals.GlobalVar as GV


def WriteOutHeader(fout, parametersDict):
    
    HeaderOreder = ["Provider", "Policy", "Algorithm", "ChargingStations", 
     "PolesPerStation", "TankThreshold", "WalkingTreshold",
     "pThreshold", "kwh", "gamma"]
    
    for key in HeaderOreder:
        fout.write(key + ":" + str(parametersDict[key])+"\n")

    fout.write("####"+"\n")
    fout.write("Type;ToRecharge;Recharged;ID;Lvl;Distance;Iter;Recharge;StartRecharge;StartRechageLVL;Stamp;EventCoords;ZoneC;Discharge;TripDistance;FileID;extractedP;ZoneID;OccupiedCS;PoleID\n")

    return

#Prepare the string for the Simulation log
def toStringBooking(Stamp,Event,ToRecharge,Recharged,NearestCar,Distance,Iter,\
                     Discharge,TripDistance,FileID,extractedP,ZoneID,OccupiedCS,
                     Recharge, StartRecharge,StartRechageLVL, PoleID):
    
    
    
    Lvl = NearestCar.getBatteryLvl()
    ID = NearestCar.getID()
    ZoneC = sf.zoneIDtoCoordinates(ZoneID)
    EventCoords = Event.coordinates
    
    outputString  = Event.type+";"
    outputString += str(ToRecharge)+";"
    outputString += str(Recharged)+";"
    outputString += "%d;"% ID
    outputString += "%.2f;"% Lvl
    outputString += "%d;"% Distance
    outputString += "%d;"% Iter
    outputString += "%.2f;"%Recharge
    outputString += "%d;"%StartRecharge
    outputString += "%.2f;"%StartRechageLVL
    outputString += "%d;"% Stamp
    outputString += "[%.6f,%.6f];"%(EventCoords[0],EventCoords[1])
    outputString += "[%.6f,%.6f];"%(ZoneC[0],ZoneC[1])
    if(Discharge == "nan"):
        outputString += "nan;" 
        outputString += "nan;"
    else:
        outputString += "%.2f;"%Discharge 
        outputString += "%.2f;"%TripDistance 
    outputString += "%s;"%FileID
    if(extractedP == "nan"):
        outputString += "nan;"
    else:
        outputString += "%.2f;"%extractedP
    outputString += "%d;"% ZoneID
    outputString += "%d;"% OccupiedCS
    outputString += "%d\n"% PoleID    
        
    return outputString


def SearchAvailableCar(ZoneI,Stamp):

    if(ZoneI.getNumCars()>0):
        return ZoneI.getBestGlobalCars(Stamp)        
    return ""

'''
SearchNearestBestCar search the best car in term of battery
'''
def SearchNearestBestCar(Zone_DistanceFromZones,ZoneID_Zone, Event, Stamp):
       
    SelectedCar = ""
    Distance = -1
    Iter = 0
    
    BookingStartingPosition = sf.coordinates_to_index(Event.coordinates)
    for DistanceI in Zone_DistanceFromZones[BookingStartingPosition]:        
        Iter +=1
        RandomZones = DistanceI[1].getRandomZones()
        for ZoneI_ID in RandomZones:        
            ZoneI = ZoneID_Zone[ZoneI_ID]                    
            SelectedCar = SearchAvailableCar(ZoneI,Stamp)
            if(SelectedCar != ""):
                Distance = DistanceI[1].getDistance()
                return SelectedCar, Distance, ZoneI.ID, Iter
    
    print("Error NO cars avaiable")
    exit(0)
    return -1, -1


'''
ParkCar parks the car accoding to the defined policy:
- ChargingStationsZones (Vector): Vector with the zone IDs having a charging station 
- Zone_DistanceFromZones (Dictionary): Matrix definining from each zone the distance to other zones ordered by distance
- ZoneID_Zone (Dictionary): DIctionary with zone ID and the zone object
- Event: The end event with the information where the booking was suppose to end
- BookedCar: The car used for the booking
- TankThreshold (Integer): The minimum Threshold (in % of total battery) after which the car has to be plugged
  < 0: Pure FF
- WalkingTreshold (Integer): The maximum distance (in meters) an user is willing to walk  
- BestEffort (Boolean): [True,False] 
    True: FF approach - when the trip ends in a zone with charging station the customer plug the car
    False: the customer do not have to plug the car if the trip ends in a zone with charging station
- pThreshold (float): Threshold to define the willingness of the user to plug the car
'''
def ParkCar(ChargingStationsZones,Zone_DistanceFromZones,ZoneID_Zone, Event, BookedCar, \
            TankThreshold, WalkingTreshold, BestEffort, pThreshold):
    
    ToRecharge = False
    Recharged = False
    Distance =-1   
    Iter = 0
    p = random.SystemRandom().random()

    BookingEndPosition = sf.coordinates_to_index(Event.coordinates)
    Lvl = BookedCar.getBatteryLvl()


    #BestEffort is True if the policy is FreeFloating or Hybrid  -> parkings only in CS when hitted
    #In case plug the car only if the user is willing to plug [based on p extracted and pThreshold]
    #pThreshold == 0 -> park only Needed
    #pThreshold == 100 -> hybrid
    if(BestEffort and BookingEndPosition in ChargingStationsZones and pThreshold >= p):
        ZoneI = ZoneID_Zone[BookingEndPosition]        
        Recharged = ZoneI.getParkingAtRechargingStations(BookedCar)
        if(Recharged): 
            return ToRecharge, Recharged, Distance, ZoneI.ID, 1, p
            
        
    #If battery lvl below the TankThreshold look for a car in a charging station
    if(Lvl < TankThreshold):
        Iter=0
        ToRecharge = True
        for DistanceI in  Zone_DistanceFromChargingZones[BookingEndPosition]:
            Iter +=1    
            Distance = DistanceI[1].getDistance()
            if(Distance > WalkingTreshold): break    
            #Since the final destination of the user is unkown, and to avoid selecting allways the same zone 
            #Get zones at the same distance in a random order        
            RandomZones = DistanceI[1].getRandomZones()
        

            for ZoneI_ID in RandomZones:     
                ZoneI = ZoneID_Zone[ZoneI_ID]
                if(ZoneI.ID in ChargingStationsZones):    
                    Recharged = ZoneI.getParkingAtRechargingStations(BookedCar)
                    if(Recharged): 
                        return ToRecharge, Recharged, Distance, ZoneI.ID, Iter, p         



    #Park at any parking in the end booking zone 
    #End here if the car did not need to be charged
    #No plug is available
    for DistanceI in Zone_DistanceFromZones[BookingEndPosition]:        
        RandomZones = DistanceI[1].getZones()
        for ZoneI_ID in RandomZones:       
            ZoneI = ZoneID_Zone[ZoneI_ID]             
            ZoneI.getAnyParking(BookedCar)
            return ToRecharge, Recharged, 0, ZoneI.ID, 1, p


'''
RunSim run a single simulation with the following parameters:
- BestEffort (Boolean): [True,False] 
    True: FF approach - when the trip ends in a zone with charging station the customer plug the car
    False: the customer do not have to plug the car if the trip ends in a zone with charging station
- Algorithm (String): The algorithm used to place the charging stations
- PolesPerStation: Number of poles per charing station
- TankThreshold (Integer): The minimum Threshold (in % of total battery) after which the car has to be plugged
  < 0: Pure FF
- WalkingTreshold (Integer): The maximum distance (in meters) an user is willing to walk  
- Zone_Cars (Dictionary): Dictionary where cars are located at the beginning 
- ChargingStationsZones (Vector): Vector with the zone IDs having a charging station 
- Stamps_Events (Dictionary): Dictionary of Stamps, and Vector of event in that moment
- Zone_DistanceFromZones (Dictionary): Matrix definining from each zone the distance to other zones ordered by distance
- Zone ID
- Vector of Distances [Class]
- Inside of each Distance Object a list of all Zones at that distance
- lastS (Integer): Simulation ID
- pThreshold (float): Threshold to define the willingness of the user to plug the car
- Kwh (float): Energy delivered by a pole 
- Gamma (float): Extra consumption
- randomStrtingLevel (Boolean): [True,False] 
    True: The cars battery is initialized with a random level
    False: All cars start at 100%
- ReturnDict (Dictionary): used to return statistics to the main thread
 - none: stats are not computed and returned
 - dictionary: the dictionar where data is stored
- ProcessID: ID of the process
- Direction: # a cosa serve?
- City: City of interest):
'''
Zone_DistanceFromChargingZones = {} 
def RunSim(
    BestEffort,
    Algorithm,
    PolesPerStation,
    TankThreshold,
    WalkingTreshold,
    Zone_Cars,
    ChargingStationsZones,
    Stamps_Events,
    Zone_DistanceFromZones,
    lastS,
    pThreshold,
    Kwh,
    Gamma,
    randomStrtingLevel,
    ReturnDict,
    ProcessID,
    Direction, # a cosa serve?
    City):


    ZoneID_Zone = {}    
    global Zone_DistanceFromChargingZones
    NumberOfStations = len(ChargingStationsZones)


    '''
    Prepare all the information related to the simulation
    '''
    GV.init()
    assingVariables(City)
    

    #Reload Zones grid with cars in the predefined starting position
    sf.ReloadZonesCars(Zone_Cars, ZoneID_Zone, PolesPerStation)

    #Load a support Matrix with distance from ANY zone to the CHARGING zones only 
    #Used to speedup the research of an avaiable charging station
    Zone_DistanceFromChargingZones = sf.FillDistancesFrom_Recharging_Zone_Ordered(Zone_DistanceFromZones, ChargingStationsZones)
    
    #Prepare the dictionary with all the simulation parameter
    SimulationParameters = sf.SetSimulationParameter(BestEffort,Algorithm,PolesPerStation,NumberOfStations,TankThreshold,
                                     WalkingTreshold, pThreshold, Kwh, Gamma)


    #Prepare the folder containing the results
    FileID = SimulationParameters["FileID"]
    OutputDir = "../output/Simulation_"+str(lastS)+"/"
    if not os.path.exists(OutputDir):
        os.makedirs(OutputDir)
    fout = open(OutputDir+FileID+".csv","w")
    WriteOutHeader(fout, SimulationParameters)

    '''Q: A COSA SERVONO QUESTI 2 LOOP E PERCHÈ SEPARATI? Li usiamo?'''
    cars = 0
    for z in Zone_Cars.keys():
        if len(Zone_Cars[z]) > 0:
            for i in range (len(Zone_Cars[z])):
                Zone_Cars[z][i].setRechKwh(Kwh)
                Zone_Cars[z][i].setGamma(Gamma)
                cars+=1

    #Initialized the car with a random battery level
    if randomStrtingLevel == True :
        for zone in Zone_Cars:
            if len(Zone_Cars[zone]) > 0 :
                for car in Zone_Cars[zone]:
                    car.BatteryCurrentCapacity = round(random.SystemRandom().random(),2) * car.BatteryMaxCapacity
    ''''''
    
    OccupiedCS = 0
    NRecharge = 0
    NStart = 0
    NEnd = 0
    NDeath = 0
    ActualBooking = 0

    MeterRerouteStart = []
    MeterRerouteEnd = []
    BookingID_Car = {}
    
    
    for Stamp in Stamps_Events:
        for Event in Stamps_Events[Stamp]:
            #Start event specify a new booking starting
            if(Event.type == "s"):
                
                NStart +=1
                ActualBooking +=1
                
                #Look for the best car near the customer
                #Best car in term of battery either pluged or not
                NearestCar, Distance, ZoneID, Iter = SearchNearestBestCar(Zone_DistanceFromZones,ZoneID_Zone, Event, Stamp)
                BookingID_Car[Event.id_booking] = NearestCar

                if NearestCar.WasInCharge == True: 
                    OccupiedCS -= 1
                    
                Recharge, StartRecharge,StartRechageLVL, PoleID = NearestCar.setStartParameters(Stamp,Event,Gamma)
                OutString = toStringBooking(Stamp,Event,"nan","nan",NearestCar,Distance,Iter, "nan","nan",FileID,"nan",ZoneID,OccupiedCS,
                                            Recharge, StartRecharge,StartRechageLVL, PoleID)
                fout.write(OutString)

                if(Distance > 0): MeterRerouteStart.append(Distance)
                
            if(Event.type == "e"):

                ActualBooking -=1
                NEnd+=1

                BookedCar = BookingID_Car[Event.id_booking]

                Discharge, TripDistance = BookedCar.setEndParameters(Stamp,Event)

                #Park the car according to the defined policy 
                ToRecharge, Recharged, Distance, ZoneID, Iter, extractedP = ParkCar(ChargingStationsZones,Zone_DistanceFromZones,ZoneID_Zone,\
                                                                       Event, BookedCar, TankThreshold, WalkingTreshold, BestEffort,pThreshold)

                if Recharged == True: OccupiedCS += 1
                
                OutString = toStringBooking(Stamp,Event,ToRecharge,Recharged,BookedCar,Distance,Iter,\
                    Discharge,TripDistance,FileID,extractedP,ZoneID,OccupiedCS,-1, -1,-1, -1)
                fout.write(OutString)

                if(Distance > 0): MeterRerouteEnd.append(Distance)
                if(Recharged == True): NRecharge +=1
                if(BookedCar.getBatteryCurrentCapacity()<0): NDeath +=1

                del BookingID_Car[Event.id_booking]

    fout.close()
    exit(0)
    #Compute statistics if ReturnDict was given
    sf.DumpStats(ReturnDict,ProcessID,Direction,OutputDir,FileID,lastS,NStart,NEnd,NRecharge,NDeath,MeterRerouteEnd,MeterRerouteStart)

    return
