#!/usr/bin/env python

import hyp3_sdk as sdk
from pathlib import Path
import dask
from dask.distributed import Client, progress
import sys 

# update number of workers and threads based on CPUs available
# more than 1 worker makes things chaotic due to automatic deletion of zip files
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: unzip.py data_folder")
        sys.exit(1)

    client = Client(threads_per_worker=2, n_workers=1)
    print(client.dashboard_link)

# choose output folder
results = []
folder = sys.argv[1]
data_dir=Path(folder)

# unzip files in parallel using dask
for ii in data_dir.glob('*.zip'):
    print(ii)
    try:
        result = dask.delayed(sdk.util.extract_zipped_product)(ii)
        results.append(result)
    except Exception as e:
        print(f'Warning: {e} Skipping download for {ii}.')

futures = dask.persist(*results)
results = dask.compute(*futures)