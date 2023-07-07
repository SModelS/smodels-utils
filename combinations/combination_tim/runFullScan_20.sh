#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_20',23,'outputFullScan_nlo_2p3_mmg05_20')"
}

callmyprogram

echo $Done
