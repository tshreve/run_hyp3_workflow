#!/bin/bash

# set variables, paths and environment
STEP=$1
burst_job=$2

if [ "$STEP" == "0" ]; then

    if [ $# -lt 10 ]; then
        echo "Usage: $0 step burst_job [min_lon] [max_lon] [min_lat] [max_lat] [orb] [max_temp_base_days] [date1] [date2]"
        echo "  Where "
        echo "  step - "
        echo "    0 - Submit jobs to Hyp3 without verification"
        echo "    1 - Submit jobs to Hyp3"
        echo "    2 - Download interferograms, prepare and run MintPy"
        echo "  burst_job - Name of the burst job"
        echo "  min_lon, max_lon, min_lat, max_lat - Bounding box coordinates (step 1 only)"
        echo "  orb - Orbit type (step 1 only)"
        echo "  max_temp_base_days - Maximum temporal baseline in days (step 1 only)"
        echo "  date1, date2 - Start and end dates for search (YYYY-MM-DD) (step 1 only)"
        exit 1
    fi

    echo "=== STEP 1: Submitting jobs to Hyp3 (default summer yearlong pairs) ==="
    ./submit_multiburst.py "$burst_job" $8 True True False $3 $4 $5 $6 $7 $9 ${10}
fi

# Submit to Hyp3
if [ "$STEP" == "1" ]; then

    if [ $# -lt 10 ]; then
        echo "Usage: $0 step burst_job [min_lon] [max_lon] [min_lat] [max_lat] [orb] [max_temp_base_days] [date1] [date2]"
        echo "  Where "
        echo "  step - "
        echo "    0 - Submit jobs to Hyp3 without verification"
        echo "    1 - Submit jobs to Hyp3"
        echo "    2 - Download interferograms, prepare and run MintPy"
        echo "  burst_job - Name of the burst job"
        echo "  min_lon, max_lon, min_lat, max_lat - Bounding box coordinates (step 1 only)"
        echo "  orb - Orbit type (step 1 only)"
        echo "  max_temp_base_days - Maximum temporal baseline in days (step 1 only)"
        echo "  date1, date2 - Start and end dates for search (YYYY-MM-DD) (step 1 only)"
        exit 1
    fi

    echo "=== STEP 1: Submitting jobs to Hyp3 (default summer yearlong pairs) ==="
    ## Submit to Hyp3 
    ./submit_multiburst.py "$burst_job" $8 False True False  $3 $4 $5 $6 $7 $9 ${10}

    echo "Please check the output text file for pairs to be processed."
    echo "Do you wish to proceed? (y/n)"  
    read REPLY
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./submit_multiburst.py "$burst_job" $8 True True False $3 $4 $5 $6 $7 $9 ${10}
    else
        echo "Job submission cancelled."
    fi
fi

# Download, unzip, and clip Hyp3 data; run MintPy with default settings
if [ "$STEP" == "2" ]; then

    if [ $# -lt 4 ]; then
        echo "Usage: $0 step burst_job download_folder mintpy_folder"
        echo "  Where "
        echo "  step - "
        echo "    0 - Submit jobs to Hyp3 without verification"
        echo "    1 - Submit jobs to Hyp3"
        echo "    2 - Download interferograms, prepare and run MintPy"
        echo "  burst_job - Name of the burst job"
        echo "  download_folder - Name of folder to download files"
        echo "  mintpy_folder - Name of folder to run MintPy"
        exit 1
    fi
    
    folder=$3
    mintpy_folder=$4

    echo "=== STEP 2: Downloading and processing data ==="
    
    mkdir "$folder"/"$burst_job"
    ./download.py "$folder"/"$burst_job" "$burst_job"
    ./unzip.py "$folder"/"$burst_job" 

    ./clip_burst.py "$folder"/"$burst_job"

    mkdir "$mintpy_folder"/"$burst_job"
    cp smallbaselineApp.cfg "$mintpy_folder"/"$burst_job"/.
    sed -i "s|burst_folder|"$mintpy_folder"/"$burst_job"/data|g" "$mintpy_folder"/"$burst_job"/smallbaselineApp.cfg
    
    mkdir "$mintpy_folder"/"$burst_job"/data
    ln -s "$folder"/"$burst_job"/* "$mintpy_folder"/"$burst_job"/data/.

    smallbaselineApp.py --dir "$mintpy_folder"/"$burst_job"  "$mintpy_folder"/"$burst_job"/smallbaselineApp.cfg
    save_gdal.py "$mintpy_folder"/"$burst_job"/velocity.h5 -d velocity -o "$mintpy_folder"/"$burst_job"/velocity_${burst_job}.tif
    save_gdal.py "$mintpy_folder"/"$burst_job"/velocity.h5 -d annualAmplitude -o "$mintpy_folder"/"$burst_job"/annualAmplitude_${burst_job}.tif

fi