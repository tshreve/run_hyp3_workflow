#!/usr/bin/env python3

import sys
from pathlib import Path
from datetime import timedelta
import hyp3_sdk as sdk
import asf_search as asf
import pandas as pd
from dateutil.parser import parse as parse_date
from collections import defaultdict

asf.constants.INTERNAL.CMR_TIMEOUT = 60 * 60  # Set CMR timeout to 1 hour

def parse_arguments():
    """Parse command line arguments
    job_name: Name of the job to submit
    max_temp_base_days: Maximum temporal baseline in days for pairs
    submit_true: Whether to submit the jobs (recommend setting False, then check pairs in output text file) (True/False)
    seasonal_true: Whether to include seasonal pairs (True/False)
    fall_spring_true: Whether to include fall-spring pairs (True/False)
    min_lon: Minimum longitude for search area
    max_lon: Maximum longitude for search area
    min_lat: Minimum latitude for search area
    max_lat: Maximum latitude for search area
    orb: Relative orbit number
    """
    if len(sys.argv) < 10:
        print("Usage: submit_multiburst.py job_name max_temp_base_days submit_true seasonal_true fall_spring_true min_lon max_lon min_lat max_lat orb")
        sys.exit(1)
    
    return {
        'job_name': sys.argv[1],
        'max_temporal_baseline': int(sys.argv[2]),
        'submit_jobs': sys.argv[3].lower() == 'true',
        'include_seasonal': sys.argv[4].lower() == 'true',
        'include_fallspring': sys.argv[5].lower() == 'true',
        'min_lon': float(sys.argv[6]),
        'max_lon': float(sys.argv[7]),
        'min_lat': float(sys.argv[8]),
        'max_lat': float(sys.argv[9]),
        'orb': int(sys.argv[10])
    }

# Set stack start and end dates, as well as search parameters
def search_stacks(stack_start='2014-01-01', stack_end='2025-07-01', min_lon=None, max_lon=None, min_lat=None, max_lat=None,orb=None):
    """Search for SAR data and create multiple stacks by burstID"""
    # Adjust based on desired search parameters
    options = { 
  	    'intersectsWith': f'POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))',
	    'dataset': 'SLC-BURST',
        'relativeOrbit': orb,
        'maxResults': 10000
    }

    # Search via ASF
    search_results = asf.search(**options)
    print(f"Found {len(search_results)} total burst scenes")
    if not search_results:
        print("No search results found")
        sys.exit(1)
    
    # Group scenes by burstID
    burst_groups = defaultdict(list)
    for scene in search_results:
        burst_id = scene.properties.get('burst', {}).get('fullBurstID', 'unknown')
        burst_groups[burst_id].append(scene)
    
    print(f"Found {len(burst_groups)} distinct burst IDs")
    
    # Create a stack for each burstID
    stacks = {}
    for burst_id, scenes in burst_groups.items():
        if len(scenes) < 2:
            print(f"Skipping burst ID {burst_id} with only {len(scenes)} scenes")
            continue
            
        print(f"Processing burst ID {burst_id} with {len(scenes)} scenes")
        
        # Get baseline results for this burst
        baseline_results = asf.baseline_search.stack_from_product(scenes[0])
        
        # Convert to DataFrame
        columns = list(baseline_results[0].properties.keys()) + ['geometry']
        data = [list(scene.properties.values()) + [scene.geometry] for scene in baseline_results]
        stack = pd.DataFrame(data, columns=columns)
        
        # Convert time strings to datetime objects
        stack['startTime'] = stack.startTime.apply(parse_date)
        stack['acquisitionDate'] = stack.startTime.dt.strftime('%Y%m%d')
        
        # Filter by date range
        stack_start_date = parse_date(f"{stack_start} 00:00:00Z")
        stack_end_date = parse_date(f"{stack_end} 00:00:00Z")
        filtered_stack = stack.loc[(stack_start_date <= stack.startTime) & 
                         (stack.startTime <= stack_end_date)]
        
        if len(filtered_stack) >= 2:
            stacks[burst_id] = filtered_stack
    
    return stacks

def generate_pairs_for_all_stacks(stacks, max_baseline, include_seasonal=False, include_fallspring=False):
    """Generate pairs for each stack and group by acquisition dates"""
    # First generate all pairs for each stack
    all_pairs = []
    for burst_id, stack in stacks.items():
        pairs = generate_pairs(stack, max_baseline, include_seasonal, include_fallspring)
        for ref, sec in pairs:
            # Get acquisition dates and granule IDs
            ref_date = stack.loc[stack.sceneName == ref, 'acquisitionDate'].iloc[0]
            sec_date = stack.loc[stack.sceneName == sec, 'acquisitionDate'].iloc[0]
            all_pairs.append((ref_date, sec_date, ref, sec))
    
    # Group pairs by date combinations
    date_grouped_pairs = defaultdict(list)
    for ref_date, sec_date, ref_granule, sec_granule in all_pairs:
        date_key = (ref_date, sec_date)
        date_grouped_pairs[date_key].append((ref_granule, sec_granule))
    
    return date_grouped_pairs

