#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_15',20,'outputFullScan_nlo_2p3_mmg05_15')"
}

callmyprogram

echo $Done
