#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_28',23,'outputFullScan_nlo_2p3_mmg05_28')"
}

callmyprogram

echo $Done
