import sys
import os
p = os.path.abspath('..')
sys.path.append(p+"/")
import Support.DataCreation as dc
import Simulator.Globals.GlobalVar as gv
import Simulator.Globals.SupportFunctions as sf
import pandas as pd
import pytz
from datetime import datetime
import time


def AbroadStamptoLocal(timezone,stamp):

    tz = pytz.timezone(timezone)
    dt = datetime.fromtimestamp(stamp, tz=tz)
    our_zone = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute,dt.second)
    our_stamp =  int(time.mktime(our_zone.timetuple()))

    return our_stamp

def formatBookings(d):
    
    bookings_df = ""
    
    if(os.path.isfile('../input/bookings_' + d["city"]) == False):
        collection="enjoy_PermanentBookings"
        if(d["provider"] == "car2go"):
            collection = "PermanentBookings"
        enjoy_bookings = dc.setup_mongodb(collection)
    
        
        print("***********************")
        print("city", d["city"])
        print("initdate ",datetime.fromtimestamp(int(d["initdate"])).strftime('%Y-%m-%d %H:%M:%S'))
        print("fianldate",datetime.fromtimestamp(int(d["finaldate"])).strftime('%Y-%m-%d %H:%M:%S'))
        print("***********************")
    
        bookings = enjoy_bookings.find({"city": d["city"],
                                        "init_time": {"$gt": d["initdate"],
                                                      "$lt": d["finaldate"]}
                                        })
    
        bookings_df = pd.DataFrame(list(bookings))
    
        if("Europe" not in d["timezone"]):
            #convert from their time zone in our time zone
            bookings_df['init_time'] = list(map(AbroadStamptoLocal, bookings_df["timezone"],bookings_df['init_time']))
            bookings_df['final_time'] = list(map(AbroadStamptoLocal, bookings_df["timezone"],bookings_df['final_time']))
    
    
        bookings_df.to_pickle('../input/bookings_' + d["city"])

    else:
        print("read")
        bookings_df = pd.read_pickle('../input/bookings_' + d["city"])
    
    bookings_df["duration"] = bookings_df["final_time"] - bookings_df["init_time"]
    bookings_df["duration"] = bookings_df["duration"].astype(int)
    bookings_df = bookings_df.drop('driving',1)

    bookings_df['type'] = bookings_df.origin_destination.apply(lambda x : x['type'])
    bookings_df['coordinates'] = bookings_df.origin_destination.apply(lambda x : x['coordinates'])
    bookings_df = bookings_df.drop('origin_destination',1)

    bookings_df['end'] = bookings_df.coordinates.apply(lambda x : x[0])
    bookings_df['start'] = bookings_df.coordinates.apply(lambda x : x[1])
    bookings_df = bookings_df.drop('coordinates',1)

    bookings_df['start_lon'] = bookings_df.start.apply(lambda x : float(x[0]) )
    bookings_df['start_lat'] = bookings_df.start.apply(lambda x : float(x[1]) )
    bookings_df = bookings_df.drop('start',1)

    bookings_df['end_lon'] = bookings_df.end.apply(lambda x : float(x[0]) )
    bookings_df['end_lat'] = bookings_df.end.apply(lambda x : float(x[1]) )
    bookings_df = bookings_df.drop('end', 1)

    bookings_df['distance'] = bookings_df.apply(lambda x : sf.haversine(
            float(x['start_lon']),float(x['start_lat']),
            float(x['end_lon']), float(x['end_lat'])), axis=1)

    bookings_df = bookings_df[bookings_df["distance"] >= 700]
    bookings_df = bookings_df[bookings_df["duration"] >= 120]
    bookings_df = bookings_df[bookings_df["duration"] <= 3600]

    if d["city"] == "Torino":
        bookings_df = bookings_df[ bookings_df["start_lon"] <= 7.8]


    return bookings_df


