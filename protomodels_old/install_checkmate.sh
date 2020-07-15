#!/bin/sh

homeDIR="$( pwd )"

madgraph="MG5_aMC_v2.6.7.tar.gz"
URL=https://launchpad.net/mg5amcnlo/2.0/2.6.x/+download/$madgraph
echo -n "Install MadGraph (y/n)? "
read answer
if echo "$answer" | grep -iq "^y" ;then
	mkdir MG5;
	echo "[installer] getting MadGraph5"; wget $URL 2>/dev/null || curl -O $URL; tar -zxf $madgraph -C MG5 --strip-components 1;
	cd $homeDIR
	rm $madgraph;
fi

#Get pythia tarball
pythia="pythia8244.tgz"
URL=http://home.thep.lu.se/~torbjorn/pythia8/$pythia
echo -n "Install Pythia (y/n)? "
read answer
if echo "$answer" | grep -iq "^y" ;then
	if hash gzip 2>/dev/null; then
		mkdir pythia8;
		echo "[installer] getting Pythia"; wget $URL 2>/dev/null || curl -O $URL; tar -zxf $pythia -C pythia8 --strip-components 1;
		echo "Installing Pythia in pythia8";
		cd pythia8;
		./configure --with-root=$ROOTSYS --prefix=$homeDIR/pythia8 --with-gzip
		make -j4; make install;
		cd $homeDIR
		rm $pythia;
	else
		echo "[installer] gzip is required. Try to install it with sudo apt-get install gzip";
	fi
fi


echo -n "Install Delphes (y/n)? "
read answer
if echo "$answer" | grep -iq "^y" ;then
	echo "[installer] getting Delphes";
  git clone https://github.com/delphes/delphes.git Delphes;
  cd Delphes;
  export PYTHIA8=$homeDIR/pythia8;
  echo "[installer] installing Delphes";
  make HAS_PYTHIA8=true;
	cd $homeDIR;
fi


echo -n "Install CheckMATE (y/n)? "
read answer
if echo "$answer" | grep -iq "^y" ;then
  echo "[installer] getting CheckMATE";
    git clone git@github.com:CheckMATE2/checkmate2.git CheckMATE2;
  cd CheckMATE2;
  rm -rf .git
  autoreconf -i -f;
  ./configure --with-rootsys=$ROOTSYS --with-delphes=$homeDIR/Delphes --with-pythia=$homeDIR/pythia8 --with-madgraph=$homeDIR/MG5
  echo "[installer] installing CheckMATE";
  make -j4
	cd $homeDIR
fi



