#!/bin/sh

./slhaCreator.py -t T6bbHH -a "2*[[x,y,60]]" --xmin 250. --xmax 1850. --ymin 150. --ymax 1650. --dx 100. --dy 100. --no_xsecs

./slhaCreator.py -t T6bbHH -a "2*[[x,y+130.,y]]" --xmin 250. --xmax 1550. --ymin 150. --ymax 1350. --dx 100. --dy 100. --no_xsecs
