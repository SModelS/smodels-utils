def singlevalue ( fraction ):
    r=int(255.*( fraction ))
    s=hex(r)[2:]
    s="0"+s
    s=s[-2:]
    return s
    ## return "%2s" % ( hex(r)[2:] ) ## , hex(b)[2:] )

def rgbValue ( fraction ):
    """ fraction=1. gives red, fraction=0. gives blue,
        fraction<0. and > 1. give black """
    if fraction<0. or fraction>1.:
      return "#000000"
    red   = [0.00, 0.00, 0.47, 1.00, 0.51]
    green = [0.00, 0.81, 0.80, 0.20, 0.00]
    blue  = [0.51, 1.00, 0.08, 0.00, 0.00]
    x=int ( fraction*4. )
    return f"#{singlevalue(red[x])}{singlevalue(green[x])}{singlevalue(blue[x])}"
