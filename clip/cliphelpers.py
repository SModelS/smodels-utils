#!/usr/bin/env python3

""" various helper functions around the clip cluster that do not fit in any of
the more specific modules """

from typing import Union
import os
import subprocess

def readJobIds():
    """ read the job ids from jobs files """
    jobids = set()
    if not os.path.exists ( "jobs" ):
        return jobids
    with open ( "jobs", "rt" ) as f:
        lines = f.readlines()
    for line in lines:
        jobid = int ( line.strip() )
        jobids.add ( jobid )
    return jobids

def getJobStatus  ( jobids : Union[list,int] ) -> dict:
    """ get the status of one or more slurm jobs 

    :returns: dictionary with jobids as keys and status as values
    """
    if type(jobids) in [ list, tuple, set ]:
        ret = {}
        for jobid in jobids:
            js = getJobStatus ( jobid)
            ret[jobid] = js[jobid]
        return ret
    cmd = f"sacct --job {jobids}"
    output = subprocess.getoutput ( cmd ).split("\n")
    if len(output)<2:
        output = f"fewer than two lines?? {output}"
    else:
        output = output[2]
        if len(output)<73:
            output = f"fewer than 73 characters?? {output}"
        else:
            output = output[60:73]
    
    output = output.strip()
    output = output.lower()
    return { jobids: output }

    """ jobinfo
    cmd = f"jobinfo {jobids}"
    output = subprocess.getoutput ( cmd ).split("\n")
    ret = "undefined"
    for line in output:
        if "State" in line:
            ret = line.replace("State","")
            ret = ret.strip()
            ret = ret[2:]
            ret = ret.lower()
            return { jobids: ret }
    return { jobids: ret }
    """

def describeSet( inp : list ) -> str:
    """ describe a given set of indices in compact form. e.g.
    [1,2,3,5] -> "1-3,5"

    returns: a string describing the indices
    """
    s = set()
    for i in inp:
        s.add(int(i))
    # return str( s )
    ret = ""
    firstIndex = s.pop() ## enter first element
    lastIndex = firstIndex
    for i in s:
        if i == lastIndex+1:
            lastIndex=i
        else:
            ret += f"{int(firstIndex)}-{int(lastIndex)}, "
            firstIndex = i
            lastIndex= i
    ret += f"{int(firstIndex)}-{int(lastIndex)}"
    return ret
