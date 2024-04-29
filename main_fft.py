# other numerical tools
import os
os.environ["CDF_LIB"] = "/path/to/cdf/library/directory"
# for cdf reading
from spacepy import pycdf

# for reading variables 
import sys


from datetime import timedelta
from datetime import datetime
# my own required functions

# FFT functions 

import funcs_FFT as fFFT

# import global constants 
import global_use as gl

date_string = sys.argv[1]
date_in_datetime = datetime.strptime(date_string, "%Y%m%d")

""" Defining all variables 

'start_date'        - chosen start date; datetime.datetime object
'end_date'          - chosen end date; datetime.datetime object
'no_days'           - number of days with burst data being FFT'd; integer

'date_string'       - full current day string
'year,month,day'    - year,month,day numerical strings

Burst-related parameters
NOTE: 'burst' is the local burst file name

'wfr_folder'        - parent burst file folder
'burst6'            - parnt burst filename
'wfr_burst_path'    - burst file for given day
'cdfs'              - burst CDF files for given day; list
'no_cdf'            - number of CDF files on given day; integer
'no_rec'            - number of burst records in each CDF file 

B_samples dictionary contains:
    'Bu'                - Magnetic field waveform measured in the u direction; nT
    'Bv'                - Magnetic field waveform measured in the v direction; nT
    'Bw'                - Magnetic field waveform measured in the w direction; nT
burst_params dictionary contains:
    'B_cal'             - Complex magnetic spectral density callibration values (for each of 6500 frequencies, regulary spaced) ; nT/Hz
    'df_cal'            - Frequency step size required for burst callibaration; Hz
    'f_max'             - Maximum frequency, above which receivers 'cuttoff'; Hz
    'burst_time'        - burst sample timestamp marking the start of the 6s sample; datetime.datetime object

Survey-related parameters

'survey_file'       - survey CDF file
'survey_data'       - class object containing all survey attributes

    'survey_freq'       - survey semi-log frequencies; Hz
    'survey_epoch'      - survey epoch; datetime.datetime 
    'Btotal'            - total magnetic spectral density; nT/Hz

Magentometer-related paraneters

'mag_file'          - L3 CDF file
'mag_data'          - class object containing all L3 attributes

    'fce'               - Gyrofrequency; Hz
    'fce_05'            - 0.5*gyrofrequency; Hz
    'fce_005'           - 0.05*gyrofrequency; Hz
    'fce_epoch'         - L3 epoch; datetime.datetime 

"""

    
day_files = gl.DataFiles(date_in_datetime)

# String version of dates for filename  
date_string,year,month,day =gl.get_date_string(date_in_datetime)
date_params = {"year": year,
                "month": month,
                "day": day,
                "single_day": date_in_datetime}


# Getting survey file and accessing survey frequencies, epoch and magnitude

survey_file = pycdf.CDF(day_files.survey_data)
survey_data = gl.AccessSurveyAttrs(survey_file)

survey_freq = survey_data.frequency
survey_epoch = survey_data.epoch_convert()
Btotal = survey_data.Bmagnitude

# Getting the magnetometer data

mag_file = pycdf.CDF(day_files.magnetic_data)
mag_data = gl.AccessL3Attrs(mag_file)

fce, fce_05, fce_005 = mag_data.f_ce
fce_epoch = mag_data.epoch_convert()

cdfs = day_files.burst_paths
no_cdf = len(cdfs)

if (no_cdf>0):

    # j counts every example for each day to append to plot names
    j=0

    for cdf in cdfs:
    
        # Open burst file
        burst = pycdf.CDF(cdf)

        # Count how many records on each CDF
        no_rec = len(burst['Epoch'])
        burst_epoch = gl.get_epoch(burst['Epoch'])

    
        
        print('found one')
        B_cal = burst['BCalibrationCoef']       # B callibration values (for each of 6500 frequencies, regulary spaced)
        df_cal = burst['CalFrequencies'][0]     # Frequency step size required for burst callibaration
        f_max = burst['CalFrequencies'][-1]     # Max frequency (where the receivers 'cuttoff')

        # this is just for the callibartion coefficients
        burst_params = {
            "B_cal": B_cal,
            "df_cal": df_cal,
            "f_max": f_max}

        # Now churning through each record in a given CDF
        for i in range(no_rec):
            
            j = j+1
            if (j%10 == 0):
                print(j, " bursts have now been identified")

            # date parameters for passing to functions more easily
            date_params["hour"] = str(burst['Epoch'][i].hour)
            date_params["burst_time"] = burst['Epoch'][i]
            

            ''' Find gyrfofrequencies for plotting '''

            fces = gl.cross_dataset(survey_file, mag_file, date_params["burst_time"]).calc_gyro()

            """ 
            Bu Bv Bw waveforms from burst file 
            """
            
            Bsamples = {"Bu": burst['BuSamples'][i],
                        "Bv": burst['BvSamples'][i],
                        "Bw": burst['BwSamples'][i]}

            ''' Doing FFTs:
                1. FFT_sliding: small windows of chosen size ('box_size') and overlap (defined by ('slider')
                2. FFT_Kletzing: fixed window size ('box_size' = 16384) and no window overlap ('slider' = 'box_size') - Kletzing et al, 2023
            '''   
            slider = gl.global_constants["Slider"]
            FFT_Kletzing = fFFT.PerformFFT(Bsamples,burst_params,slider).process_Kletzing_windows()
            FFT_sliding = fFFT.PerformFFT(Bsamples,burst_params,slider).process_sliding_windows()  
            
            ''' Save to CDFs '''
            make_cdf = fFFT.CreatePSDFiles(FFT_sliding,date_params,fces).save_FFT()
            make_cdf = fFFT.CreatePSDFiles(FFT_Kletzing,date_params,fces).save_FFT()

            