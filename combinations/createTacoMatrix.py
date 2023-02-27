#!/usr/bin/env python3

""" small script to create a combinations matrix from the taco output """

from smodels_utils.helper.various import getSqrts

class TacoMatrixCreator:
    def __init__ ( self ):
        self.createDictionary()

    def createDictionary ( self ):
        f = open ( "SModelS_MA5.json", "rt" )
        txt = f.read()
        f.close()
        txt = txt.replace(": ",":" )
        txt = txt.replace(" ","" )
        D = eval ( txt )
        self.translation = D

    def translate ( self, ma5id ):
        p = ma5id.find("-")
        ma5id=list(ma5id)
        ma5id[p]=":"
        ma5id = "".join(ma5id )
        ma5id = ma5id.replace(" ","")
        if ma5id in self.translation:
            return self.translation[ma5id]
        # some ids we just cannot find, not ma5<->smodels match
        # print ( f"[createTacoMatrix] could not find {ma5id}" )
        return None

    def cleanUp ( self, inp ):
        ret = {}
        for source,dest in inp.items():
            if source == None:
                continue
            tmp=[ x for x in dest if x is not None ]
            if tmp == []:
                continue
            ret[source]=tmp
        return ret

    def pprint ( self, D ):
        """ pretty print the combinability matrix """
        print ( "combinables" )
        print ( "===========" )
        for k,v in D.items():
            print ( f"{k}: {len(v)} combinables: {', '.join(v[:3])}, ... "  )
            # print ( f"{k}: {len(v)} combinables: {', '.join(v[:])}, ... "  )


    def run( self ):
        """ run, create the goddamn matrix """
        f = open ( "taco_matrix.txt", "rt" )
        lines=f.readlines()
        f.close()
        ma5analyses = lines[0].strip().split(",")
        smodelsanas = []
        ret = {} # the combinability matrix
        count = {}
        for a in ma5analyses[1:]:
            smodelsId = self.translate ( a )
            smodelsanas.append( smodelsId )
            if smodelsId == None:
                continue
            anaId = smodelsId [ : smodelsId.find(":") ]
            if not anaId in count:
                count[anaId]=0
            count[anaId]+=1
            ret[smodelsId]=[]
        for i,line in enumerate(lines[1:]):
            if smodelsanas[i]==None:
                continue
            anaIdi = smodelsanas[i] [ : smodelsanas[i].find(":") ]
            sqrtsi = getSqrts ( anaIdi )
            values = list ( map ( float, line.split(",")[1:] ) )
            for j,v in enumerate ( values ):
                if smodelsanas[j]==None:
                    continue
                anaIdj = smodelsanas[j] [ : smodelsanas[j].find(":") ]
                if anaIdj == anaIdi:
                    # dont look at SRs within the same analysis
                    continue
                # we dont need to document results from different experiments
                if "CMS" in anaIdj and "ATLAS" in anaIdi:
                    continue
                if "ATLAS" in anaIdj and "CMS" in anaIdi:
                    continue
                # we dont need to document results from different runs
                sqrtsj = getSqrts ( anaIdj )
                if abs ( sqrtsj -sqrtsi ) > 1e-5:
                    continue
                # print ( "anas", anaIdi, anaIdj )
                if abs(v) < .01:
                    ret [ smodelsanas[i] ].append ( smodelsanas[j] )
        #for a,c in count.items():
        #    print ( f"{a} has {c} SRs" )
        ret = self.cleanUp ( ret ) # remove the Nones
        ret = self.shrinkDictionary ( ret, count )
        self.pprint ( ret )
        self.save ( ret )

    def save ( self, ret ):
        f=open("tacocombinations.py","wt" )
        f.write ( "allowedTaco={}\n" )
        for k,v in ret.items():
            f.write ( f'allowedTaco["{k}"]={v}\n' )
        f.close()

    def shrinkDictionary ( self, D, count ):
        """ see if we can shrink this dictionary in case srA is uncorrelated
            with all analyses of anaB """
        return D
        ret = {}
        for sourceid, destids in D.items():
            tmp = []
            localcounts = {}
            for destid in destids:
                destana = destid [ : destid.find(":") ]
                if not destana in localcounts:
                    localcounts[destana]=0
                localcounts[destana]+=1
            ret[sourceid]=destids
        return ret


if __name__ == "__main__":
    creator = TacoMatrixCreator()
    creator.run()
