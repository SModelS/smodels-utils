#!/bin/sh

"""
.. module:: untar.sh
   :synopsis: super simple script that untars all tarballs

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

for i in `ls *.tar`; do
	tar xvf $i;
done
