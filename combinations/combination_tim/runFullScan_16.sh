#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_16',25,'outputFullScan_nlo_2p3_mmg05_16')"
}

callmyprogram

echo $Done
