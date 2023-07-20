#!/bin/bash

source ~/.bashrc

callmyprogram(){
  python -i -c "import runFullScan_mmg10;runFullScan_mmg10.main('2ndFilter_slha_nlo/2ndFilter_slha_nlo_mmg10/2ndFilter_slha_nlo_mmg10_24',23,'outputFullScan_nlo_2p3_mmg10_24')"
}

callmyprogram

echo $Done
