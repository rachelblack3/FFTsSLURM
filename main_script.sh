#!/bin/bash

startdate="20130201"
enddate="20130301"

currdate=$startdate

## Loop from the start to the end
while [[ "$currdate" < "$enddate" ]]; do

    ## Get the year and the month from the current date
    year=$(date -d "$currdate" +%Y)
    month=$(date -d "$currdate" +%m)
    day=$(date -d "$currdate" +%d)

    ## Copy all of the day folders to the HPCDATA filesystem
    HPCDATA='/data/hpcdata/users/rablack75/first_attempt/data'
    WORKSDATA='/data/spacecast/wave_database_v2/RBSP-A/L2/$year/$month/*'

    ## copy all burst files from every day in given month
    for i in $(seq 7)
    do
        scp -r /data/spacecast/wave_database_v2/RBSP-A/L2/$year/$month/0$i /data/hpcdata/users/rablack75/first_attempt/data
    done

    Burst_days=(/data/hpcdata/users/rablack75/first_attempt/data/*) 
    ## Get number of days in month                                     
    numdays=${#Burst_days[@]}                                                                                      
    
    ## create magnetometer folder
    mkdir -p /data/hpcdata/users/rablack75/first_attempt/data/magnetometer
    
    ## copy over magnetometer data
    for i in $(seq $numdays)
    do
        scp -r /data/spacecast/wave_database_v2/RBSP-A/L3/$year/$month/0$i/rbsp-a_magnetometer_1sec-geo_emfisis-L3_*.cdf /data/hpcdata/users/rablack75/first_attempt/data/magnetometer
    done

    # take off 1 day from number of days as the array indicies in slurm script goes from 0 to numdays-1 
    numdays=`expr $((numdays-1))`
    
    ## Run actual sbatch processing code for each day of the month
    ## the --export options allows you to list bash varaiables that you wish to pass to the slurm script
    sbatch --array=0-$numdays --export=currdate=$currdate processing_batch_file.sh

    ## create folder for daily output
    mkdir -p /data/emfisis_burst/wip/rablack75/rablack75/SLURM_attempt/$year/$month/$day
    
    ## transfer all new files to /data/emfisisburst
    scp -r /data/hpcdata/users/rablack75/first_attempt/output /data/emfisis_burst/wip/rablack75/rablack75/SLURM_attempt/$year/$month/$day
    
    ## remove all data files and output from the hpc folders
    rm -rf /data/hpcdata/users/rablack75/first_attempt/data/*
    rm -rf /data/hpcdata/users/rablack75/first_attempt/output/*

    ## Increment the date
    currdate=$(date -d "$currdate + 1month" +%Y%m%d)


done