def generate_pairs(stack, max_baseline, include_seasonal=False, include_fallspring=False):
    """Generate pairs based on temporal baseline criteria"""
    sbas_pairs = set()
    print(include_fallspring)
    # Standard pairs within max_baseline
    for reference, rt in stack.loc[::-1, ['sceneName', 'temporalBaseline']].itertuples(index=False):
        secondaries = stack.loc[
            (stack.sceneName != reference) & 
            (stack.temporalBaseline - rt <= max_baseline) &
            (stack.temporalBaseline - rt > 0)
        ]
        for secondary in secondaries.sceneName:
            sbas_pairs.add((reference, secondary))
    
    # Add one-year-long seasonal pairs if requested
    if include_seasonal:
        for date, reference, rt in stack.loc[::-1, ['startTime', 'sceneName', 'temporalBaseline']].itertuples(index=False):
            if date.month < 9 and date.month > 5:  # Pre-September scenes
                secondaries = stack.loc[
                    (stack.sceneName != reference) &
                    (stack.temporalBaseline - rt <= (max_baseline + 365)) &
                    (stack.temporalBaseline - rt > 365)
                ]
                for secondary in secondaries.sceneName:
                    sbas_pairs.add((reference, secondary))
                    
    # Add fall-spring pairs if requested
    if include_fallspring:
        for date, reference, rt in stack.loc[::-1, ['startTime', 'sceneName', 'temporalBaseline']].itertuples(index=False):
            if date.month < 12 and date.month > 8:  # Fall scenes
                secondaries = stack.loc[
                    (stack.sceneName != reference) &
                    (stack.temporalBaseline - rt <= (max_baseline + 190)) &
                    (stack.temporalBaseline - rt > 190)
                ]
                for secondary in secondaries.sceneName:
                    sbas_pairs.add((reference, secondary))
      
    return sorted(sbas_pairs)

def submit_multi_burst_jobs(date_grouped_pairs, job_name_prefix):
    """Submit InSAR jobs grouped by acquisition date pairs"""
    try:
        hyp3 = sdk.HyP3(prompt="password")
        print(f"Submitting job {job_name_prefix}")

        job_ids = []
        for (ref_date, sec_date), pairs in date_grouped_pairs.items():
            # Extract granule lists for this date pair
            reference_granules = [pair[0] for pair in pairs]
            secondary_granules = [pair[1] for pair in pairs]
            
            # Create job name
            job_name = job_name_prefix
            
            
            # Submit as a single multi-burst job
            job = hyp3.submit_insar_isce_multi_burst_job(
                reference=reference_granules,
                secondary=secondary_granules,
                name=job_name,
                apply_water_mask=True,
                looks='10x2'
            )
            

            
        print(f"Successfully submitted {len(date_grouped_pairs)} multi-burst jobs")
        return 
        
    except Exception as e:
        print(f"Error submitting jobs: {e}")
        sys.exit(1)

def main():
    # Parse arguments
    args = parse_arguments()
    
    # Search for stacks by burst ID
    stacks = search_stacks(min_lon = args['min_lon'], max_lon = args['max_lon'], min_lat = args['min_lat'], max_lat = args['max_lat'], orb = args['orb'])

    # Generate pairs across all stacks and group by date
    date_grouped_pairs = generate_pairs_for_all_stacks(
        stacks, 
        args['max_temporal_baseline'], 
        args['include_seasonal'],
        args['include_fallspring']
    )
    
    # Save all pairs to file
    with open(f'{args["job_name"]}_all_pairs.txt', 'w') as file:
        for (ref_date, sec_date), pairs in date_grouped_pairs.items():
            file.write(f"# {ref_date} -> {sec_date} ({len(pairs)} pairs)\n")
            for reference, secondary in pairs:
                file.write(f"{reference},{secondary}\n")
    
    total_pairs = sum(len(pairs) for pairs in date_grouped_pairs.values())
    print(f"Total pairs: {total_pairs} across {len(date_grouped_pairs)} date combinations")
    
    # Submit jobs if requested
    if args['submit_jobs']:
        submit_multi_burst_jobs(date_grouped_pairs, args["job_name"])

if __name__ == '__main__':
    main()