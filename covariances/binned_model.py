def create ( bins ):
    import numpy as np
    import array

    import model_90 as m9
    import copy
    class _:
        def __init__(self,name):
            self.name=name

    ret = _("mbins")
            
    D = []
    for i,d in enumerate(m9.data.tolist()):
        if i in bins:
            D.append ( d )
    ret.data = array.array('d',D )

    B=[]
    for i,b in enumerate(m9.background.tolist() ):
        if i in bins:
            B.append ( b )
    ret.background = array.array('d', B ) 

    T=[]
    for i,t in enumerate(m9.third_moment.tolist() ):
        if i in bins:
            T.append ( t )
    ret.third_moment = array.array('d', T ) 

    S=[]
    for i,s in enumerate(m9.signal.tolist() ):
        if i in bins:
            S.append ( s )
    ret.signal = array.array('d', S ) 

    ## first unflatten
    C_= [ m9.covariance[m9.nbins*i:m9.nbins*(i+1)] for i in range(m9.nbins) ]

    ## then select
    C=[]                                                                                                                                  
    for i in range(m9.nbins):                                                                                                                    
        if not i in bins:                                                                                                                 
            continue                                                                                                                      
        ## correct row, now pick correct columns                                                                                          
        col=[]                                                                                                                            
        for j,e in enumerate ( C_[i] ):                                                                                         
            if j in bins:                                                                                                                 
                C.append ( e )
    ret.covariance=array.array('d', C )
    ret.nbins=len(bins)
    return ret
