#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo_13',10,'outputFullScan_nlo_2p3_mmg05_13')"
}

callmyprogram

echo $Done
