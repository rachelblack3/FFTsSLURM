#!/bin/bash

startdate="20130101"
enddate="20130201"

currdate=$startdate

## Loop from the start to the end
while [[ "$currdate" < "$enddate" ]]; do

    ## Get the year and the month from the current date
    year=$(date -d "$currdate" +%Y)
    month=$(date -d "$currdate" +%m)
    day=$(date -d "$currdate" +%d)

    ## Copy all of the day folders to the HPCDATA filesystem

    ## copy burst files
    scp -r /data/spacecast/wave_database_v2/RBSP-A/L2/$year/$month/* /data/hpcdata/users/rablack75/first_attempt/data
    ## copy survey file
    #mkdir -p /data/hpcdata/users/rablack75/first_attempt/data/survey
    #scp -r /data/spacecast/wave_database_v2/RBSP-A/L2/$year/$month/$day/rbsp-a_WFR-spectral-matrix-diagonal_emfisis-L2_*.cdf /data/hpcdata/users/rablack75/first_attempt/data/survey
    ## copy magnetometer file
    #mkdir -p /data/hpcdata/users/rablack75/first_attempt/data/magnetometer
    #scp -r /data/spacecast/wave_database_v2/RBSP-A/L3/$year/$month/$day/rbsp-a_magnetometer_1sec-geo_emfisis-L3_*.cdf /data/hpcdata/users/rablack75/first_attempt/data/magnetometer
     
    ## Increment the date
    currdate=$(date -d "$currdate + 1month" +%Y%m%d)
done