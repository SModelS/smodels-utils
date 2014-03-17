"""
.. module:: moreHelpers
    :synopsis: more helper classes and functions.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

def nCPUs():
  """ obtain the number of CPU cores on the machine, for several
      platforms and python version. FIXME currently not used. """
  try:
    import multiprocessing                                                                return multiprocessing.cpu_count()
  except Exception,e:                                                                     pass
  try:                                                                                    import psutil
    return psutil.NUM_CPUS
  except Exception,e:
    pass
  try:
    import os
    res = int(os.sysconf('SC_NPROCESSORS_ONLN'))
    if res>0: return res
  except Exception,e:
    pass
  return None

