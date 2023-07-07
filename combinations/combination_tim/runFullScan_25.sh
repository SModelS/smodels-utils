#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_25',23,'outputFullScan_nlo_2p3_mmg05_25')"
}

callmyprogram

echo $Done
