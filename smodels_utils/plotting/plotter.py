#!/usr/bin/env python
"""
.. module::plotter
     :synopsis: creates a 2D Histogram using ROOT.TH2F()
     :required modules: ROOT, gROOT, numpy, plotvariables, analysisdicts, extractdicts
"""
#Class Plotter():
#===========================================================================
'''
def get_entries(orig_path): 
	"""
	returns from the orig-directory a list of the input files for the ExLine and EffMaps 
	"""
        import os
        listofentries = os.listdir(orig_path)
        listofentries.sort()
        listofmapdirs  = []
        listoflinedirs = []
        for entry in listofentries:
            if '.dat' in entry:
               listofmapdirs.append(entry)
            elif '.txt' in entry:
               listoflinedirs.append(entry)

	return listofmapdirs, listoflinedirs
'''
#================================================================================
#for Data in listData: # see @@
from smodels.tools.physicsUnits import fb, pb, GeV
def get_masses(Data): # TODO ShORT NAMES
	"""
	returns the masses of the mother and daughter particles from "._data" as lists  
	"""                      
        max_mothermass = max(Data)[0][0][0].asNumber()
        min_mothermass = min(Data)[0][0][0].asNumber()
        max_daughtermass = 0
        min_daughtermass = ''
        list_mother_mass = []
        list_daughter_mass = []
        for num in Data:
                for masspoint in num[::2]:
                        for massrange in masspoint:
                            for mother_mass in massrange[0::1]:
                                list_mother_mass.append(mother_mass.asNumber())
                # the loop is written twice for ipython
                #for num in Data:
                    #for masspoint in num[::2]:
                        #for massrange in masspoint:
                            for daughter_mass in massrange[1::1]:
                                list_daughter_mass.append(daughter_mass.asNumber())
                                if daughter_mass.asNumber() >= max_daughtermass: max_daughtermass = daughter_mass.asNumber()
                                if daughter_mass.asNumber() < min_daughtermass : min_daughtermass = daughter_mass.asNumber()
                                
	return max_mothermass, min_mothermass, max_daughtermass, min_daughtermass, list_mother_mass, list_daughter_mass
#================================================================================

def ext_eff(db, Analysis, txName=[], mp=[], dp=[]): # TODO loop over all SR
	"""
	returns a list of all efficiencies "all_eff" and a list of non zero efficiencies "nonz_eff"
	mother parameters::mp = [min_mothermass, max_mothermass, mother_binning]
	daughter parameters::dp = [min_daughtermass, max_daughtermass, daughter_binning]
	"""
	all_eff=[]
	nonz_eff = []

	for xvalue in range(int(mp[0]), int(mp[1]), int(mp[2])):

            for yvalue in range(int(dp[0]), int(dp[1]), int(dp[2])):

                Mass_Point = [  [[xvalue*GeV, yvalue*GeV],[xvalue*GeV, yvalue*GeV]] ] # e.g. Mass_Point = [  [[812.5*GeV, 687.5*GeV],[812.5*GeV, 687.5*GeV]] ]
		from functionspackage import Find_Eff
                #Eff = Tx.getEfficiencyFor(Mass_Point[0])
		Eff = Find_Eff(db, Mass_Point=[], Analysis=[], txName=[])
		all_eff.append(Eff)

                if Eff != 0: nonz_eff.append(Eff)

	return all_eff, nonz_eff
#================================================================================

def set_palette_lim(nonz_eff=[], lim=[]):
	"""
	sets the limits of the color-bar. 
	The Limits of the Colorbar can be either defined manualy by setting the Values of up_lim and low_lim using lim= [low, up] or by chossing the lowest and highest non zero Efficiency
	"""
        low_lim = ''
        up_lim = ''

        try : low_lim = lim[0]
        except : low_lim = min(nonz_eff)
        try : up_lim = lim[1]
        except: up_lim = max(nonz_eff)

	return low_lim, up_lim
#================================================================================

def set_canvas():
	"""
	Sets the parameters for the canvas and the pad
	"""               

        gROOT.SetBatch()#prevent showing the plot during calculation
        
	# TODO move to the top
        from plotvariables import canvas_width, canvas_high, x_low, y_low, x_high, y_high, leftmargin, rightmargin, bottommargin

        canvas	= ROOT.TCanvas('canvas','canvas', canvas_width, canvas_high)

        pad 	= ROOT.TPad('pad1','pad1', x_low, y_low, x_high, y_high)
        pad.SetFrameFillColor(ROOT.kWhite)
        pad.Draw()
        pad.cd()
        pad.SetLeftMargin(leftmargin)
        pad.SetRightMargin(rightmargin)
        pad.SetBottomMargin(bottommargin)
        from plotvariables import scale_style
	if scale_style == 'log':
                pad.SetLogz()

        leg = ROOT.TLegend(0.17, 0.75 ,.42, .88)
        #leg.SetFillColor(ROOT.kGray)
        #pad.SetGrid();

	return canvas, pad, leg
#================================================================================

