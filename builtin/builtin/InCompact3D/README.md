
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













