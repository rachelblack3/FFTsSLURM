# FFTsSLURM
Code for doing my RBSP burst FFTs on the HPC

## Summary
The space on the HPC is limited. At one time, I have space for 160 GB of data. This corresponds to a month's worth of burst input (RBSP CDFs) and output (my FFT CDFs).
Therefore, this code currently:

  1. copies over a weeks's worth of data to the HPC data storage (can easily do a month, was just testing out for timings...)
  2. performs the FFTs on these files (the code is parallelised in SLURM by sending each day to a different core)
  3. copies the output from the HPC data storage to my data storage
  4. and, finally, deletes all input/output from the HPC

This process is in a wider loop specifiying the date range desried.

The outer loop copying over the data and passing inforation to the SLURM script is in **main_script.sh**
The SLURM script that parallelises the job by day and sends to the HPC is **proccessing_batch_file.sh**
The python script performing the FFTs is **main_fft.py**, which also uses functions from **funcs_fft.py** and **global_use.py**

The output files are of format:

- **PSD_Kletzing_{datetime}.cdf**: The 0.468s FFTs

- **PSD_sliding_{datetime}.cdf**: The 0.03s FFTs



