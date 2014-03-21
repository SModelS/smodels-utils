class ByNameColorizer:
  """ A very simple class that assigns colors to particles """

  def __init__ ( self ):
    pass

  def getColor ( self, particle ):
    # print "[ColorizeByName.py] particle=",particle,"<br>"
    Dict={ "~g": "#ff0000" }
    if Dict.has_key ( particle ): return Dict[particle]
    leptons=[ "e" ,"mu", "tau", "nu" ]
    for l in leptons:
      if particle.find ( "~" + l )==0:  return "#d57f28"
    
    if particle.find("chi")>-1: return "#009900"
    squarks=[ "q", "b", "t", "u", "d", "c", "s" ]
    for sq in squarks: 
      if particle.find ( "~" + sq )==0:
        return "#0000cc"
    return "#000000"
