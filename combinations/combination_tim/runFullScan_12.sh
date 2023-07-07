#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_12',10,'outputFullScan_nlo_2p3_mmg05_12')"
}

callmyprogram

echo $Done
