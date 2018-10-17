#!/bin/bash

if [ "$1" == "" ]; then
	echo "supply txname"; exit;
fi

tar czvf $1.tar.gz $1*slha
