import numpy as np
import sys
import os
p = os.path.abspath('..')
sys.path.append(p+"/")

'''
Created on 13/nov/2017

@author: dgiordan
'''

class Distance(object):
    
    def __init__(self, Distance):
      
        self.Zones = []
        self.Distance = Distance
      
        return  
    
    def getZones(self):
        
        return self.Zones

    def getRandomZones(self):

        np.random.shuffle(self.Zones)
        
        return self.Zones

    def getDistance(self):
    
        return self.Distance


    def appendZone(self,z):
        
        self.Zones.append(z)
        
        return

    def setZone(self, Zones):
        
        self.Zones = Zones

        return
    
    def setDistance(self, Distance):
        
        self.Distance = Distance
        
        return