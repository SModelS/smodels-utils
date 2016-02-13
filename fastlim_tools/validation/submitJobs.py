#!/usr/bin/env python

"""
.. module:: runFiles
   :synopsis: Used to submit several jobs in the cluster

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""
import sys,os,glob,shutil
import argparse,subprocess

if __name__ == "__main__":
    
    argparser = argparse.ArgumentParser(description='Submit several jobs using qsub')
    argparser.add_argument('dir', help='name of SLHA folder containing the SLHA files')
    argparser.add_argument('-Ncore', help='total number of cores to be used', type=int, default=1)
    argparser.add_argument('-Njobs', help='total number of jobs to be submitted', type=int, default=1)
    argparser.add_argument('-twall', help='walltime for each job (in hours)', type=int, default=2)
    argparser.add_argument('-log', help='log file to store the output', default="log.dat")
    argparser.add_argument('-Tool', help='Tool to be used (fastlim/smodels)', required=True)
    args = argparser.parse_args()    
    
    slhadir = args.dir
    ncore = args.Ncore
    njobs = args.Njobs
    slhadir  = os.path.abspath(slhadir)
    if slhadir[-1] == '/': slhadir = slhadir[:-1]
    
    slhafiles = glob.glob(slhadir+"/*.slha")
    nFilesPerJob = len(slhafiles)/njobs + 1
    nCoresPerJob = max(1,ncore/njobs)
    islha = 0
    nfolders = []
    for ijob in range(njobs):
        folder = slhadir + "_"+args.Tool+"Job_"+str(ijob)
        if os.path.isdir(folder):
            print 'Error: Folder %s exists' %folder
            sys.exit()
        if folder[:7] == '/export':
            folder = folder[7:]
        os.mkdir(folder)
        nfolders.append(folder)
        for ifile in range(islha,islha+nFilesPerJob):
            if ifile >= len(slhafiles): break
            shutil.copy(slhafiles[ifile],folder)
        islha += nFilesPerJob
    
    #Submit jobs
    for ijob in range(njobs):
        with open('subJob'+args.Tool+str(ijob),'w') as jobscript:
            jobscript.write("#PBS -S /bin/bash\n\
#PBS -l walltime=%d:00:00\n\
#PBS -l procs=%d\n\
#PBS -N %s\n\
#PBS -e %s/err.log\n\
#PBS -o %s/log.out\n\
\n\
./singleJob.py %s -Ncore %d -Tool %s >> %s/%s \n" %(args.twall,nCoresPerJob,nfolders[ijob],nfolders[ijob],
                                                                'subJob'+args.Tool+str(ijob),
                                                                nfolders[ijob],nCoresPerJob,args.Tool,
                                                                nfolders[ijob],args.log))

        subprocess.call("qsub subJob"+args.Tool+str(ijob),shell=True)
    sys.exit()
        
