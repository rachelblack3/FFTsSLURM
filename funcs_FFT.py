''' The following code contains two classes:

    --> PerfromFFT: contains functions with FFT routines 
    --> CreatePSDFiles: creates CDF files to hold the PSD from FFT routines 
'''

import numpy as np

# datetime package
from datetime import datetime

# FFT package
from scipy.fft import fft,rfftfreq

# File creation/control
import os

# CDF file management 
from spacepy import pycdf

# Global parameters/function
import global_use as global_constants

class PerformFFT:
    ''' class for storing all methods related to performing FFTs

        Defining key parameters:

        'N'                 - number of points in sample; integer
        'box_size'          - number of points in each window; integer
        'n_bins'            - number of FFT windows in total sample; integer
        'n_f'               - number of frequencies; integer
        'df'                - frequency bin width; Hz
        'Twin'              - temporal duration of window; s
        'duration'          - total duration of burst PSD; s

        Frequency calibration parameters:

        'cal_step'          - ratio between FFT frequency & callibration frequency bin width
        'Bcal_c             - callibration coefficients associated with FFT frequencies 

        Hanning window:
        
        'w'                  - hanning function; dependent on 'box_size'
        'wms'                - correction to the FFT power spectral densities required as a result of the Hanning window

        FFT:

        'fft_box'           - array to hold FFTs in each U, V, W direction, dimensions(n_bins, n_f, 3); complex nT
        'total'             - power spectrum in each U, V, W direction, dimensions(n_bins, n_f, 3); nT
        'PSD'               - power spectral density magnitdue, dimensions(n_bins, n_f); nT/Hz
        't_array'           - time array based upon n_bins and duration
        'n_468'             - number of sliding windows in first 0.468s, corresponding to single kletzing window; integer
        'PSD_468'           - power spectral density of first n_468 windows; nT/Hz

        Outputs:

        'FFTs'               - dictionary containing all required FFT data for saving

    '''

    def __init__(self,
               waveform_samples,
               burst_params,
               slider):

        self.waveform_samples = waveform_samples # Bu, Bv, Bw
        self.burst_params = burst_params         # B_cal, df_cal, f_max
        self.slider = slider                     # slider from global constants
    
    def process_Kletzing_windows(self):
    
        """ Doing the FFT porcess identical to that on board the PBSP (Kletzing, 2023)
        In other words, using a 0.468s window from the beginning of the 6s burst sample, before rebinning into semi-logirtihmic bins
        """
        Bu = self.waveform_samples["Bu"]
        Bv = self.waveform_samples["Bv"]
        Bw= self.waveform_samples["Bw"]
        
        f_s = global_constants.global_constants["f_s"] 
        N = len(Bu)                                                     # Number of sample points
        box_size = global_constants.global_constants["Kletzing box"]    # Number of samples in each box 
        n_bins =  int(N/box_size)                                       # Number of points in temporal space


        """ 
        Frequencies from FFT boxes
        """
        
        freq = rfftfreq(box_size, f_s)[:box_size//2]
        n_f = len(freq)

        df = freq[1] - freq[0]

        """ 
        Putting the calibration coeffcients into complex form
        """
        cal_step = int(df/self.burst_params["df_cal"])
        Bcal_c=[]
        
        for i in range(n_f):
            f = freq[i]
            if (f < self.burst_params["f_max"]):
                Bcal_c.append(complex(self.burst_params["B_cal"][i*cal_step,0],self.burst_params["B_cal"][i*cal_step,1]))
            else:
                break
        
        # Resetting number of frequencies to f_max - i.e. Cutting off frequencies where the reciever stopped picking them up (fmax from callibration specifications))
        n_f = len(Bcal_c)
        freq = freq[0:n_f]  

        """ 
        Do FFTs - remember to normalise by N and multiply by hanning window and complex correction
        """
        # create array for storing FFTs in each U, V and W directions

        fft_box = np.zeros((n_bins,n_f,3),dtype = complex)

        w = np.hanning(box_size)                                            # hanning window
        wms = np.mean(w**2)                                                 # hanning window correction
            
        lower_edge = 0
        upper_edge = box_size
        slider = box_size

        i = 0 
        
        while i<n_bins:

            fft_box[i,:,0] = (fft(w*(1/box_size)*Bu[lower_edge:upper_edge]))[:n_f]*Bcal_c  
            fft_box[i,:,1] = (fft(w*(1/box_size)*Bv[lower_edge:upper_edge]))[:n_f]*Bcal_c
            fft_box[i,:,2] = (fft(w*(1/box_size)*Bw[lower_edge:upper_edge]))[:n_f]*Bcal_c
            
            # update lower and upper edge - no overlapping windows
            lower_edge += slider
            upper_edge += slider

            i += 1

        # get temporal size of window
        T_window = box_size*f_s

        print('the frequency bands for little bins are',df)

        """ 
        take absolute values and square to get power density
        """
        total = abs(fft_box) * abs(fft_box)

        """ 
        divide array by correction for spectral power lost by using a hanning window
        """
        total= total/wms
        
        """ 
        find B field magnitude
        """
        PSD = np.zeros((n_bins,n_f))

        for n in range(n_f):
            for m in range(n_bins):

                # Multiply by 2 to account for negative freqiencies from FFT 
                # Divide by frequency step size to have a PSD in units/Hz 
                PSD[m,n]=(total[m,n,0]+total[m,n,1]+total[m,n,2])*2*T_window  
        
        """ 
        define the time array for plotting
        """
        duration = n_bins*T_window
        Twin = global_constants.global_constants["f_s"]*global_constants.global_constants["Kletzing box"]
        t_array = np.linspace(0.,duration, n_bins)

        FFTs = {"Frequencies": freq,
            "PSD": PSD,
            "Time": t_array,
            "Flag": 'Kletzing'} 

        return FFTs
    

    """ FFT with sliding overlapping windows """

    def process_sliding_windows(self):
        from scipy.fft import fft,rfftfreq
        import numpy as np

        Bu = self.waveform_samples["Bu"]
        Bv = self.waveform_samples["Bv"]
        Bw = self.waveform_samples["Bw"]

        f_s = global_constants.global_constants["f_s"]
        N = len(Bu)                                                     # Number of sample points
        box_size = global_constants.global_constants["Sliding box"]     # Number of samples in each box 
        n_bins = int((N - (box_size - self.slider))/self.slider)        # Number of points in temporal space


        """ 
        Frequencies from FFT boxes
        """
        
        freq = rfftfreq(box_size, f_s)[:box_size//2]
        n_f = len(freq)

        df = freq[1] - freq[0]


        """ 
        Putting the calibration coeffcients into complex form
        """
        cal_step = int(df/self.burst_params["df_cal"])
        Bcal_c=[]
        
        for i in range(n_f):
            f = freq[i]
            if (f < self.burst_params["f_max"]):
                Bcal_c.append(complex(self.burst_params["B_cal"][i*cal_step,0],self.burst_params["B_cal"][i*cal_step,1]))
            else:
                break
        
        # Resetting number of frequencies to f_max - i.e. Cutting off frequencies where the reciever stopped picking them up (fmax from callibration specifications))
        n_f = len(Bcal_c)
        freq = freq[0:n_f]  

        """ 
        Do FFTs - remember to normalise by N and multiply by hanning window and complex correction
        """

        fft_box = np.zeros((n_bins,n_f,3),dtype = complex)

        w = np.hanning(box_size)                                            # hanning window
        wms = np.mean(w**2)                                                 # hanning window correction

        # Do sliding window FFTs

            
        lower_edge = 0              # Lower edge of each box
        upper_edge = box_size       # Upper edge of each box
        i = 0 

        while upper_edge<N:

            fft_box[i,:,0] = (fft(w*(1/box_size)*Bu[lower_edge:upper_edge]))[:n_f]*Bcal_c  
            fft_box[i,:,1] = (fft(w*(1/box_size)*Bv[lower_edge:upper_edge]))[:n_f]*Bcal_c
            fft_box[i,:,2] = (fft(w*(1/box_size)*Bw[lower_edge:upper_edge]))[:n_f]*Bcal_c
            
            lower_edge += self.slider
            upper_edge += self.slider

            i += 1

        fft_av = fft_box
    
        T_window = box_size*f_s

        print('the frequency bands for little bins are',df)

        """ 
        take absolute values and square to get power density
        """
        total = abs(fft_av) * abs(fft_av)

        """ 
        divide array by correction for spectral power lost by using a hanning window
        """
        total= total/wms
        
        """ 
        find B field magnitude
        """
        PSD = np.zeros((n_bins,n_f))

        for n in range(n_f):
            for m in range(n_bins):

                # Multiply by 2 to account for negative freqiencies from FFT 
                # Divide by frequency step size to have a PSD in units/Hz 
                PSD[m,n]=(total[m,n,0]+total[m,n,1]+total[m,n,2])*2*T_window  
        
        """ 
        define the time array for plotting
        """
        duration = N*f_s
        
       
        t_array = np.linspace(0,duration, n_bins)
        n_468 = int((duration/0.468)*n_bins)
        
        # input flag for kletzing or sliding

        FFTs = {"Frequencies": freq,
            "PSD": PSD,
            "PSD_0468s": PSD[0:n_468,:],
            "Time": t_array,
            "Flag": 'sliding'} 

        return FFTs
    

class CreatePSDFiles:

    ''' class for creating CDFs containg burst FFT data + statistics
    
            PARAMETERS:
             '''

    def __init__(self,FFTs,date_params,fces):

        self.PSD = FFTs["PSD"]
        self.Frequency = FFTs["Frequencies"]
        self.Time = FFTs["Time"]
        self.timedate = date_params
        self.Kletzing = FFTs["Flag"]
        self.fce = fces[0]
        self.fce_05 = fces[1]
        self.fce_005 = fces[2]
    
    
    def save_FFT(self):
        
        # What is the date and time of this burst? Make a directory for that day
        file_path = 'output/' + self.timedate['day']

        # Check if directry exists, otherwise create directory
        os.makedirs(file_path, exist_ok=True)

        # Is it Kletzing windows or sliding windows?
        if self.Kletzing == 'Kletzing':
            cdf_name = file_path+ '/' + 'PSD_Kletzing_'+ datetime.strftime(self.timedate['burst_time'],'%Y-%m-%d_%H:%M:%S.%f')+'.cdf'
        else:
            cdf_name = file_path+ '/'  + 'PSD_sliding_'+ datetime.strftime(self.timedate['burst_time'],'%Y-%m-%d_%H:%M:%S.%f') +'.cdf'

        # Create CDF for Burst record
        cdf = pycdf.CDF(cdf_name, '')

        # Save main datasets: the PSD, the time steps, and the frequencies
        cdf['Time'] = self.Time
        cdf['PSD'] = self.PSD
        cdf['Frequencies'] = self.Frequency

        # Set units for the above
        cdf['PSD'].attrs['units'] = 'nT/Hz'
        cdf['Frequencies'].attrs['units'] = 'Hz'
        cdf['Time'].attrs['units'] = 's'

        # Set dependencies for the PSD
        cdf['PSD'].attrs['Dependency1'] = 'Time'
        cdf['PSD'].attrs['Dependency2'] = 'Frequency' 

        # other important quantities; gyrofrequencies and timestamp (beginning of burst)
        cdf.new('fce', self.fce, recVary=False)
        cdf.new('fce_05', self.fce_05, recVary=False)
        cdf.new('fce_005', self.fce_005, recVary=False)
        cdf.new('BurstDatetime', self.timedate['burst_time'], recVary=False)

        cdf['fce'].attrs['units'] = 'Hz'
        cdf['fce'].attrs['CATDESC'] = 'Gyrofrequency calculated from L3 magnetometer data'
        cdf['fce_05'].attrs['units'] = 'Hz'
        cdf['fce_05'].attrs['CATDESC'] = '0.5*gyrofrequency calculated from L3 magnetometer data'
        cdf['fce_005'].attrs['units'] = 'Hz'
        cdf['fce_005'].attrs['CATDESC'] = '0.05*gyrofrequency calculated from L3 magnetometer data'
        cdf["BurstDatetime"].attrs['units'] = "datetime.datetime object"

        # set author & burst datetime
        cdf.attrs['Author'] = 'Rachel Black'
        cdf.attrs['Date created'] = datetime.now()
        # close the CDF file
        cdf.close()

        return
    