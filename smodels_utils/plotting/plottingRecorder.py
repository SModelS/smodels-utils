#!/usr/bin/env python3

"""
.. module:: plottingRecorder
   :synopsis: class to record matplotlib plottings, so we can tweak

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

class FunctionWrapper:
    """ this is a class that intercepts calls to 'callable',
    and returns the string of the function call, verbatim
    """
    def __init__(self, parent, _callable, prefix : str = "plt" ):
        self.parent = parent
        self.callable = _callable
        self.prefix = prefix
        self.verbose = False

    def pprint ( self, line : str ):
        if self.verbose:
            print ( f"[Wrapper] {line}" )

    def __call__(self, *args, **kwargs):
        self.pprint ( f"{self.callable.__name__}({args}){kwargs}" )
        #if self.callable.__name__ == "pcolormesh":
        #    import IPython; IPython.embed()
        import numpy as np
        f = self.parent.recordingfile
        s_args = ""
        for a in args:
            if "matplotlib" in str(type(a)):
                self.pprint ( f"skipping {a}" )
                continue
            if len(s_args):
                s_args += ","
            if type(a) == str:
                a = f"'{a}'"
            if type(a) in [  np.array, np.ndarray ]:
                a=list(a)
            a = str(a)
            a = a.replace("nan","np.nan" )
            for l in [ "r", "t", "n", "l", "b" ]:
                a = a.replace( rf"\{l}", f"\\\\{l}" )
            s_args += a
        for k,v in kwargs.items():
            if "matplotlib.colors.LinearSegmentedColormap" in str(v):
                s_args += f",{k}=getColormap()"
                continue
            if "transform" in k:
                s_args += f",transform=fig.transFigure"
                continue
            #if "matplotlib" in str(type(v)):
            #    print ( "v", v )
            #    continue
            if len(s_args):
                s_args += ","
            s_args += f"{k}="
            if type(v)==str:
                s_args += f"'{str(v)}'"
            else:
                s_args += f"{str(v)}"
        prefix = self.prefix
        if self.prefix == "<<backspace>>":
            f.seek(f.tell() - 1)
            f.truncate()
            prefix = ""
        line = f"{prefix}.{self.callable.__name__}({s_args})\n"
        if "savefig" in line:
            line = "from smodels_utils.helper.various import pngMetaInfo\n"
            line += "metadata = pngMetaInfo()\n"
            line += "plt.savefig('recorded.png',metadata=metadata)\n"
        if "plt.gcf()" in line:
            line = "fig=plt.gcf()\n"
        if "plt.gca()" in line:
            line = "ax=plt.gca()\n"
        if "plt.subplots()" in line:
            line = "fig,ax=plt.subplots()\n"
        f.write ( line )
        ret = self.callable(*args, **kwargs)
        self.parent.callable_results.append(ret)
        if "matplotlib" in str(type(ret)):
            ret = Interceptor ( ret, "<<backspace>>" )
            ret.recordingfile = f
            ret.callable_results = self.parent.callable_results
            return ret
        return ret

class Interceptor:
    def __init__ ( self, obj, prefix : str = "plt" ):
        self.obj = obj
        self.prefix = prefix

    def __getattr__(self, attr):
        # print("@@ Getting {0}.{1}".format(type(self.obj).__name__, attr))
        ret = getattr(self.obj, attr)
        if hasattr(ret, "__call__"):
            return FunctionWrapper(self, ret, self.prefix )
        return ret

class Recorder ( Interceptor ):
    """ a wrapper class that records the function calls, stores
        thme in recorder.py """
    def __init__(self, obj, importColorMap : bool = True,
                  outputfile : str = "recorder.py" ):
        super ( Recorder, self ).__init__( obj )
        import time
        self.recordingfilename = outputfile
        self.recordingfile = open ( self.recordingfilename, "wt" )
        self.recordingfile.write ( "#!/usr/bin/env python3\n" )
        self.recordingfile.write ( "#\n" )
        self.recordingfile.write ( "# a python script that recorded the plotting statements,\n" )
        self.recordingfile.write ( "# so we can re-plot\n" )
        self.recordingfile.write ( f"# this file was created {time.asctime()}\n" )
        self.recordingfile.write ( "\n" )
        self.recordingfile.write ( "from matplotlib import pyplot as plt\n" )
        if importColorMap:
            self.recordingfile.write ( "from plottingFuncs import getColormap\n" )
        # from matplotlib.transforms import BboxTransformTo, TransformedBbox, Bbox
        self.recordingfile.write ( "import numpy as np\n" )
        self.recordingfile.write ( "from numpy import array\n" )
        self.recordingfile.write ( "\n" )
        self.recordingfile.write ( "# recorded code start here\n" )
        self.callable_results = []

    def intercept ( self, obj, prefix : str ):
        """ intercept calls to obj """
        ret = Interceptor ( obj, prefix )
        ret.recordingfile = self.recordingfile
        ret.callable_results = self.callable_results
        return ret

    def closeFile ( self ):
        self.recordingfile.close()
        import os
        os.chmod ( self.recordingfilename, 0o755 )

def importMatplot ( record : bool, importColorMap : bool = True ):
    """ import matplotlib
    :param record: if true, then wrap the module into a recorder class.
                   this class will create a recorder.py script
    """
    if not record:
        import matplotlib.pylab as plt
        return plt
    import matplotlib.pylab as actualplt
    plt = Recorder ( actualplt, importColorMap = importColorMap )
    import atexit
    atexit.register ( plt.closeFile )
    return plt


