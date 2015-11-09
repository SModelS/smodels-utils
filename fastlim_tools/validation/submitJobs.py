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
    argparser.add_argument('-log', help='log file to store the output', default="log.dat")
    args = argparser.parse_args()    
    
    slhadir = args.dir
    ncore = args.Ncore
    njobs = args.Njobs
    if slhadir[-1] == '/': slhadir = slhadir[:-1]
    
    nfolders = [slhadir + "_job_"+str(i) for i in range(njobs)]
    slhafiles = glob.glob(slhadir+"/*.slha")
    nFilesPerJob = len(slhafiles)/njobs + 1
    nCoresPerJob = ncore/njobs
    islha = 0
    for folder in nfolders:
        if os.path.isdir(folder):
            print 'Error: Folder %s exists' %folder
            sys.exit()
        os.mkdir(folder)
        for ifile in range(islha,islha+nFilesPerJob):
            if ifile >= len(slhafiles): break
            shutil.move(slhafiles[ifile],folder)
        islha += nFilesPerJob
    
    #Submit jobs
    for ijob in range(njobs):
        subprocess.call(["qsub ./singleJob ",nfolders[ijob]," -Ncore "+str(nCoresPerJob), " >> "+args.log])
    sys.exit()
        