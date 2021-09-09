#import sys
#sys.path.insert(0,".")
# import matplotlib-backend-kitty
def importBackend():
    import matplotlib, os, sys, subprocess
    from smodels_utils import SModelSUtils
    home = os.environ["HOME"]
    ver = sys.version[:3]
    path = f"{home}/.local/lib/python{ver}/site-packages/"
    name = "matplotlib-backend-kitty"
    if not os.path.exists ( os.path.join ( path, name ) ):
        cmd = f"mkdir -p {path}"
        subprocess.getoutput ( cmd )
        sourcedir = os.path.join ( SModelSUtils.installDirectory(), "smodels_utils", "plotting" )
        o = cmd = f"cp -r {sourcedir}/{name} {path}"
        subprocess.getoutput ( cmd )

    matplotlib.use('module://matplotlib-backend-kitty')

importBackend()
import matplotlib.pyplot as plt
from matplotlib.pyplot import *
