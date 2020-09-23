

wget https://github.com/zeromq/libzmq/releases/download/v4.3.3/zeromq-4.3.3.tar.gz
tar -xzf zeromq-4.3.3.tar.gz 
mkdir zmq
rm zeromq-4.3.3.tar.gz
cd zeromq-4.3.3

./autogen.sh
./configure --prefix=$(pwd)/../zmq
make
make install
cd ..
rm -rf zeromq-4.3.3

make -sj
cp -r zmq/lib/* lib/linux-x86_64/.
