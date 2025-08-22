# run_hyp3
This script is for automatically running all steps needed to submit, download, and prepare HyP3 multiburst interferograms for ingestion into MintPy, then running MintPy with default settings. It uses scripts from the repos [merge_hyp3](https://github.com/tshreve/merge_hyp3) and [download_hyp3](https://github.com/tshreve/download_hyp3).

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

- ## Installation
1. Clone the repository:
```bash
git clone https://github.com/tshreve/run_hyp3_workflow.git
```

2. Install dependencies for download using *run_hyp3_dependencies.txt* in a conda environment:
```bash
echo 'dask
hyp3_sdk
asf_search
gdal
numpy
mintpy' > run_hyp3_dependencies.txt
 ```

```bash
conda create --name run_hyp3 --file run_hyp3_dependencies.txt
conda activate run_hyp3
 ```

 3. Update [Earthdata login](https://urs.earthdata.nasa.gov/home) credentials in ```~/.netrc``` file:
```bash
echo 'machine urs.earthdata.nasa.gov
    login YOUR_USERNAME
    password YOUR_PASSWORD' >> ~/.netrc
 ```
 

## Usage


To run, use the following commands:  <br>
1. To submit jobs to HyP3: <br>
```bash
./run_hyp3_workflow.sh 1 job_name min_lon max_lon min_lat max_lat orb max_temp_base_days
```

where: <br>
```job_name``` : HyP3 job name <br>
```min_lon``` : Minimum longitude of AOI <br>
```max_lon``` : Maximum longitude of AOI <br>
```min_lat``` : Minimum latitude of AOI <br>
```max_lat``` : Maximum latitude of AOI <br>
```orb``` : Relative orbit (can be obtained through the [ASF Vertex Data Search](https://search.asf.alaska.edu/#/)) <br>
```max_temp_base_days``` : maximum temporal baseline for nearest neighbor pairs  <br>
 <br>

You will be prompted to check the created text file to ensure you are submitting the correct dates.
 <br>
2.  Once submitted jobs are finished, download and prepare HyP3 interferograms, and run MintPy with default settings:<br>
 ```bash
./run_hyp3_workflow.sh 2 job_name
```

where: <br>
```ref_Scene_ID``` : Reference scene ID <br>
```sec_Scene_ID``` : Secondary scene ID   <br>
```job_name```: HyP3 job name <br>
```filter_strength``` : interferogram filter strength <br>
 <br>
## Contributing
Contributions are encouraged! I will do my best to continue updating this script, but if you've found ways to improve it on your own, feel free to create a PR using the following:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Make your changes.
4. Push your branch: `git push origin feature-name`.
5. Create a pull request.

Ideas for increased functionality are also welcome. Thanks to all who are helping to make InSAR more accessible, in particular those who maintain [MintPy](https://github.com/insarlab/MintPy), [asf_search](https://github.com/asfadmin/Discovery-asf_search), and [hyp3_sdk](https://github.com/ASFHyP3/hyp3-sdk)!

## License
Please see [license information for MintPy](https://github.com/insarlab/MintPy?tab=License-1-ov-file), [asf_search](https://github.com/asfadmin/Discovery-asf_search?tab=BSD-3-Clause-1-ov-file), and [hyp3_sdk](https://github.com/ASFHyP3/hyp3-sdk?tab=BSD-3-Clause-1-ov-file).