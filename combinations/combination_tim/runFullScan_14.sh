#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_14',20,'outputFullScan_nlo_2p3_mmg05_14')"
}

callmyprogram

echo $Done
