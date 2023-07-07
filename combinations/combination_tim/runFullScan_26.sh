#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_26',23,'outputFullScan_nlo_2p3_mmg05_26')"
}

callmyprogram

echo $Done
