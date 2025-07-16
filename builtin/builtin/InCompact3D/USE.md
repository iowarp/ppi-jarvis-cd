##  Run incompact3D 
### Jarvis(ADIOS2)
This is the procedure for running the application with ADIOS2 as the I/O engine.<br>
Step 1: find the benchmarks and its scripts file you want to run from [Incompact3D](https://github.com/xcompact3d/Incompact3d) github
```
Incompact3D/examples/benchmarks/scripts.i3d
```

step 2: Build environment
```
spack load incompact3D@coeus
spack load openmpi
export PATH=~/coeus-adapter/build/bin:$PATH
jarvis ppl env build
```
step 3: add jarvis repo
```
jarvis repo add coeus_adapter/test/jarvis/jarvis_coeus
```
step 4: Set up the jarvis packages
```
location=$(spack location -i incompact3D@coeus)
jarvis ppl create incompact3d
jarvis ppl append InCompact3D benchmarks=Pipe-Flow Incompact3D_location=$location output_folder=/output_fold/location script_file_name=input_DNS_Re1000_LR.i3d ppn=16 nprocs=16 engine=bp5
jarvis ppl env build

```

step 5: Run with jarvis
```
jarvis ppl run
```

Step 6: post-processing<br>
please refer this [jarvis packages](../InCompact3D_post) for post-processing.
Add InCompact3D_post to jarvis pipeline
```
jarvis ppl append InCompact3D_post benchmarks=Pipe-Flow output_folder=/output_fold/location engine=bp5 nprocs=1 ppn=16  
```
Jarvis will execute the test and generate output for the derived variables. <br>
Note: The current operation applied to derived variables is add, which may produce a large volume of output.

Step 7: visualization<br>
The visualization of bp5 file requires ParaView. <br>
Please refer this [jarvis packages](../paraview) for ParaView. <br>

### Jarvis (Hermes)
This is the procedure for running the application with Hermes as the I/O engine.<br>
Step 1: find the benchmarks and its scripts file you want to run
```
jarvis_coeus/Incompact3D/examples/benchmarks/scripts.i3d
```

step 2: Build environment
```
spack load hermes@master
spack load incompact3D@coeus
spack load openmpi
export PATH=~/coeus-adapter/build/bin:$PATH
export LD_LIBRARY_PATH=~/coeus-adapter/build/bin:LD_LIBRARY_PATH
```
step 3: add jarvis repo
```
jarvis repo add coeus_adapter/test/jarvis/jarvis_coeus
```
step 4: Set up the jarvis packages
```
jarvis ppl create incompact3d_hermes
jarvis ppl append hermes_run provider=sockets
jarvis ppl append Incompact3d example_location=/path/to/incompact3D-coeus engine=hermes nprocs=16 ppn=16 benchmarks=Pipe-Flow
jarvis ppl env build
```
Note: The current derived variable in coeus only support hash() opeartions.
```text
[ADIOS2 ERROR] <Helper> <adiosSystem> <ExceptionToError> : adios2_end_step: std::bad_array_new_length
```
This error is common for some other operations.<br>
step 5: Run with jarvis
```
jarvis ppl run
```

Step 6: post-processing<br>
please refer this [jarvis packages](../InCompact3D_post) for post-processing.
Add InCompact3D_post to jarvis pipeline
```
jarvis ppl append InCompact3D_post benchmarks=Pipe-Flow output_folder=/output_fold/location engine=hermes nprocs=1 ppn=16  
```
Step 7: visualization<br>
Currently, Hermes does not support the visualization. 



## Deploy without Jarvis (Adios)
```
spack load incompact3D@coeus
cd incompact3d/examples/Pipe-flow/
mpirun -np 16 ../../build/bin/xcompact3d
```