# Installation
The gray_scott is installed along with the coeus-adapter. 
```bash
git clone https://github.com/grc-iit/coeus-adapter.git
cd coeus-adapter
mkdir build
cd build
cmake ../
make -j8
```

For the official way to install gray-scott, please refer here.
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
