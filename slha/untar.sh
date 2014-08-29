#!/bin/sh

<<EOF
.. module:: untar.sh
   :synopsis: super simple script that untars all tarballs

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

EOF

for i in `ls *.tar`; do
	tar xvf $i;
done
