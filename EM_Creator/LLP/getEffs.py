#!/usr/bin/env python

#Reads a series of data files  with the (isolated) HSCP momentum information for each event (in the stable limit)
#and extract an efficiency map for all the points, including the effect of finite width.

import sys
from configparser import SafeConfigParser,ExtendedInterpolation
import logging
import time
import os
import multiprocessing
import numpy as np
import math,glob



FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s at %(asctime)s'
logging.basicConfig(format=FORMAT,datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)


class Particle(object):

    def __init__(self,**kargs):

        for key,val in kargs.items():
            setattr(self,key,val)

    def GetPdgCode(self):

        return self.pdg

    def fourMom(self):

        return [self.energy] + self.triMommentum

    def triMom(self):

        return self.triMomentum

    def Eta(self):
        pmom = self.P()
        fPz = self.fourMom()[3]
        if pmom != abs(fPz):
            return 0.5*np.log((pmom+fPz)/(pmom-fPz))
        else:
            return 1e30

    def P(self):

        return math.sqrt(self.triMomentum[0]**2 + self.triMomentum[1]**2 + self.triMomentum[2]**2)

    def Energy(self):

        return self.energy

    def GetCalcMass(self):

        if hasattr(self,'mass'):
            return self.mass
        else:
            mass = np.sqrt(np.inner(self.fourMom(),self.fourMom()))
            return mass

def  getEffForEvent(event,xEffs=None):
    """
    Compute the efficiency for the event for a given
    list of x-values (xEffs), where x = L/ctau.
    Only uses the maximal signal region/mass reconstruction satisfying m_hscp < mrec/0.6.

    :param event: List with Particle objects containing efficiencies
    :param xEffs: list of float with the effective values for L/ctau to rescale the events for.
                  If None, will return the unrescaled efficiency (zero width).

    :return: numpy array with a list of rescaled efficiencies for each value of x in xEff.
    """


    #Number of particles:
    npart = len(event)
    if npart < 1:
        logger.error("Can not handle events with no particles")
        raise ValueError("%s" %str(event))
    if (npart > 2):
        logger.error("Can not handle more than 2 particles per event")
        raise ValueError("%s" %str(event))


    #Trigger probabilities and error:
    ProbTrigger = [0.]*2
    #Online probabilities and error for each signal region/mass cut:
    ProbOnline = [0.]*2
    #Compute zero-width efficiencies:
    mrec = [0,100.,200.,300.]     #Use only maximum mass cut
    for i,p in enumerate(event):
        irec = int(math.floor(p.mass*0.6/100.))
        irec = min(irec,len(mrec)-1)
        ProbTrigger[i] = p.effs[0]
        ProbOnline[i] = p.effs[irec+1]

    #Efficiency if both particles decay outside:
    eff12 = ProbTrigger[0]*(1-ProbTrigger[1]) + ProbTrigger[1]*(1-ProbTrigger[0]) + ProbTrigger[0]*ProbTrigger[1]
    eff12 *= ProbOnline[0]*(1-ProbOnline[1]) + ProbOnline[1]*(1-ProbOnline[0]) + ProbOnline[0]*ProbOnline[1]

    #Efficiency if only the first one decays outside:
    eff1only = ProbTrigger[0]*ProbOnline[0]
    #Efficiency if only the second one decays outside:
    eff2only = ProbTrigger[1]*ProbOnline[1]

    if xEffs is None:
        return eff12

    #Now comput the fraction of particles which survive each part of the detector.
    #For each particle, get fraction which crossed a distance L:
    FL = []
    for x in xEffs:
        evtFL = [0.]*2
        for ip,particle in enumerate(event):
            evtFL[ip] = math.exp(-particle.mass*x/particle.P()) #Compute fraction of long-lived
        FL.append(tuple(evtFL))

    FL = np.array(FL,dtype=[('F1',float),('F2',float)])
    F12 = FL['F1']*FL['F2']
    F1only = FL['F1']*(1-FL['F2'])
    F2only = FL['F2']*(1-FL['F1'])


    eventEff = F12*eff12 + F1only*eff1only + F2only*eff2only

    return eventEff

def getEventsFrom(infile,useEffs=False):
    """
    Reads a simplified LHE file and returns a list of events.
    Each event is simply a list of TParticle objects.

    :param infile: Path to the input file
    :param useEffs: If useEffs = True, includes the event efficiencies. If False, set efficiencies to 1.

    :return: list of events (e.g. [ [ TParticle1, TParticle2,..], [ TParticle1,...]  ])
    """

    if not os.path.isfile(infile):
        logger.error("File %s not found" %infile)
        return []

    f = open(infile,'r')
    events = f.read()
    events = events[events.find('<event>'):events.rfind('<\event>')]
    events = events.split('<event>')[1:]
    eventList = []
    f.close()
    for i,event in enumerate(events[:]):
        evLines = [l for l in event.split('\n') if l]
        particles = []
        for l in evLines[2:-1]:
            l = l.replace('\n','').replace('+-','')
            l = l.split()
            l = [float(x) for x in l]
            pData = l[:6]
            triMomentum = [pData[1],pData[2],pData[3]]
            energy =  pData[4]
            pdg = int(pData[0])
            mass = pData[5]
            if pdg > 0:
                name = "hscp"
                charge = 1.
            else:
                name = "~hscp"
                charge = -1.
            particle = Particle(pdg=pdg,triMomentum=triMomentum,energy=energy,mass=mass,name=name,charge=charge)
            if useEffs:
                particle.effs = [l[i] for i in range(6,15,2)]
                particle.effErrors = [l[i] for i in range(7,16,2)]
            else:
                particle.effs = [1.,1.] #Offline and Online probabilities
                particle.effErrors = [0.,0.] #Offline and Online probabilities errors

            particles.append(particle)

        eventList.append(particles)

    return eventList

