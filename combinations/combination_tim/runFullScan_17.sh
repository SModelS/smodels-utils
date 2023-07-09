#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan;runFullScan.main('2ndFilter_slha_nlo/2ndFilter_slha_nlo_mmg10/2ndFilter_slha_nlo_mmg10_17',25,'outputFullScan_nlo_2p3_mmg10_17')"
}

callmyprogram

echo $Done
