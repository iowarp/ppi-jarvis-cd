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