def getEffsFor(lheFile,widths,detectorLength,outFolder):
    """
    Compute the efficiencies for a list of widths
    using the events and efficiencies stored in the lheFile (for zero width).

    :param lheFile: path to the LHE file with efficiencies for zero widths
    :param widths: list of widths (in GeV) to compute the efficiency for
    :param detectorLength: fixed detector length size (in meters)
    :param outFolder: output folder

    :return: True/False
    """

    if not os.path.isfile(lheFile):
        logger.error('File %s not found' %lheFile)
        return False

    inputFile = lheFile
    if lheFile.endswith(".tar.gz"):
        tar = tarfile.open(lheFile, "r:gz")
        tar.extractall()
        tar.close()
        inputFile = lheFile.replace('.tar.gz','')
    elif fname.endswith(".tar"):
        tar = tarfile.open(fname, "r:")
        tar.extractall()
        tar.close()
        inputFile = lheFile.replace('.tar','')

    events = getEventsFrom(inputFile, useEffs=True)
    invCtau = np.array(widths)/1.975e-16
    xEffs = invCtau*detectorLength

    zeroEff = 0.
    rescaledEff = np.array([0.]*len(xEffs))
    zeroEffErr = 0.
    rescaledEffErr = np.array([0.]*len(xEffs))
    for event in events:
        if not event:
            continue  #Skip events without HSCPs


        #Get efficiency for zero width
        zeff = getEffForEvent(event,None)
        zeroEff += zeff
        zeroEffErr += zeff**2
        #Get rescaled efficiency
        reff = getEffForEvent(event,xEffs)
        rescaledEff += reff
        rescaledEffErr += reff**2

    zeroEffErr = np.sqrt(zeroEffErr)
    rescaledEffErr = np.sqrt(rescaledEffErr)
    LLPfraction = rescaledEff/zeroEff
    LLPfractionErr = LLPfraction*np.sqrt((rescaledEffErr/rescaledEff)**2 + (zeroEffErr/zeroEff)**2)

    res = np.array(zip(widths,LLPfractions,LLPfractionsErr),dtype=[('width',float),('eff',float),('effError',float)])
    res = np.sort(res,order='width')

    outFile = os.path.join(outFolder,inputFile.replace('.lhe','')+'.eff')
    #Save results to file:
    header = '%19s'*len(res.dtype.names) %res.dtype.names
    header = header[3:]
    np.savetxt(outFile,res,header=header,fmt = ['     %1.7e']*len(res.dtype.names))

    return True


if __name__ == "__main__":

    import argparse
    ap = argparse.ArgumentParser( description=
            "Compute effective fraction of long-lived particles" )
    ap.add_argument('-p', '--parfile', default='fraction_parameters.ini',
            help='path to the parameters file.')
    ap.add_argument('-v', '--verbose', default='error',
            help='verbose level (debug, info, warning or error). Default is error')


    t0 = time.time()

    args = ap.parse_args()

    level = args.verbose.lower()
    levels = { "debug": logging.DEBUG, "info": logging.INFO,
               "warn": logging.WARNING,
               "warning": logging.WARNING, "error": logging.ERROR }
    if not level in levels:
        logger.error ( "Unknown log level ``%s'' supplied!" % level )
        sys.exit()
    logger.setLevel(level = levels[level])

    parser = SafeConfigParser( inline_comment_prefixes=( ';', ))
    parser.optionxform = str
    parser._interpolation = ExtendedInterpolation()
    ret = parser.read(args.parfile)
    if ret == []:
        logger.error( "No such file or directory: '%s'" % args.parfile)
        sys.exit()

    lheFiles = eval(parser.get("options","lheFiles"))
    outFile = parser.get("options","outFile")
    widths = np.array(eval(parser.get("options","widths")))
    detectorLength = eval(parser.get("options","detectorLength"))
    ncpus = parser.getint("options","ncpu")
    if ncpus  < 0:
        ncpus =  multiprocessing.cpu_count()

    ncpus = min(ncpus,len(lheFiles))
    pool = multiprocessing.Pool(processes=ncpus)
    children = []
    #Loop over model parameters and submit jobs
    for lheFile in lheFiles:
        p = pool.apply_async(getLLPFraction, args=(lheFile,widths,detectorLength,))
        children.append(p)

    #Wait for jobs to finish:
    output = [p.get() for p in children]

    print("\n\nDone in %3.2f min" %((time.time()-t0)/60.))
