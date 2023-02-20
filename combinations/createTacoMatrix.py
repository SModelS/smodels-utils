#!/usr/bin/env python3

""" small script to create a combinations matrix from the taco output """

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
        return ma5id

    def run( self ):
        f = open ( "taco_matrix.txt", "rt" )
        lines=f.readlines()
        f.close()
        ma5analyses = lines[0].strip().split(",")
        smodelsanas = []
        ret = {}
        for a in ma5analyses[1:]:
            smodelsAnaId = self.translate ( a )
            smodelsanas.append( smodelsAnaId )
            ret[smodelsAnaId]=[]
           #  print ( a, "=>", smodelsAnaId )
        for i,line in enumerate(lines[1:3]):
            values = list ( map ( float, line.split(",")[1:3] ) )
            for j,v in enumerate ( values ):
                if abs(v) < .01:
                    ret [ smodelsanas[i] ].append ( smodelsanas[j] )
                    
                    
            print ( values )
            
            


if __name__ == "__main__":
    creator = TacoMatrixCreator()
    creator.run()
