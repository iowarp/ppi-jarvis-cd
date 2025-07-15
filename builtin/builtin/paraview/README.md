# paraview 


ParaView is an open-source data analysis and visualization application designed to handle large-scale scientific datasets. It supports interactive and batch processing for visualizing complex simulations and performing quantitative analysis.

## Installation

```bash
spack install paraview
```

## how to use it with Jarvis in cluster

### set the environment
load paraview and openmpi
```
module load paraview
spack load openmpi

```
### create jarvis pipeline
```
jarvis ppl create paraview
jarvis ppl env build
jarvis ppl append paraview port_id=11111
```

### run the application
```
jarvis ppl run
```

## How to use it in local computer 
###
Run this command in local terminal:
```
ssh -N -L 11111:localhost:11111 your_id@ares.cs.iit.edu
```
In local paraview, following these instructions:
File -> connect </br>
Then set the port number and connect to Ares.  