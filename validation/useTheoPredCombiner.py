#!/usr/bin/env python3

"""
.. module:: useTheoPredCombiner
   :synopsis: contains the code that replaces validationObjs:getDataFromPlanes,
              runs theoryPredictionsCombiner over it. To use it, overwrite
              ValidationPlot.getDataFromPlanes with the method below.

"""


import logging, tempfile, time
logger = logging.getLogger(__name__)
import validationObjs

class ValidationPlot( validationObjs.ValidationPlot ):
    def getDataFromPlanes(self):
        """
        Runs SModelS on the SLHA files from self.slhaDir and store
        the relevant data in self.data.
        Uses runSModelS.main.
        """
        logger.error ( "using useTheoPredCombiner override method!" )

        #Get list of SLHA files:
        if not self.slhaDir:
            logger.warning("SLHA folder not defined")
            return False
        slhaDir = self.getSLHAdir()  #Path to the folder containing the SLHA files
        logger.debug("SLHA files for validation at %s" %slhaDir)

        from smodels.tools import modelTester
        #Get list of input files to be tested
        try:
            fileList, inDir = modelTester.getAllInputFiles(slhaDir)
        except Exception: ## old version?
            fileList = modelTester.getAllInputFiles(slhaDir)
            inDir = slhaDir


        #Set temporary outputdir:
        outputDir = tempfile.mkdtemp(dir=slhaDir,prefix='results_')

        #Get parameter file:
        parameterFile = self.getParameterFile(tempdir=outputDir)
        logger.info("SLHA dir %s" % self.slhaDir )
        logger.info("Parameter file: %s" %parameterFile)
        # print ("Parameter file: %s" %parameterFile)

        from smodels.tools import modelTester
        #Read and check parameter file, exit parameterFile does not exist
        parser = modelTester.getParameters(parameterFile)

        #Select the desired experimental result
        listOfExpRes = [self.expRes]

        t0=time.time()
        """ Test all input points """
        modelTester.testPoints(fileList, inDir, outputDir, parser, 'validation',
                 listOfExpRes, 5000, False, parameterFile)
        dt=(time.time()-t0) / len(fileList) ## for now we just write out avg time

        #Define original plot
        massPlane = MassPlane.fromString(self.txName,self.axes)
        if massPlane == None:
            logger.error ( "no mass plane!" )
            return False
        #Now read the output and collect the necessary data
        self.data = []
        slhafiles= os.listdir(slhaDir)
        ct_nooutput=0
        slhafiles.sort() ## make sure we also go in the same order
        myglobals = globals()
        myglobals["inf"]=float("inf")
        myglobals["nan"]=float("nan")
        for slhafile in slhafiles:
            if not os.path.isfile(os.path.join(slhaDir,slhafile)):  #Exclude the results folder
                continue
            fout = os.path.join(outputDir,slhafile + '.py')
            if not os.path.isfile(fout):
                if ct_nooutput>4:
                    ## suppress subsequently same error messages
                    continue
                logger.error("No SModelS output found for %s (should be %s)" % \
                              ( slhafile, fout ) )
                ct_nooutput+=1
                if ct_nooutput==5:
                    logger.error("did not find SModelS output 5 times subsequently. Will quench error msgs from now on.")
                continue
            # print ( "reading %s" % fout )
            ff = open(fout,'r')
            txt = ff.read()
            cmd = txt.replace('\n','') # .replace("inf,","float('inf'),")
            exec( cmd, myglobals )
            ff.close()
            if not 'ExptRes' in smodelsOutput:
                logger.debug("No results for %s " %slhafile)
                ## still get the masses from the slhafile name
                axes = self.getXYFromSLHAFileName ( slhafile, asDict=True )
                ## log also the errors in the py file
                Dict = { 'slhafile': slhafile, 'error': 'no results', 'axes': axes }
                self.data.append ( Dict )
                continue
            res = smodelsOutput['ExptRes']
            expRes = res[0]
            #Double checks (to make sure SModelS ran as expected):
            leadingDSes = {}
            if len(res) != 1:
                logger.debug("Wait. We have multiple dataset Ids. Lets see if there is a combined result." )
                found_combined=False
                for eR in res:
                    if "combined" in eR["DataSetID"]:
                        logger.debug ( "found a combined result. will use it." )
                        found_combined=True
                        expRes = eR
                if self.options["keepTopNSRs"] not in [ None, 0 ]:
                    maxR, expRes = -1., None
                    for eR in res:
                        if "r_expected" in eR:
                            r = eR["r_expected"]
                            while r in leadingDSes: # make sure it's unique
                                r = r * .9999
                            leadingDSes[r]=eR["DataSetID"]
                            if r>maxR:
                                maxR = eR["r_expected"]
                                expRes = eR
                if not found_combined and self.options["keepTopNSRs"] in [ None, 0 ]:
                    logger.warning("We have multiple dataset ids, but none is a combined one. Dont know what to do." )
                    return False
            if expRes['AnalysisID'] != self.expRes.globalInfo.id:
                logger.error("Something went wrong. Obtained results for the wrong analyses")
                return False
            if self.txName != expRes['TxNames'][0] or len(expRes['TxNames']) != 1:
                logger.error("Something went wrong. Obtained results for the wrong txname")
                return False

            #Replaced rounded masses by original masses
            #(skip rounding to check if mass is in the plane)
            roundmass = expRes['Mass (GeV)']
            """
            width = copy.deepcopy ( roundmass )
            for ib,br in enumerate(width):
                for ic,w in enumerate(br):
                    width[ib][ic]=None
            """
            width = None
            if "Width (GeV)" in expRes:
                width = expRes['Width (GeV)']
            #print ( "roundmass", slhafile, roundmass )
            #print ( "expRes", expRes )
            if roundmass is None or "TGQ12" in slhafile:
                ## FIXME, for TGQ12 why cant i use exptres?
                import inspect
                frame = inspect.currentframe()
                line = frame.f_lineno
                #print ( "roundmass is not given in validationObjs.py:%s" % line )
                #print ( "we try to extract the info from the slha file name %s" % \
                #        slhafile )
                roundmass = self.getMassesFromSLHAFileName ( slhafile )
            # print ( "after", slhafile, roundmass )
            mass = [br[:] for br in roundmass]
            slhadata = pyslha.readSLHAFile(os.path.join(slhaDir,slhafile))
            origmasses = list(set(slhadata.blocks['MASS'].values()))
            for i,br in enumerate(mass):
                for im,m in enumerate(br):
                    for omass in origmasses:
                        if round(omass,1) == m:
                            mass[i][im] = omass
                            break

            #print ( "get xy", mass, width )
            varsDict = massPlane.getXYValues(mass,width)
            #print ( "varsdict", varsDict )
            if varsDict is None:
                logger.debug( "dropping %s, doesnt fall into the plane of %s." % \
                               (slhafile, massPlane ) )
                continue
            Dict = {'slhafile' : slhafile, 'axes' : varsDict, 't': dt,
                    'signal': expRes['theory prediction (fb)'],
                    'UL': expRes['upper limit (fb)'], 'condition': expRes['maxcond'],
                    'dataset': expRes['DataSetID'] }
            if len(leadingDSes)>1:
                s = []
                n = self.options["keepTopNSRs"]
                for k,v in sorted ( leadingDSes.items(), reverse=True )[:n]:
                    s.append ( (k,v) )
                Dict["leadingDSes"]= s
            if "l_max" in expRes and "likelihood" in expRes:
                import math
                ratio = 1.
                if expRes["l_max"]>0.:
                    ratio =  expRes["likelihood"] / expRes["l_max"]
                elif expRes["likelihood"]>0.:
                    ratio = float("inf")
                if ratio <= 0.:
                    ratio=1e-90
                Dict["chi2"] = -2*math.log ( ratio )
            if 'expected upper limit (fb)' in expRes:
                Dict['eUL']=expRes["expected upper limit (fb)"]
                drawExpected = self.options["drawExpected"]
                if drawExpected == "auto":
                    drawExpected = True
                self.options["drawExpected"]=drawExpected
            if "efficiency" in expRes.keys():
                Dict["efficiency"] = expRes['efficiency']
            if expRes['dataType'] == 'efficiencyMap':
                #Select the correct dataset (best SR):
                dataset = [dset for dset in self.expRes.datasets if dset.dataInfo.dataId == expRes['DataSetID']]
                if len(dataset)==1:
                    dataset = dataset[0]
                else: ## probably the combined case. we take any dataset.
                    dataset = self.expRes.datasets[0]

                txname = [tx for tx in dataset.txnameList if tx.txName == expRes['TxNames'][0]][0]
                mnw=[]
                if width == None:
                    mnw = mass
                else:
                    for bm,bw in zip(mass,width):
                        br=[]
                        for m,w in zip(bm,bw):
                            br.append( (m,w) )
                        mnw.append(br)
                massGeV = addUnit ( mnw, GeV )
                if not "efficiency" in Dict.keys():
                    try:
                        Dict['efficiency'] = txname.txnameData.getValueFor(massGeV)
                    except SModelSError as e:
                        logger.error ( "could not handle %s: %s" % ( slhafile, e ) )
                        Dict=None
            logger.debug('expres keys : {}'.format(expRes.keys()))
            if 'best combination' in expRes.keys():
                Dict['best combination'] = expRes['best combination']

            if Dict:
                self.data.append(Dict)

        #Remove temporary folder
        if slhaDir != self.slhaDir and not self.keep: shutil.rmtree(slhaDir)

        if self.data == []:
            logger.error("There is no data for %s/%s/%s.\n Are the SLHA files correct? Are the constraints correct?"
                          %(self.expRes.globalInfo.id,self.txName,self.axes))

        #Apply k-factors to theory prediction (default is 1)
        for ipt,pt in enumerate(self.data):
            if "error" in pt.keys():
                continue
            pt['signal'] *= self.kfactor
            self.data[ipt] = pt
            self.data[ipt]['kfactor'] = self.kfactor

