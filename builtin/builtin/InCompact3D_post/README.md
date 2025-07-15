
This is the post-processing to read file with adios2 bp5 from incompact3D examples.

### how to install
Installing the coeus-adapter will also generate an executable file named inCompact3D_analysis

### Jarvis(ADIOS2)

step 1: Build environment
```
spack load incompact3D@coeus
spack load openmpi
export PATH=~/coeus-adapter/build/bin/:$PATH
```
step 3: add jarvis repo
```
jarvis repo add coeus_adapter/test/jarvis/jarvis_coeus
```
step 4: Set up the jarvis packages
```
jarvis ppl create incompact3D_post
jarvis ppl append InCompact3D_post file_location=/path/to/data.bp5 nprocs=16 ppn=16 engine=bp5
jarvis ppl env build
```

step 5: Run with jarvis
```
jarvis ppl run
```

### Jarvis (Hermes)
This is the procedure for running the application with Hermes as the I/O engine.<br>
step 1: Place the run scripts in the example folder and copy an existing script as input.i3d.
The following example demonstrates this setup for the Pipe-Flow benchmark.
```
cd Incompact3d/examples/Pipe-Flow
cp input_DNS_Re1000_LR.i3d input.i3d
```

step 2: Build environment
```
spack load hermes@master
spack load incompact3D@coeus
spack load openmpi
export PATH=/incompact3D/bin:$PATH
export PATH=~/coeus-adapter/build/bin:$PATH
export LD_LIBRARY_PATH=~/coeus-adapter/build/bin:LD_LIBRARY_PATH
```
step 3: add jarvis repo
```
jarvis repo add coeus_adapter/test/jarvis/jarvis_coeus
```
step 4: Set up the jarvis packages
```
jarvis ppl create incompact3d
jarvis ppl append hermes_run provider=sockets
jarvis ppl append Incompact3d example_location=/path/to/incompact3D-coeus engine=hermes nprocs=16 ppn=16 benchmarks=Pipe-Flow
jarvis ppl append InCompact3D_post file_location=/path/to/data.bp5 nprocs=16 ppn=16 engine=hermes
jarvis ppl env build
```

step 5: Run with jarvis
```
jarvis ppl run
```