def call_histo(x_par=[], y_par=[], z_par=[]):
	"""
	creates a 2D histogram using the class ROOT.TH2F
	the parameters of the x-axis are x_par=[values=[nbinsx, minofxaxis, maxofxaxis], list_mother_mass=[]]
	the parameters of the y-axis are y_par=[values=[nbinsy, minofyaxis, maxofyaxis], list_daughter_mass=[]]
	the parameter of the z-axis is the list of Efficiencies z_par=[all_eff]
	"""
	
	mymap = 	ROOT.TH2F('Histo', 'T2HD', x_par[0][0], x_par[0][1], x_par[0][2], y_par[0][0], y_par[0][1], y_par[0][2])

        for x, y, z in zip (x_par[1] , y_par[1], z_par[0]):

		if z <= low_lim: 
			z = low_lim
			print '***The lower limit of the color bar is greater than the smallest efficiency***'
			print 'The efficiency', z, 'is setted to the lower limit', low_lim
		mymap.Fill(x, y, z)
	
	return mymap
#================================================================================

def set_style():
	"""
	sets the style of the color palette
	"""
	from functionspackage import setpalette
	if palettestyle: 
		setpalette(palettestyle[0], ncontours=999)
	else:
		setpalette('mypalette', ncontours=999)#set 'mypalette' as default

#================================================================================

def set_histo(self, maxima=[], minima=[], lim=[], title=''): # self == mymap
	"""
	maxima = [maxofxaxis, maxofyaxis]
	minima = [minofxaxis, minofyaxis]
	lim=[low_lim, up_lim]
	title::string == the title of the map
	"""
	xaxis = self.GetXaxis()
	yaxis = self.GetYaxis()
	zaxis = self.GetZaxis()
	xaxis.SetRangeUser(minima[0], maxima[0]) 
	yaxis.SetRangeUser(minima[1], maxima[1])
	self.SetStats(0)
	self.Draw('COLZ')

	self.SetMinimum(lim[0])
	self.SetMaximum(lim[1])

	from plotvariables import map_titlesize
	self.SetTitle("Signal Region:" + title)
	self.SetTitleSize(map_titlesize)
#================================================================================

def set_exline(orig_path):
	"""
	
	"""
	from plotvariables import exclusionline_width, analysis_textsize
	exclusionline   = orig_path + '/' + ('exclusion'+'_'+model+'.txt')

	from functionspackage import HistoDataProducer
	xline, yline, zline = HistoDataProducer(exclusionline, num=2)
	xline  = np.array(xline)
	yline  = np.array(yline)
	line = ROOT.TGraph(len(xline), xline, yline)
	line.SetLineColor(ROOT.kYellow)
	line.SetLineWidth(exclusionline_width)
	line.Draw('SAME')
#================================================================================

def set_text():
	"""
	
	"""
	from plotvariables import xaxis_titlesize, yaxis_titlesize, xaxis_labelsize, yaxis_labelsize, axis_titleoffset, colormap_zaxis_title, analysis_textsize, analysis_textfont, model_textsize, model_textfont, colormap_zaxis_title              
	xtitle, ytitle = 'xtitle','ytitle' # TODO
	xaxis.SetLabelSize(xaxis_labelsize)
	yaxis.SetLabelSize(yaxis_labelsize)
	yaxis.SetTitleOffset(axis_titleoffset)
	zaxis.SetTitleOffset(axis_titleoffset)
	xaxis.SetTitle(xtitle)
	yaxis.SetTitle(ytitle)
	zaxis.SetTitle(colormap_zaxis_title)
	yaxis.SetTitleSize(yaxis_titlesize)
	xaxis.SetTitleSize(xaxis_titlesize) 

        analysistitle	= ROOT.TLatex(minofxaxis,0.95*maxofyaxis, analysis)
        modeltitle	= ROOT.TLatex(minofxaxis,0.85*maxofyaxis, model)
        
        analysistitle.SetTextSize(analysis_textsize)
        analysistitle.SetTextFont(analysis_textfont)
        analysistitle.Draw("SAME")   
                
        modeltitle.SetTextSize(model_textsize)
        modeltitle.SetTextFont(model_textfont)
        modeltitle.Draw("SAME")

#================================================================================
def save_map(canvas):
	"""
	
	"""
        import os
        workingdir = os.getcwd()
        modelkey = model
        massplane = txName[0] # TODO
        modelname = ''

        from plotvariables import scale_style
        if scale_style == 'log':
                outputdir = workingdir + '/' + ('EM_Output_plotter') + '/' + analysis + '/' + 'logscale' + '/'+ modelname + '/' + massplane
        elif scale_style == '':
                outputdir = workingdir + '/' + ('EM_Output_plotter') + '/' + analysis + '/' + 'linearscale' + '/'+ modelname + '/' + massplane

        if not os.path.exists(outputdir):
		os.makedirs(outputdir)
        canvas.SaveAs(outputdir + '/' + title+ '.png')
        canvas.Close()
#================================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='analysis, model, massplane  - Helper \n '	)
    parser.add_argument('--analysis',	'-a',         help='Anlaysis: ATLAS-2013-04 or ATLAS-2013-11 or CMS-13-012')
    parser.add_argument('--model',          '-m',         help='Model: T5WW or T5ZZ or TSlepSlep or TChipChimSlepSnu'  )
    parser.add_argument('--massplane',	'-p',         help='Mass plane: x or x025 or x05 or x057 or x095 or DELTACharginoSlepton5 or DELTACharginoSlepton10 or DELTACharginoSlepton15 or DELTASleptonNeutralino5 or DELTASleptonNeutralino10 or DELTASleptonNeutralino15' )
    args	= parser.parse_args()
    analysis	= args.analysis
    model 	= args.model                                  
    massplane 	= args.massplane
    run_my_fct(analysis, model, massplane)

#================================================================================


