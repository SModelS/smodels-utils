#!/usr/bin/env python

"""
.. module:: pythiaCardGen
   :synopsis: Method to generate a process-specific pythia card 

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import tempfile,os
import logging
logger = logging.getLogger(__name__)

def getPythiaCardFor(momPDGs,filename=None):
    """
    Uses the dictionary of pythia processes and generates a pythia card
    to run only production of the process contaning the mother PDGs
    :param momPDGs: list with one or two PDGs. If only one is defined, pair production
                    of the same mother is assumed
    :param filename: Name for the pythia.card file. If no name is defined, a temporary name will be
                     assigned.
    :return: Name of the file generated
    """
    
    if not filename:
        filename = tempfile.mkstemp(prefix="pythia_",suffix=".card",dir=os.getcwd())
        os.close(filename[0])
        filename = filename[1]
    f = open(filename,'w')
    
    #Define initial block:
    header = "! Pythia6 template configuration used when running smodels, for\n\
! the computation of the LO cross sections. \n\
IMSS(1)=11     ! Spectrum from external SLHA file\n\
MSTP(161)=66\n\
MSTP(162)=67\n\
MSTP(163)=68\n\
IMSS(21)=61    ! LUN number for SLHA File\n\
IMSS(22)=61\n\
MSTP(41)=0     ! No decays\n\
MSTP(42)=0     ! no mass smearing (narrow width approximation)\n\
MSTP(81)=0     ! multiple parton interactions 1 is Pythia default\n\
MSTP(61)=0     ! No ISR\n\
MSTP(71)=0     ! No FSR\n\
MSTP(111)=0    ! No hadronization\n\
MSTJ(1)=0      ! No fragmentation\n\
MSEL=0        ! All MSSM processes, except Higgs production\n"
    f.write(header)
    
    #Define the processes to be generated:
    if len(momPDGs) == 1: pids = [[momPDGs[0],momPDGs[0]]]
    else:
        pids=[]
        for ipdg1,pdg1 in enumerate(momPDGs):
            for ipdg2 in range(ipdg1,len(momPDGs)):
                pids.append([pdg1,momPDGs[ipdg2]])
    
    for pid in pids:
        procs = getProcessesFor(pid)
        if not procs: 
            continue
            # return False
        for p in procs:
            f.write("MSUB("+str(p)+")=1\n")
    
    #Write footer:
    footer = "end\nNEVENTS,0,0,SQRTSD0\nend\n"
    f.write(footer)
    f.close()
    return filename

def getProcessesFor(pidPair):
    """
    Using the dictionary of pythia processes, return the production process
    containing both PDGs
    :param pidPair: pair of PDGs (i.e. [1000011,1000011])
    :return: list of msub values
    """
    
    msubDict = [[[1000011,1000011],[201]], [[2000011,2000011],[202]], [[1000011,2000011],[203]],
               [[1000013,1000013],[204]], [[2000013,2000013],[205]], [[1000013,2000013],[206]],
               [[1000015,1000015],[207]], [[2000015,2000015],[208]], [[1000015,2000015],[209]],
               [[1000011,1000012],[210]], [[1000013,1000014],[210]], [[1000015,1000016],[211]],
               [[2000015,1000016],[212]], [[1000012,1000012],[213]], [[1000014,1000014],[213]],
               [[1000016,1000016],[214]], [[1000022,1000022],[216]], [[1000023,1000023],[217]],
               [[1000025,1000025],[218]], [[1000035,1000035],[219]], [[1000022,1000023],[220]],
               [[1000022,1000025],[221]], [[1000022,1000035],[222]], [[1000023,1000025],[223]],
               [[1000023,1000035],[224]], [[1000025,1000035],[225]], [[1000024,1000024],[226]],
               [[1000037,1000037],[227]], [[1000024,1000037],[228]], [[1000022,1000024],[229]],
               [[1000023,1000024],[230]], [[1000025,1000024],[231]], [[1000035,1000024],[232]],
               [[1000022,1000037],[233]], [[1000023,1000037],[234]], [[1000025,1000037],[235]],
               [[1000035,1000037],[236]], [[1000021,1000022],[237]], [[1000021,1000023],[238]],
               [[1000021,1000025],[239]], [[1000021,1000035],[240]], [[1000021,1000024],[241]],
               [[1000021,1000037],[242]], [[1000021,1000021],[243,244]],
               [['sqL',1000022],[246]], [['sqR',1000022],[247]],
               [['sqL',1000023],[248]], [['sqR',1000023],[249]],
               [['sqL',1000025],[250]], [['sqR',1000025],[251]],
               [['sqL',1000035],[252]], [['sqR',1000035],[253]],
               [['sqL',1000024],[254]], [['sqL',1000037],[256]],
               [['sqL',1000021],[258]], [['sqR',1000021],[259]],
               [[1000006,1000006],[261,264]], [[2000006,2000006],[262,265]], [[1000006,2000006],[263]],
               [['sqL','sqL'],[271,274,277,279]], [['sqR','sqR'],[272,275,278,280]], [['sqL','sqR'],[273,276]],
               [[1000005,'sqL'],[281,284]], [[2000005,'sqR'],[282,285]], [[1000005,'sqR'],[283,286]],
               [[2000005,'sqL'],[283,286]],
               [[1000005,1000005],[287,289,291]], [[2000005,2000005],[288,290,292]], [[1000005,2000005],[293,296]],
               [[1000005,1000021],[294]], [[2000005,1000021],[295]]]
    
    ptcDic = {'sqL' : [i for i in range(1000001,1000005)], 'sqR' : [i for i in range(2000001,2000005)]}
    
    #Make sure the PDGs are positive:
    pids = [abs(pidPair[0]),abs(pidPair[1])]
    
    for msub in msubDict:
        pair = msub[0]
        isub = msub[1]
        if set(pair) == set(pids): return isub
        elif isinstance(pair[0],str) and not isinstance(pair[1],str):
            if pids[0] in ptcDic[pair[0]] and pids[1] == pair[1]:
                return isub
            elif pids[1] in ptcDic[pair[0]] and pids[0] == pair[1]:
                return isub 
        elif isinstance(pair[1],str) and not isinstance(pair[0],str):
            if pids[0] in ptcDic[pair[1]] and pids[1] == pair[0]:
                return isub
            elif pids[1] in ptcDic[pair[1]] and pids[0] == pair[0]:
                return isub 
        elif isinstance(pair[0],str) and isinstance(pair[1],str):            
            if pids[0] in ptcDic[pair[0]] and pids[1] in ptcDic[pair[1]]:
                return isub
            elif pids[0] in ptcDic[pair[1]] and pids[1] in ptcDic[pair[0]]:
                return isub
    
    logger.warning("Pythia process for %s not found" %str(pidPair))
#     import sys
#     sys.exit()
    return False
