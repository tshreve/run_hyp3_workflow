#!/usr/bin/env python

from pathlib import Path
import numpy as np
from hyp3_sdk import HyP3
from dask.distributed import Client
import sys 

# update number of workers and threads based on CPUs available
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: download.py data_folder job_name")
        sys.exit(1)
    
    client = Client(threads_per_worker=2, n_workers=5)
    print(client.dashboard_link)


username = 'username'
password = 'password'

# add data folder here 
folder = sys.argv[1]

# parallel processing works well with username and password input here
# could also try adding credentials from a `.netrc` file.
try:
    hyp3 = HyP3(username=username,password=password)
except:
    print("Error: could not authenticate Earthdata account, check username and password.")
    sys.exit(1)
    
# job to download
jname = sys.argv[2] 

# download zip files to chosen folder
job = hyp3.find_jobs(name=jname)
#job = hyp3.watch(job)
insar_products = job.download_files(folder)