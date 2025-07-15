# Gray-Scott Model
## what is the Gray-Scott application?
The Gray-Scott system is a **reaction–diffusion system**, meaning it models a process involving both chemical reactions and diffusion across space. In the case of the Gray-Scott model that reaction is a chemical reaction between two substances 
 u and v, both of which diffuse over time. During the reaction gets used up, while  is produced. The densities of the substances 
 and are represented in the simulation.

## what this model generate:
The Gray-Scott system models the chemical reaction

U + 2V ->  3V

This reaction consumes U and produces V. Therefore, the amount of both substances needs to be controlled to maintain the reaction. This is done by adding U at the "feed rate" F and removing V at the "kill rate" k. The removal of V can also be described by another chemical reaction:

V -> P

For this reaction P is an inert product, meaning it doesn't react and therefore does not contribute to our observations. In this case the Parameter k controls the rate of the second reaction.


## what is the input of gray-scott

The Gray-Scott system models two chemical species:

U: the feed chemical, continuously added to the system.

V: the activator chemical, which is produced during the reaction and also removed.




##  Key Input Parameters

| Parameter      | Description                                    | Typical Range or Example Values         |
|----------------|------------------------------------------------|----------------------------------------|
| **F**          | Feed rate of U (controls how quickly U is replenished in the system) | 0.01 – 0.08         |
| **k**          | Kill rate of V (controls how quickly V is removed from the system) | 0.03 – 0.07         |
| **Du**         | Diffusion coefficient for U                   | Typically ~2 × Dv        |
| **Dv**         | Diffusion coefficient for V                   | Lower than Du (e.g., half) |
| **Grid size(L)**  | Spatial resolution of the simulation grid     | 256×256, 512×512       |
| **Time step(Steps)**  | Time integration step size                   | 0.01 – 1.0            |
| **Initial condition** | Initial distribution of U and V         | U = 1, V = 0 with small localized perturbations (e.g., center patch with V = 1) |
| **Simulation speed** | Controls visual update or iteration speed | 1×, 2×, etc.          |
| **Color scheme** | Display mode for concentration visualization | Black & white or RGB sliders |
| **Noise(noise)** | add noise for the simulation | 0.01~0.1 |
| **I/O frequency(plotgap)** | the frequecey of I/O between simulation steps  | 1~10 |












Gray-Scott is a 3D 7-Point stencil code

# Installation
Since gray_scott is installed along with the coeus-adapter, these steps can be skipped.
```bash
git clone https://github.com/pnorbert/adiosvm
pushd adiosvm/Tutorial/gs-mpiio
mkdir build
pushd build
cmake ../ -DCMAKE_BUILD_TYPE=Release
make -j8
export GRAY_SCOTT_PATH=`pwd`
popd
popd
```




# Gray Scott model execution
Please follow these steps for the gray-scott with adios2 as I/O.
## 1. Setup Environment

Create the environment variables needed by Gray Scott
```bash
spack load mpi
export PATH="${COEUS_Adapter/build/bin}:$PATH"
```````````



## 2. Create a Pipeline

The Jarvis pipeline will store all configuration data needed by Gray Scott.

```bash
jarvis pipeline create gray-scott-test
```

## 3. Save Environment

Store the current environment in the pipeline.
```bash
jarvis pipeline env build
```

## 4. Add pkgs to the Pipeline

Create a Jarvis pipeline with Gray Scott
```bash
jarvis pipeline append adios2_gray_scott

```

## 5. Run Experiment

Run the experiment
```bash
jarvis pipeline run
```

## 6. Clean Data

Clean data produced by Gray Scott
```bash
jarvis pipeline clean
```

# Gray Scott With Hermes
Please follow this steps for the gray-scott with hermes as I/O engine and adios2 as I/O libray.
## 1. Setup Environment

Create the environment variables needed by Hermes + Gray Scott
```bash
# On personal
spack install hermes@master adios2
spack load hermes adios2
# On Ares
spack load hermes@master
# export GRAY_SCOTT_PATH=$/coeus_adapter/build/bin
export PATH="${COEUS_Adapter/build/bin}:$PATH"
```


## 2. Create a Pipeline

The Jarvis pipeline will store all configuration data needed by Hermes
and Gray Scott.

```bash
jarvis pipeline create gs-hermes
```

## 3. Save Environment

We must make Jarvis aware of all environment variables needed to execute applications in the pipeline.

```bash
jarvis pipeline env build
```

## 4. Add pkgs to the Pipeline

Create a Jarvis pipeline with Hermes, the Hermes MPI-IO interceptor,
and gray-scott
```bash
jarvis pipeline append hermes_run --sleep=10 --provider=sockets
jarvis pipeline append adios2_gray_scott engine=hermes 
```

For derived variable with adios2 in hermes:
```bash
jarvis pipeline append hermes_run --sleep=10 --provider=sockets
jarvis pipeline append adios2_gray_scott engine=hermes_derived
```

## 5. Run the Experiment

Run the experiment
```bash
jarvis pipeline run
```

## 6. Clean Data

To clean data produced by Hermes + Gray-Scott:
```bash
jarvis pipeline clean
```

# Adios2 Write engine for a BP5 file copy

## 1. Add this package to the Jarvis package folder
Compile the Coeus-adapter with OpenMPI.
## 2. Specify the location where you want the BP5 file copy:
```
jarvis pipeline append adios2_gray_scott engine=hermes bp_file_copy=/path/to/file
```
## 3. Run Gray-Scott
```
jarvis pipeline run
```


