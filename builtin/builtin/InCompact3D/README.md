
# The Xcompact3D(Incompact3D) 

## what is the Incompact3D application?
Xcompact3d is a Fortran-based framework of high-order finite-difference flow solvers dedicated to the study of turbulent flows. Dedicated to Direct and Large Eddy Simulations (DNS/LES) for which the largest turbulent scales are simulated, it can combine the versatility of industrial codes with the accuracy of spectral codes. Its user-friendliness, simplicity, versatility, accuracy, scalability, portability and efficiency makes it an attractive tool for the Computational Fluid Dynamics community.

XCompact3d is currently able to solve the incompressible and low-Mach number variable density Navier-Stokes equations using sixth-order compact finite-difference schemes with a spectral-like accuracy on a monobloc Cartesian mesh.  It was initially designed in France in the mid-90's for serial processors and later converted to HPC systems. It can now be used efficiently on hundreds of thousands CPU cores to investigate turbulence and heat transfer problems thanks to the open-source library 2DECOMP&FFT (a Fortran-based 2D pencil decomposition framework to support building large-scale parallel applications on distributed memory systems using MPI; the library has a Fast Fourier Transform module).
When dealing with incompressible flows, the fractional step method used to advance the simulation in time requires to solve a Poisson equation. This equation is fully solved in spectral space via the use of relevant 3D Fast Fourier transforms (FFTs), allowing the use of any kind of boundary conditions for the velocity field. Using the concept of the modified wavenumber (to allow for operations in the spectral space to have the same accuracy as if they were performed in the physical space), the divergence free condition is ensured up to machine accuracy. The pressure field is staggered from the velocity field by half a mesh to avoid spurious oscillations created by the implicit finite-difference schemes. The modelling of a fixed or moving solid body inside the computational domain is performed with a customised Immersed Boundary Method. It is based on a direct forcing term in the Navier-Stokes equations to ensure a no-slip boundary condition at the wall of the solid body while imposing non-zero velocities inside the solid body to avoid discontinuities on the velocity field. This customised IBM, fully compatible with the 2D domain decomposition and with a possible mesh refinement at the wall, is based on a 1D expansion of the velocity field from fluid regions into solid regions using Lagrange polynomials or spline reconstructions. In order to reach high velocities in a context of LES, it is possible to customise the coefficients of the second derivative schemes (used for the viscous term) to add extra numerical dissipation in the simulation as a substitute of the missing dissipation from the small turbulent scales that are not resolved. 

Xcompact3d is currently being used by many research groups worldwide to study gravity currents, wall-bounded turbulence, wake and jet flows, wind farms and active flow control solutions to mitigate turbulence.  ​

## what this model generate:

### Numerical flow solutions
Xcompact3D produces high-fidelity numerical solutions to the Navier–Stokes equations, including: Velocity fields (u, v, w) in 3D. Pressure fields (p). Scalar fields (e.g., temperature, concentration) if configured. Derived quantities such as vorticity, dissipation rates, or turbulent stresses.

### 3D snapshots and flow visualizations
The solver can output 3D snapshots of flow variables at user-defined intervals.
These snapshots can be used for: Flow visualization (e.g., isosurfaces, slices, contours). Statistical analysis (mean fields, fluctuations). Detailed inspection of turbulent structures.

## Benchmark data and case studies
As demonstrated in the paper, Xcompact3D generates data for well-known CFD test cases, including:

1. Taylor–Green vortex: Transition from laminar to turbulent states.

2. Turbulent channel flow: Wall-bounded turbulence with comparisons to reference data.

3. Flow past a cylinder: Including wake dynamics and vortex shedding.

4. Lock-exchange flow: Variable-density gravity currents.

5. Fractal-generated turbulence: Turbulence control and mixing studies.

6. Wind farm simulations: Detailed turbine wake interactions.

##  Key Input Parameters (Xcompact3d)

