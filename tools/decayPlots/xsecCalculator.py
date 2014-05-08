## import vertigo

class XSecCalculator:
  """ A simple calculator that bases its numbers on the xsecs for the
    simplified models 
    For smarter stuff, we use pickle files, see XSecFromPickleFile
    """
  def __init__ ( self, masses ):
    self.masses=masses
    ## xsector=vertigo.XSection()
    self.xsecs={}
    self.adjoint={}
    allvalues=[]
    ## print "masses:",masses
    for (name,mass) in masses.items():
      if name[:1]!="~":
        continue
      if name[:3]=="~l_" or name[:4]=="~nu_" or name[:4]=="~mu_" or name[:3]=="~e_":
        continue
      if name[:5]=="~tau_":
        continue
      if name[:4]=="~chi":
        continue
      if name[:2]=="~g":
        x=0.
        try:
          x=0. ## xsector.xSecGG ( float(mass) )
        except:
          # no cross section, if mass is a string
          pass
        ## print "[XSec] gg m=%f  s=%f" % ( mass, x )
        self.xsecs[name]=x
        allvalues.append ( x )
        for (name2,mass2) in masses.items():
          if name2[:1]!="~":
            continue
          if name2[:2]=="~l" or name2[:3]=="~nu":
            continue
          if name2[:4]=="~chi":
            continue
          if name2[:2]!="~g":
            if not self.adjoint.has_key(name):
              self.adjoint[name]={}
            x=0.
            try:
              x=0. ## xsector.xSecGQ(float(mass),float(mass2))
            except:
              pass
            ## print "[XSec] gq m=%f m=%f  s=%f" % ( mass, mass2, x )
            self.adjoint[name][name2]=x
            ## allvalues.append ( x )
      else:
        x=0.
        try:
          fmass=float ( mass )
          x=0. ## xsector.xSecQQ ( fmass )
        except:
          pass
        self.xsecs[name]=x
        allvalues.append ( x )
        ##print "[XSec] qq name=%s m=%f  s=%f" % ( name, mass, x )
    self.maximum=max ( allvalues )

  def getXSec ( self, particle ):
    if self.xsecs.has_key ( particle ):
      return self.xsecs[particle]
    return 0.0

  def getColor ( self, particle ):
    import Colors
    mxsec=self.getXSec ( particle )
    if mxsec==None or mxsec==0.:
      return Colors.rgbValue ( -1. )
    ## print "%f / %f = %s " % ( float(mxsec), self.maximum, colors.rgbValue ( float(mxsec) / self.maximum ) )

    return Colors.rgbValue ( float(mxsec) / self.maximum )

  def getAdjointXSec ( self, p1, p2 ):
    if self.adjoint.has_key ( p1 ) and self.adjoint[p1].has_key ( p2 ):
      return self.adjoint[p1][p2]
    if self.adjoint.has_key ( p2 ) and self.adjoint[p1].has_key ( p1 ):
      return self.adjoint[p2][p1]
    return 0.
