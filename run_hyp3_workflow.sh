
if [ $# -lt 2 ]; then
    echo "Usage: $0 step burst_job [min_lon] [max_lon] [min_lat] [max_lat] [orb] [max_temp_base_days]"
    echo "  Where step is:"
    echo "    0 - Submit jobs to Hyp3 without verification"
    echo "    1 - Submit jobs to Hyp3"
    echo "    2 - Download interferograms, prepare and run MintPy"
    echo "  burst_job - Name of the burst job"
    echo "  min_lon, max_lon, min_lat, max_lat - Bounding box coordinates (optional)"
    echo "  orb - Orbit type (optional)"
    echo "  max_temp_base_days - Maximum temporal baseline in days (optional)"
    exit 1
fi

# set variables, paths and environment
STEP=$1
echo $STEP
burst_job=$2
folder=/path/to/your/data/folder/
mintpy_folder=/path/to/your/mintpy/folder/

# environment for running download.py, unzip.py, and submit_multiburst.py
conda activate run_hyp3

if [ "$STEP" == "0" ]; then
    echo "=== STEP 1: Submitting jobs to Hyp3 (default 40 day temp baseline) ==="
    ./submit_multiburst.py "$burst_job" $8 True True False $3 $4 $5 $6 $7
fi

# Submit to Hyp3
if [ "$STEP" == "1" ]; then
    echo "=== STEP 1: Submitting jobs to Hyp3 (default 40 day temp baseline) ==="
    ## Submit to Hyp3 
    ./submit_multiburst.py "$burst_job" $8 False True False  $3 $4 $5 $6 $7

    echo "Please check the output text file for pairs to be processed."
    echo "Do you wish to proceed? (y/n)"  
    read REPLY
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./submit_multiburst.py "$burst_job" $8 True True False $3 $4 $5 $6 $7
    else
        echo "Job submission cancelled."
    fi
fi

# Download, unzip, and clip Hyp3 data; run MintPy with default settings
if [ "$STEP" == "2" ]; then
    echo "=== STEP 2: Downloading and processing data ==="

    mkdir "$folder"/"$burst_job"
    ./download.py "$folder"/"$burst_job" "$burst_job"
    ./unzip.py "$folder"/"$burst_job" 

    cd ${merge_folder}

    ./clip_burst.py "$folder"/"$burst_job"

    mkdir "$mintpy_folder"/"$burst_job"
    cp "$config_file" "$mintpy_folder"/"$burst_job"/.
    sed -i "s|burst_folder|$burst_job|g" "$mintpy_folder"/"$burst_job"/smallbaselineApp.cfg
    
    mkdir "$mintpy_folder"/"$burst_job"/data
    ln -s "$folder"/"$burst_job"/* "$mintpy_folder"/"$burst_job"/data/.

    smallbaselineApp.py --dir "$mintpy_folder"/"$burst_job"  "$mintpy_folder"/"$burst_job"/smallbaselineApp.cfg
    save_gdal.py velocity.h5 -d velocity -o velocity_${burst_job}.tif
    save_gdal.py velocity.h5 -d annualAmplitude -o annualAmplitude_${burst_job}.tif

fi