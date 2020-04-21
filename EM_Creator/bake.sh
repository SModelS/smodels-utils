#!/bin/sh
  
./bake.py -p 5 -t TGQ -m "[(50,4500,200),(50,4500,200),(0.)]" -a --analyses "atlas_susy_2016_07,cms_sus_16_033" -n 10000 --mingap2 0. --mingap13 0. &
./bake.py -p 5 -t TGQ -m "[(750,4500,200),(750,4500,200),(695.)]" -a --analyses "atlas_susy_2016_07,cms_sus_16_033" -n 10000 --mingap2 0. --mingap13 0. &
./bake.py -p 5 -t TGQ -m "[(1050,4500,200),(1050,4500,200),(995.)]" -a --analyses "atlas_susy_2016_07,cms_sus_16_033" -n 10000 --mingap2 0. --mingap13 0. &
./bake.py -a -p 5 -t TGQ --analyses "cms_sus_16_033,atlas_susy_2016_07" -m "[(100,2000,200),(100,2000,200),(50,2000,200)]" -n 10000 --mingap2 0. --mingap13 0. &
./bake.py -p 5 -t TGQ -m "[(50,4500,400),(50,4500,400),(50,3000,400.)]" -a --analyses "atlas_susy_2016_07,cms_sus_16_033" -n 10000 --mingap2 0. --mingap13 0. &
