#!/usr/bin/env python3

"""
.. module:: plottingRecorder
   :synopsis: class to record matplotlib plottings, so we can tweak

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

class Recorder:
    """ a wrapper class that records the function calls, stores
        thme in recorder.py """
    def __init__(self, obj, importColorMap : bool = True ):
        self.recordingfilename = "recorder.py"
        self.recordingfile = open ( self.recordingfilename, "wt" )
        self.recordingfile.write ( "#!/usr/bin/env python3\n" )
        self.recordingfile.write ( "#\n" )
        self.recordingfile.write ( "# a python script that recorded the plotting statements,\n" )
        self.recordingfile.write ( "# so we can reproduce the plotting\n\n" )
        self.recordingfile.write ( "from matplotlib import pyplot as plt\n" )
        if importColorMap:
            self.recordingfile.write ( "from plottingFuncs import getColormap\n" )
        # from matplotlib.transforms import BboxTransformTo, TransformedBbox, Bbox
        self.recordingfile.write ( "import numpy as np\n" )
        self.recordingfile.write ( "from numpy import array\n" )
        self.recordingfile.write ( "\n" )
        self.recordingfile.write ( "# recorded code start here\n" )
        self.obj = obj
        self.callable_results = []
        self.obj.subplots()
        self.fig, self.ax = self.obj.subplots()

    def closeFile ( self ):
        self.recordingfile.close()
        import os
        os.chmod ( self.recordingfilename, 0o755 )

    def __getattr__(self, attr):
       #  print("Getting {0}.{1}".format(type(self.obj).__name__, attr))
        ret = getattr(self.obj, attr)
        if hasattr(ret, "__call__"):
            return self.FunctionWrapper(self, ret)
        return ret

    class FunctionWrapper:
        def __init__(self, parent, callable):
            self.parent = parent
            self.callable = callable

        def __call__(self, *args, **kwargs):
            #if self.callable.__name__ == "pcolormesh":
            #    import IPython; IPython.embed()
            import numpy as np
            s_args = ""
            for a in args:
                if "matplotlib" in str(type(a)):
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
            line = f"plt.{self.callable.__name__}({s_args})\n"
            if "savefig" in line:
                line = "from smodels_utils.helper.various import pngMetaInfo\n"
                line += "metadata = pngMetaInfo()\n"
                line += "plt.savefig('recorded.png',metadata=metadata)\n"
            if "plt.gcf()" in line:
                line = "fig=plt.gcf()\n"
            if "plt.gca()" in line:
                line = "ax=plt.gca()\n"
            self.parent.recordingfile.write ( line )
            ret = self.callable(*args, **kwargs)
            self.parent.callable_results.append(ret)
            return ret


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


