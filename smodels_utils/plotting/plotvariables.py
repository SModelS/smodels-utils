#!/usr/bin/env python
"""
.. module::	plotvariables
   :synopsis:	contains the vaiables needed to plot a color map (see plotfunction) or a ratio (see ratiofunction).
   The parameters for ROOT-TH2F-Histogram can be set manually here if setth2f == 'manualy' in mapplotter instead of using functionspackage::TH2F_Parameters to set them automatically. 
"""
####################################################
"""
Define the vraiables for both Color- and Ratio-Map. These variables are going to be used in plotfunction and ratiofunction
"""
limits                  = [] # edit here to chnage the limits of the color bar of EffMaps. Otherwise the limits are imported form analysisdicts
ratiolimits		= [0,2] # # edit here to chnage the limits of the color bar of Ratio Maps.

scale_style		='log' # choose 'log' for logarithmed scale or '' for linear

#ratio_maptitle          = 'DELTACharginoSlepton5 over DELTASleptonNeutralino5' # edit here the title of ratio maps

ratio_zaxis_title       = 'RATIO'
ratio_style             = 'bwr' # edit here to change the style of the color palette for ratio-plots (see functionspackage::setpalette)
skip_bincontents        = 1 # edir here to left out some bin-Contents when ploting a ratio-map with the contains of the bins (using Draw('text')) for more clearly overview.   

colormap_zaxis_title    = 'A #times #epsilon'
colormap_style          = '' # edit here to change the style of the color palette for color maps (see functionspackage::setpalette)

xaxis_labelsize         = 0.04
yaxis_labelsize         = 0.05
xaxis_titlesize		= 0.07
yaxis_titlesize		= 0.07
axis_titleoffset        = 1.6
analysis_textsize       = 0.045
analysis_textfont       = 42
model_textsize          = 0.045
model_textfont          = 12
map_titlesize 	        = 0.7
exclusionline_width     = 4
####################################################
"""
Canvas and Pad parameters
"""
canvas_width 	= 1500 #this value fits for all maps
canvas_high 	= 1500 #this value fits for all maps
x_low 		= 0.02 #this value fits for all maps
y_low 		= 0.02 #this value fits for all maps
x_high 		= 0.95 #this value fits for all maps
y_high 		= 0.98 #this value fits for all maps
leftmargin	= 0.25
rightmargin 	= 0.15
bottommargin 	= 0.2
#################################################### TH2F Histogram parameters
"""
for manually setting of the ROOT-TH2F-Histogram-parameters when chosing setth2f == 'manualy' in mapplotter
"""
setnbinsx	=''
setminofxaxis	=''
setmaxofxaxis	=''
setnbinsy	=''
setminofyaxis	=''
setmaxofyaxis	=''
####################################################
"""
Parameters for Analysis not included in the Analysis_Dicts::analysisdicts
"""
setexclusiondir         =''
setmother      		=''
setdaughter		=''
settopo    		=''
setlimits               =[]







