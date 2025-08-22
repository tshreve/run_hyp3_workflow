#!/usr/bin/env python3

from pathlib import Path
from typing import List, Union
from osgeo import gdal
import dask
from dask.distributed import Client

gdal.UseExceptions()


def get_common_overlap(file_list: List[Union[str, Path]]) -> List[float]:
    """Get the common overlap of  a list of GeoTIFF files

    Arg:
        file_list: a list of GeoTIFF files

    Returns:
         [ulx, uly, lrx, lry], the upper-left x, upper-left y, lower-right x, and lower-right y
         corner coordinates of the common overlap
    """

    corners = [gdal.Info(str(dem), format='json')['cornerCoordinates'] for dem in file_list]

    ulx = max(corner['upperLeft'][0] for corner in corners)
    uly = min(corner['upperLeft'][1] for corner in corners)
    lrx = min(corner['lowerRight'][0] for corner in corners)
    lry = max(corner['lowerRight'][1] for corner in corners)
    return [ulx, uly, lrx, lry]

def clip_files(file,overlap):

            dst_file = file.parent / f'{file.stem}_clipped{file.suffix}'
            if not dst_file.exists():
                try:
                    gdal.Translate(destName=str(dst_file), srcDS=str(file), projWin=overlap)
                except:
                    print("Could not open data file", dst_file)
                    

def clip(data_folder):
    """Clip all GeoTIFF files to their common overlap
    
    Args:
        data_dir:
            directory containing the GeoTIFF files to clip
        overlap:
            a list of the upper-left x, upper-left y, lower-right-x, and lower-tight y
            corner coordinates of the common overlap
    Returns: None
    """
    data_dir = Path(data_folder)

    files = data_dir.glob('*/*_dem.tif')

    overlap = get_common_overlap(files)
    
    print(overlap)

    extensions =        [ '_unw_phase.tif', '_dem.tif','_lv_theta.tif', '_lv_phi.tif', '_water_mask.tif','_corr.tif','_conncomp.tif' ] 
                        #
                        #


    results = []

    for extension in extensions:
        for file in data_dir.rglob(f'*{extension}'):
            result = dask.delayed(clip_files)(file,overlap)
            results.append(result)

    futures = dask.persist(*results)
    results = dask.compute(*futures)

if __name__ == '__main__':
    import sys

    client = Client(threads_per_worker=2, n_workers=5)
    print(client.dashboard_link)

    if len(sys.argv) < 2:
        print("Usage: clip_burst.py data_folder")
        sys.exit(1)
    elif len(sys.argv) == 2:
        clip(sys.argv[1])