| **Parameter**     | **Description**                                            | **Example / Options**                       |
|--------------------|------------------------------------------------------------|--------------------------------------------|
| **p_row, p_col**  | Domain decomposition for parallel computation             | Auto-tune (0), or set to match core layout |
| **nx, ny, nz**   | Number of mesh points per direction                         | E.g., 1024, 1025 (non-periodic)           |
| **xlx, yly, zlz** | Physical domain size (normalized or dimensional)          | E.g., 20D (cylinder case)                 |
| **itype**        | Flow configuration                                        | 0–11 (custom, jet, channel, etc.)         |
| **istret**      | Mesh refinement in Y direction                               | 0: none, 1–3: various center/bottom       |
| **beta**         | Refinement strength parameter                               | Positive values (trial & error tuning)     |
| **iin**           | Initial condition perturbations                            | 0: none, 1: random, 2: fixed seed        |
| **inflow_noise**| Noise amplitude at inflow                                   | 0–0.1 (as % of ref. velocity)           |
| **re**            | Reynolds number                                           | E.g., Re = 1/ν                           |
| **dt**            | Time step size                                            | User-defined, depends on resolution        |
| **ifirst, ilast**| Start and end iteration numbers                            | E.g., 0, 50000                            |
| **numscalar**   | Number of scalar fields                                     | Integer ≥ 0                               |
| **iscalar**     | Enable scalar fields                                        | Auto-set if numscalar > 0                |
| **iibm**        | Immersed Boundary Method                                    | 0: off, 1–3: various methods             |
| **ilmn**       | Low Mach number solver                                      | 0: off, 1: on                            |
| **ilesmod**   | LES model selection                                          | 0: off, 1–4: various models             |
| **nclx1...nclzn** | Boundary conditions per direction                         | 0: periodic, 1: free-slip, 2: Dirichlet |
| **ivisu**       | Enable 3D snapshots output                                 | 1: on                                    |
| **ipost**      | Enable online postprocessing                                 | 1: on                                    |
| **gravx, gravy, gravz** | Gravity vector components                          | E.g., (0, -1, 0)                        |
| **ifilter, C_filter** | Solution filtering controls                         | E.g., 1, 0.5                             |
| **itimescheme** | Time integration scheme                                    | E.g., 3: Adams-Bashforth 3, 5: RK3      |
| **iimplicit** | Y-diffusive term scheme                                     | 0: explicit, 1–2: implicit options      |
| **nu0nu, cnu** | Hyperviscosity/viscosity ratios                            | Default: 4, 0.44                        |
| **ipinter**     | Interpolation scheme                                      | 1–3 (Lele or optimized variants)       |
| **irestart**    | Restart from file                                          | 1: enabled                              |
| **icheckpoint** | Checkpoint file frequency                                 | E.g., every 5000 steps                 |
| **ioutput**    | Output snapshot frequency                                 | E.g., every 500 steps                  |
| **nvisu**      | Snapshot size control                                      | Default: 1                             |
| **initstat**  | Start step for statistics collection                        | E.g., 10000                            |
| **nstat**      | Statistics collection spacing                              | Default: 1                             |
| **sc, ri, uset, cp** | Scalar-related parameters                             | Schmidt, Richardson, settling, init conc.|
| **nclxS1...nclzSn** | Scalar BCs                                            | 0: periodic, 1: no-flux, 2: Dirichlet |
| **scalar_lbound, scalar_ubound** | Scalar bounds                           | E.g., 0, 1                             |
| **sc_even, sc_skew** | Scalar symmetry flags                               | True/False                            |
| **alpha_sc, beta_sc, g_sc** | Scalar wall BC params                         | For implicit solvers                   |
| **Tref**       | Reference temperature for scalar                          | Problem-specific                      |
| **iibmS**    | IBM treatment for scalars                                   | 0: off, 1–3: various modes          |

---


## Install with spack
step 1: Install Spack
```
cd ${HOME}
git clone https://github.com/spack/spack.git
cd spack
git checkout tags/v0.22.2
echo ". ${PWD}/share/spack/setup-env.sh" >> ~/.bashrc
source ~/.bashrc
```
step 2: Clone the coeus-adapter repos
```
git clone -b derived-merged https://github.com/grc-iit/coeus-adapter.git
```
step 3: Add Coeus repo packages for spack
```
spack repo add /coeus_adapter/CI/coeus
```
step 4: Install the incompact3D with spack
```
spack install incompact3D io_backend=adios2 ^openmpi ^adios2-coeus@2.10.0
```

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

## Install without spack

### installation as ADIOS2 I/O as backup
step 1: 2decomp-fft handles domain decomposition and parallel I/O, which Incompact3D depends on for writing field data.<br>
Below is the installation process for 2decomp-fft with ADIOS2 support
```
git clone -b coeus https://github.com/hxu65/2decomp-fft.git
spack load intel-oneapi-mkl
spack load openmpi
export MKL_DIR=/mnt/common/hxu40/spack/opt/spack/linux-ubuntu22.04-skylake_avx512/gcc-11.4.0/intel-oneapi-mkl-2024.2.2-z5q74r7t24qiimwlklk6jofy5twcmsjq/mkl/latest/lib/cmake/mkl
cmake -S . -B ./build -DIO_BACKEND=adios2 -DCMAKE_PREFIX_PATH=/mnt/common/hxu40/software/2decomp-fft/build -Dadios2_DIR=/mnt/common/hxu40/install2/lib/cmake/adios2
cd build
make -j8
make install
```
step 2: build the incompact3D with 2decomp-fft support
```
git clone https://github.com/xcompact3d/Incompact3d
cd Incompact3d
spack load intel-oneapi-mkl
spack load openmpi
export MKL_DIR=${MKLROOT}/lib/cmake/mkl
cmake -S . -B ./build -DIO_BACKEND=adios2 -Dadios2_DIR=/path/to/adios2/install/lib/cmake/adios2 -Ddecomp2d_DIR=/path/to/decomp2d/build
cd build
make -j8
make install
```


## Deploy without Jarvis (Adios)
```
spack load incompact3D@coeus
cd incompact3d/examples/Pipe-flow/
mpirun -np 16 ../../build/bin/xcompact3d
```