def createParkingsFromBookings(df):

    parkings = pd.DataFrame()

    def coord2id (lon, lat):
              
        ind = int((lat - gv.minLat) / gv.ShiftLat) * \
              gv.NColumns + \
              int((lon - gv.minLon) / gv.ShiftLon)
        if(ind<=gv.MaxIndex):

            return int(ind)


        return -1


    i = 0
    for plate in df.plate.unique():
        res = pd.DataFrame()
        tmp = df[df["plate"] == plate].reset_index()
        tmp["zone"] = tmp.apply(lambda x: coord2id(x["end_lon"], x["end_lat"]), axis=1)
        tmp.init_time = tmp.init_time.shift(-1)
        tmp = tmp.dropna()
        if len(tmp) == 1 : continue
        i=i+1

        res["duration"] = tmp["final_time"].astype(int) - tmp["init_time"].astype(int)
        res["init_time"] = tmp["init_time"].astype(int)
        res["final_time"] = tmp["final_time"].astype(int)
        res["plate"] = tmp["plate"]
        res["lat"] = tmp["end_lat"]
        res["lon"] = tmp["end_lon"]
        res["zone"] = tmp["zone"]

        if res.isnull().any().any() : print (i, plate)

        parkings = parkings.append(res, ignore_index=True)


    return parkings

def printCSV(parkings,d):
    def wrapperIDtoCoords(zoneID, coord):
        out = sf.zoneIDtoCoordinates(zoneID)

        if coord == "lon":
            return out[0]
        else :
            return out[1]

    parkings["plate"] = parkings["plate"].astype(str)
    parkings["duration"] = parkings["duration"].astype(int)
    parkings["duration"] = parkings["duration"].div(60)

        
    q = parkings.groupby("zone").count()["duration"]
    parkings_stats =  pd.DataFrame(q)
    parkings_stats = parkings_stats.rename(columns={'duration':"NParkings"})
    parkings_stats["SumTime"] = parkings.groupby("zone").sum()["duration"]
    parkings_stats["AvgTime"] = parkings_stats["SumTime"]/ parkings_stats["NParkings"]

    parkings_stats = parkings_stats.reset_index()
    parkings_stats["Lon"] = parkings_stats.apply(lambda row : wrapperIDtoCoords(row.zone, "lon"), axis=1)
    parkings_stats["Lat"] = parkings_stats.apply(lambda row : wrapperIDtoCoords(row.zone, "lat"), axis=1)

    parkings_stats = parkings_stats.set_index("zone")
    parkings_stats.to_csv("../input/"+ d["city"] + "_" + d["provider"] + "_ValidZones.csv", index_label="id")

    parkings_stats[["Lon", "Lat", "NParkings"]].sort_values(by="NParkings", ascending=False)\
    .to_csv("../input/"+ d["city"]+ "_" + d["provider"] + "_max-parking500.csv", index_label="id")

    parkings_stats[["Lon", "Lat", "SumTime"]].sort_values("SumTime", ascending=False)\
    .to_csv("../input/"+ d["city"] + "_" + d["provider"] + "_max-time500.csv", index_label="id")

    parkings_stats[["Lon", "Lat", "AvgTime"]].sort_values("AvgTime", ascending=False)\
    .to_csv("../input/"+ d["city"] + "_" + d["provider"] + "_avg-time500.csv", index_label="id")

    return

def main():
    
    
    if(os.path.isfile("creating.txt") == False):
        print("missing creating file")
        exit(0)
    city_config = open("creating.txt","r")
    city = city_config.readline().strip()
    city_config.close()
    
    d = dc.readConfigFile(city)
    gv.init()
    dc.assingVariables(city)
    
    bookings_df = formatBookings(d)
    print("CVZ, all data queried")
    parkings_df = createParkingsFromBookings(bookings_df)
    print("CVZ, all parkings are created")
    printCSV(parkings_df,d)
    print("CVZ, input files generated")
    

main()