import pymongo
import ssl
import time
import datetime
import os
import pandas as pd
p = os.path.abspath('..')
import Simulator.Globals.GlobalVar as GlobalVar

###############################################################################

def setup_mongodb(CollectionName):
    """"Setup mongodb session """


    if(os.isfile(p+"/Support/mongo_config.ini", "r")=="False"):
        print("MongoDB credential missing.\n")
        print("Please contact us to get credential to access the data.\n")
        exit(0)
    
    with open(p+"/Support/mongo_config.ini", "r") as f:
        content = f.readlines()
    config={}
    for x in content:
        if len(x) > 0:
            x = x.rstrip()
            line = x.split("=")
            if len(line[1]) > 0:
                config[line[0]] = line[1]
            else :
                print (line[0], "not present")
                exit(666)
    

    
    server = config['server']
    dbname = config['dbname']
    username = config['username']
    password = config['password']
    
    
    try:
        client = pymongo.MongoClient(server,
                                     27017,
                                     ssl=True,
                                     ssl_cert_reqs=ssl.CERT_NONE) 
        client.server_info()
        db = client[dbname] #Choose the DB to use
        db.authenticate(username, password)#, #authentication        
        Collection = db[CollectionName] 
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print(err)
    return Collection

###############################################################################


cities_timezone = {
                    "Amsterdam":        "Europe/Amsterdam", 
                    "Austin":           "America/Chicago", 
                    "Berlin":           "Europe/Berlin", 
                    "Calgary":          "US/Arizona",
                    "Columbus":         "America/New_York",
                    "Denver":           "America/Denver", 
                    "Firenze":          "Europe/Rome", 
                    "Frankfurt" :       "Europe/Berlin",
                    "Hamburg":          "Europe/Berlin",
                    "Madrid":           "Europe/Madrid",
                    "Milano":           "Europe/Rome", 
                    "Montreal":         "America/Montreal",
                    "Munchen":          "Europe/Berlin",
                    "New York City":    "America/New_York",
                    "Rheinland":        "Europe/Berlin",
                    "Roma":             "Europe/Rome", 
                    "Seattle":          "America/Los_Angeles",
                    "Stuttgart":        "Europe/Berlin",
                    "Torino":           "Europe/Rome", 
                    "Toronto":          "America/Montreal",
                    "Vancouver":        "America/Vancouver",
                    "Washington DC":    "America/New_York",
                    "Wien":             "Europe/Vienna"
                    }    

def CreateConfigFile():



    print("Avaiable cities "+str(cities_timezone.keys()))  
    default = "Torino"  
    city = str(input('Insert city Press ENTER for default ['+default+']: '))
    if(city!="" and city not in cities_timezone): 
        print("Invalid City")
        exit(0)
    if(city == ""): city = default    
    config = open(p+"/input/" + city + "_config.txt", "w") 
    config.write("city="+city+"\n")

    
    default = "car2go"
    provider = str(input('Insert Provider [car2go,enjoy] Press ENTER for default ['+default+']: '))
    if(provider==""): provider=default    
    config.write("provider=" + provider + "\n")

    default = "2017-09-05T00:00:00"
    initdate = str(input('Insert initial date in this format \"%Y-%m-%dT%H:%M:%S\" Press ENTER for default ['+default+']:'))
    if(initdate==""): initdate=default    
    config.write("initdate=" + initdate + "\n")

    default = "2017-11-02T00:00:00"
    finaldate = str(input('Insert final date in this format \"%Y-%m-%dT%H:%M:%S\" Press ENTER for default ['+default+']:'))
    if(finaldate==""): finaldate=default    
    config.write("finaldate=" + finaldate + "\n")

    default = 'mean'
    fleetSize = str(input('Insert fleetSize default ['+default+']:'))
    if(fleetSize==""): fleetSize=default    
    config.write("fleetSize=" + fleetSize + "\n")


    config.close()

    return  city


###############################################################################
def readConfigFile(city):
    

    with open(p+"/input/" + city + "_config.txt", "r") as f:
        content = f.readlines()

    d={}
    for x in content:
        if len(x) > 0:
            x = x.rstrip()
            line = x.split("=")
            if len(line[1]) > 0:
                d[line[0]] = line[1]
            else :
                print (line[0], "not present")
                exit(666)

    d["city"] = d["city"].lower().title()
    d["initdate"] = int(time.mktime(datetime.datetime.strptime(d["initdate"], "%Y-%m-%dT%H:%M:%S").timetuple()))
    d["finaldate"] = int(time.mktime(datetime.datetime.strptime(d["finaldate"], "%Y-%m-%dT%H:%M:%S").timetuple()))
    d["timezone"] = cities_timezone[city]
    pathCityAreas = p+"/input/car2go_oper_areas_limits.csv"
    if(os.path.isfile(pathCityAreas)):
        cityAreas = pd.read_csv(pathCityAreas, header=0)
        cityAreas = cityAreas.set_index("city")
        d["limits"] = cityAreas.loc[d["city"]]
        
    
    return d

def assingVariables(city):
    
    

    d = readConfigFile(city)

    # GlobalVar.MaxLat = d["limits"]["maxLat"]
    # GlobalVar.MaxLon = d["limits"]["maxLon"]
    # GlobalVar.minLat = d["limits"]["minLat"]
    # GlobalVar.minLon = d["limits"]["minLon"]
    GlobalVar.city = d["city"]
    GlobalVar.provider = d["provider"]
    GlobalVar.initDate = int(d["initdate"])
    GlobalVar.finalDate = int(d["finaldate"])
    GlobalVar.fleetSize = d["fleetSize"]


    GlobalVar.CaselleCentralLat = 45.18843
    GlobalVar.CaselleCentralLon = 7.6435

    GlobalVar.CorrectiveFactor = 1.4  # .88

    # GlobalVar.shiftLat500m = 0.0045
    # GlobalVar.shiftLon500m = 0.00637
    
    #add /2 in order to have a zonization 250x250
    

    if "limits" in d.keys():
        GlobalVar.MaxLat = d["limits"]["maxLat"]
        GlobalVar.MaxLon = d["limits"]["maxLon"]
        GlobalVar.minLat = d["limits"]["minLat"]
        GlobalVar.minLon = d["limits"]["minLon"]
        GlobalVar.NColumns = int((GlobalVar.MaxLon - GlobalVar.minLon) / GlobalVar.shiftLon500m)
        GlobalVar.NRows = int((GlobalVar.MaxLat - GlobalVar.minLat) / GlobalVar.shiftLat500m)
        GlobalVar.MaxIndex = GlobalVar.NRows * GlobalVar.NColumns - 1

        GlobalVar.ShiftLon = (GlobalVar.MaxLon - GlobalVar.minLon) / GlobalVar.NColumns
        GlobalVar.ShiftLat = (GlobalVar.MaxLat - GlobalVar.minLat) / GlobalVar.NRows


    return
