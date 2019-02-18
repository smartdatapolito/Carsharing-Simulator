import sys
import os
p = os.path.abspath('..')
sys.path.append(p+"/")
import Support.DataCreation as dc

city = dc.CreateConfigFile()

fout = open("creating.txt","w")
fout.write(city)
fout.close()
