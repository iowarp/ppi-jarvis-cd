# WRF is the application to stimulation weather

# Installation and usage of WRF
A detailed installation and usage can be found here:    
https://github.com/grc-iit/jarvis-cd/wiki/7.5.-WRF



# WRF With Hermes

## 1. Setup Environment

Create the environment variables needed by Hermes + WRF
```bash
export LD_LIBRARY_PATH=/coeus-adapter/build/bin:$LD_LIBRARY_PATH
export PATH=/coeus-adapter/build/bin:$PATH
module load adios2
spack load hermes@master
export DIR=~/Build_WRF/LIBRARIES
export LD_LIBRARY_PATH=$DIR/lib:$LD_LIBRARY_PATH
export PATH=$DIR/bin:$PATH
export LD_LIBRARY_PATH=/adios2/lib:$LD_LIBRARY_PATH
```

## 2. Install Jarvis and set up Jarvis
Please refer this website for more information about Jarvis.  
https://grc.iit.edu/docs/jarvis/jarvis-cd/index

## 3. Create a Pipeline

The Jarvis pipeline will store all configuration data needed by Hermes
and Gray Scott.

```bash
jarvis pipeline create wrf
```

## 3. Save Environment

Store the current environment in the pipeline.
```bash
jarvis pipeline env build
```

## 4. change some parameter in namelist.input file
```
io_form_history = 14
io_form_restart = 14
frames_per_outfile   = 1000000,
```
## 5. Add pkgs to the Pipeline

Create a Jarvis pipeline with Hermes, the Hermes MPI-IO interceptor,
and wrf
```bash
jarvis pipeline append hermes_run --sleep=10 provider=sockets
jarvis pipeline append wrf wrf_location=/WRF/test/em_real nprocs=4 ppn=6 engine=hermes

```

## 6. Run the Experiment

Run the experiment
```bash
jarvis pipeline run
```

## 7. Clean Data

To clean data produced by Hermes + Gray-Scott:
```bash
jarvis pipeline clean
```
