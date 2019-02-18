'''
Created on 13/nov/2017

@author: dgiordan
'''
import sys
import os
p = os.path.abspath('..')
sys.path.append(p+"/")
from Simulator.Classes.Car import *

class Zone(object):
      
    def __init__(self, ID, PolesPerStation):
        
        self.PolesPerStation = PolesPerStation
        self.ID = ID
        self.Cars = []
        self.Poles = {i:"" for i in range(0,PolesPerStation)}
        self.numCars = 0       
        self.numOccupiedPoles = 0
        return


    '''
    Get the best avaiable car in the zone
    If the zone is a charging station zone check the car with the highest battery
    '''
    def getBestGlobalCars(self,Stamp):
       
        BestCar = ""
        BestLvl = -1

        InRecharge = False
        PoleID = -1

        if(self.numOccupiedPoles>0):
            for Polei in self.Poles:
                if(self.Poles[Polei]!=""):
                    CarI = self.Poles[Polei]
                    if(BestCar == ""):
                        BestCar = CarI    
                        InRecharge = True
                        PoleID = Polei
                    else:
                        CarILvl = CarI.getBatteryLvl(Stamp)
                        if(CarILvl > BestLvl): 
                            BestCar = CarI
                            BestLvl = CarILvl
                            InRecharge = True
                            PoleID = Polei

        for CarI in self.Cars:
            if(BestCar == ""):
                BestCar = CarI  
                InRecharge = False  
            else:
                CarILvl = CarI.getBatteryLvl()
                if(CarILvl > BestLvl): 
                    BestCar = CarI
                    BestLvl = CarILvl
                    InRecharge = False
                    
        if(BestCar != ""): 
            self.numCars-=1
            if(InRecharge): 
                self.Poles[PoleID]=""
                self.numOccupiedPoles-=1
            else: 
                del self.Cars[self.Cars.index(BestCar)]

        return BestCar

   
    def getAnyParking(self,CarToPark):
        self.numCars+=1
        self.Cars.append(CarToPark)
        
        return
    
    def getParkingAtRechargingStations(self,CarToPark):
        
        if(self.numOccupiedPoles < self.PolesPerStation):
            self.numCars+=1
            self.numOccupiedPoles+=1
            for Polei in self.Poles:
                if(self.Poles[Polei]==""):
                    self.Poles[Polei]= CarToPark
                    CarToPark.setPoleID(Polei)
                    return True
        
        return False

        
    def getNumCars(self):
        
        return self.numCars

    def setCars(self,cars):

        self.RechargedCars = []        
        
        CarVector = []
        for CarI in cars:
            CarVector.append(Car(gv.provider, CarI.ID))
        
        self.Cars = CarVector

        self.numCars = len(self.Cars)
        
        return

    def setAvaiableChargingStations(self, n):
        
        self.AvaiableChargingStations = n
        return

    def getAvaiableChargingStations(self):
        
        return self.AvaiableChargingStations