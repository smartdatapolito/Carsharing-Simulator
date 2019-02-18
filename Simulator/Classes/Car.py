'''
Created on 13/nov/2017

@author: dgiordan
'''

from Simulator.Globals.SupportFunctions import haversine, checkCasellePerimeter, checkBerlinZone
import Simulator.Globals.GlobalVar as gv



class Car(object):
    
    def __init__(self, provider, ID):
        
        self.ID = ID
        
        self.BatteryMaxCapacity = 25.2
        self.kwh_km = 0.188
        if provider == 'car2go':
            self.BatteryMaxCapacity = 17.6
            self.kwh_km = 0.13

        self.BatteryCurrentCapacity = self.BatteryMaxCapacity 
        
        self.NumRentals = 0
        self.StartBookingPosition = 0
        
        self.WasInCharge = False
        self.PoleID = -1
        self.EndBooking = 0 #Timestamp
        
        self.kwh = 2

        self.reduction_factor_kwh = 0.1 #'''SERVE?'''
        self.gamma = 0
        
        return

    '''
    Return the battery level 
    Stamp: Timestamp of the event
    If stamp is passed and the car is under charge the update battery level is returned
    '''
    def getBatteryLvl(self, Stamp = False):
                    
        #WAS IN CHARGE
        if Stamp != False and self.WasInCharge:
            EnergyDelivered, BatteryCurrentCapacity = self.EvaluateChargingCapacity(Stamp)            
    
            return BatteryCurrentCapacity/self.BatteryMaxCapacity*100

    
        return self.BatteryCurrentCapacity/self.BatteryMaxCapacity*100

    '''
    If under recharge evaluate current Capacity
    '''
    def EvaluateChargingCapacity(self, CurrentStamp):
    
        kw = self.kwh
    
        ChargingDuration = (CurrentStamp-self.EndBooking)/(60.0*60.0) #in hour
        DeliveredEnergy = ChargingDuration * kw 
    
        if (self.BatteryCurrentCapacity + DeliveredEnergy <= self.BatteryMaxCapacity):
            return DeliveredEnergy, self.BatteryCurrentCapacity + DeliveredEnergy
    
        '''
        serve questo codice commentato? [sotto]
        '''
        # '''recharge linear to 0-70 %, unlinear from 70 to 100'''
        # max_supply_h = self.BatteryMaxCapacity/self.kwh
        # if duration > max_supply_h
        #     a =  self.cut_hout_perc * max_supply_h * self.kwh
        #     b = (duration/max_supply_h - self.cut_hout_perc * max_supply_h/max_supply_h)  *  (self.reduction_factor_kwh * self.kwh)
        #     delta_c = a + b
        # else
        #     delta_c = duration * kw
    
        #str_out = str(self.BatteryCurrentCapacity)+ "_"+str(duration)+"_"+str(delta_c)+"_"+str(self.BatteryMaxCapacity)
        RealDeliveredEnergy = self.BatteryMaxCapacity-self.BatteryCurrentCapacity
        return RealDeliveredEnergy, self.BatteryMaxCapacity
    

    def getID(self):
        
        return self.ID

    def getBatteryCurrentCapacity(self):
        
        return self.BatteryCurrentCapacity

    def getGamma(self): 
        
        return self.gamma

    def setGamma(self, gamma_par): 
        
        self.gamma = gamma_par 
        
        return
    
    def getRechKwh(self): 
        
        return self.kwh 

    def setRechKwh(self, kwh): 
        
        self.kwh = kwh 
        
        return

    def setPoleID(self,PoleID):

        self.WasInCharge = True
        self.PoleID = PoleID

        return
    
    def setStartPosition(self, BookingStarting_Position):
        
        self.StartBookingPosition = BookingStarting_Position
    
        return

    def setEndBooking(self, EndBooking):
        
        self.EndBooking = EndBooking
        
        return
    
    '''
    Set all parameters related to the start event
    If the car was in recharge update the battery Level before unplug it
    '''
    def setStartParameters(self,Stamp,Event,gamma):
        
        Recharge = -1
        StartRecharge = -1
        StartRechageLVL = -1
        PoleID = -1
        self.setStartPosition(Event.coordinates)
        self.setGamma(gamma)
        
        if(self.WasInCharge):
            Recharge, StartRecharge,StartRechageLVL, PoleID = self.Charge(Stamp)
    
        return  Recharge, StartRecharge,StartRechageLVL, PoleID
    
    def setEndParameters(self,Stamp,Event):
        
        self.setEndBooking(Stamp)
        
        return self.Discharge(Event.coordinates)
        
    
    '''
    Charge the battery up to when the car is taken
    If the battery arrives at 100% saturate the capacity at 100%
    '''
    def Charge(self, EndRecharge):
        
        StartRechargeLvl = self.getBatteryLvl()
        StartRecharge = self.EndBooking
        PoleID = self.PoleID
    
        DeliveredEnergy, self.BatteryCurrentCapacity = self.EvaluateChargingCapacity(EndRecharge)
    
        self.WasInCharge = False
        self.EndBooking = -1
        self.PoleID = -1
        
        return DeliveredEnergy, StartRecharge,StartRechargeLvl, PoleID         
    

    '''
    Discharge the battery at the end of a booking
    If the battery arrives at 0kw set to -0.001
    '''
    def Discharge(self, BookingEndPosition):
        
        Origin = self.StartBookingPosition
        Destination = BookingEndPosition
        Distance = haversine(Origin[0],Origin[1],Destination[0],Destination[1])
        
        if(checkCasellePerimeter(Origin[0],Origin[1]) or checkCasellePerimeter(Destination[0],Destination[1])):
            Distance *=1 #For trips FROM or TO Caselle I do not use the corrective factor
        elif (checkBerlinZone(Origin[0],Origin[1])):
            Distance *=1
        else: 
            Distance *= gv.CorrectiveFactor 
        
        DistanceKm = Distance/1000
        EnergyConsumption = DistanceKm * self.kwh_km * (1+self.gamma)
    
        self.BatteryCurrentCapacity = self.BatteryCurrentCapacity - EnergyConsumption
        if self.BatteryCurrentCapacity <=0 :
            self.BatteryCurrentCapacity = -0.001
    
        return EnergyConsumption, Distance
