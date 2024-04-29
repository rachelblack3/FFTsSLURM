#!/bin/bash
#SBATCH -o /data/hpcdata/users/rablack75/first_attempt/output/%a.out
#SBATCH --error=/data/hpcdata/users/rablack75/first_attempt/output/%a.err
#SBATCH -J printname
#SBATCH --mem=10gb
#SBATCH --time=00:10:00
#SBATCH --mail-type=begin,end,fail
#SBATCH --mail-user=rablack75@bas.ac.uk
#SBATCH --partition=short
#SBATCH --account=short 
#SBATCH --wait                                                  

source /data/hpcdata/users/rablack75/burstenv/bin/activate                     # activate environment

date=$(date -d "$currdate + ${SLURM_ARRAY_TASK_ID}day" +%Y%m%d)

python /data/hpcdata/users/rablack75/first_attempt/main_fft.py ${date}