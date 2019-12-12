
cd adUVCSupport
git clone https://github.com/jwlodek/libuvc.git
cd libuvc
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
make
mkdir ../../os
mkdir ../../os/linux-x86_64
cp *.so* ../../os/linux-x86_64/.
cp *.a ../../os/linux-x86_64/.
cd ../..
rm -rf libuvc
cd ..
make -sj
