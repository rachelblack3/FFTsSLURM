import sys
import glob
import os
from datetime import datetime

# the only thing that the python script needs is the day
def date_strings(date_string):

    date = datetime.strptime(date_string, "%Y%m%d")

    if (date.day <10):
        day = "0"+str(date.day)
    else:
        day = str(date.day)


    if (date.month<10):
        month = "0"+str(date.month)
    else:
        month = str(date.month)
    

    year = str(date.year)

    return day,month,year


date = sys.argv[1]
day,month,year = date_strings(date)

files = glob.glob('/data/hpcdata/users/rablack75/first_attempt/data/'+day+'/*')

print(date, "in output")

outpath = 'output/' + day
os.makedirs(outpath, exist_ok=True)

f = open(outpath+"/attempt1.txt","w+")

for file in files:
    f.write(file + "in seperate file")
    
f.close()
