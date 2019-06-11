#!/usr/bin/env python3

""" The pytorch-based regressor for Z. So we can walk along its gradient. """

import os
import numpy as np
import torch
import torch.nn.functional as F

class RegressionHelper:
    def __init__(self):
        pass

    def freeParameters ( self, slhafile ):
        with open(slhafile,"r") as f:
            lines=f.readlines()
        variables = {}
        t=[]
        for line in lines:
            p = line.find("#")
            if p>-1:
                line = line[:p]
            line = line.strip()
            if not "D1" in line and not "M1" in line and not "D2" in line and \
                   not "M2" in line:
                continue
            tokens = line.split(" ")
            for i in tokens:
                if i.startswith("D"):
                    t.append ( i )
                if i.startswith("M"):
                    t.append ( i )
                    t.append ( i.replace("M","SS" ) )
        return t

    def countDegreesOfFreedom ( self, slhafile ):
        return len ( self.freeParameters( slhafile ) )
            

class PyTorchModel(torch.nn.Module):
    def __init__(self, variables ):
        super(PyTorchModel, self).__init__()
        self.variables = variables
        dim = self.inputDimension()
        dim4 = int ( dim/4)
        dim16= int ( dim4/4)
        self.linear1 = torch.nn.Linear( dim, dim4 )
        self.linear2 = torch.nn.Linear( dim4, dim16 )
        self.relu = torch.nn.ReLU()
        self.linear3 = torch.nn.Linear( dim16, 1 )

    def inputDimension(self):
        """ returns the dimensionality of the input """
        return len ( self.variables ) 

    def forward(self, x):
        out1 = self.linear1 ( x )
        act1 = self.relu ( out1 )
        out2 = self.linear2 ( act1 )
        act2 = self.relu ( out2 )
        out3 = self.linear3 ( act2 )
        y_pred = torch.sigmoid( out3 )
        return y_pred

class Regressor:
    """ this is our nice regressor """
    def __init__ ( self, variables=None, walkerid=0 ):
        if variables == None:
            helper = RegressionHelper ()
            variables = helper.freeParameters( "template_many.slha" )
        self.torchmodel = PyTorchModel( variables )
        self.load() ## if a model exists we load it
        self.criterion = torch.nn.MSELoss(reduction="mean")
        self.adam = torch.optim.Adam(self.torchmodel.parameters(), lr=0.01 )
        self.walkerid = walkerid

    def convert ( self, theorymodel ):
        """ convert a theory model to x_data """
        ret = [ None ]* len(self.torchmodel.variables)
        for k,v in theorymodel.masses.items():
            if not "M%d" % k in self.torchmodel.variables:
                print ( "error, dont know what to do with M%d" % k )
                sys.exit()
            idx = self.torchmodel.variables.index( "M%d" % k)
            ret[idx]= np.log(v+1e-5) / 10. # a bit of a normalization
        for k,v in theorymodel.ssmultipliers.items():
            if not "SS%d" % k in self.torchmodel.variables:
                print ( "error, dont know what to do with M%d" % k )
                sys.exit()
            idx = self.torchmodel.variables.index( "SS%d" % k)
            ret[idx]=v
        for pid,decays in theorymodel.decays.items():
            for dpid,dbr in decays.items():
                if not "D%d_%d" % ( pid, dpid ) in self.torchmodel.variables:
                    print ( "error dont know what to do with D%d_%d" % ( pid, dpid ) )
                    sys.exit()
                idx = self.torchmodel.variables.index( "D%d_%d" % (pid,dpid) )
                ret[idx]=dbr
        for c,i in enumerate(ret):
            if i==None:
                ## FIXME make sure it only happens when irrelevant
                ret[c]=0.
        return torch.Tensor(ret)

    def pprint ( self, *args ):
        """ logging """
        print ( "[regressor:%d] %s" % (self.walkerid, " ".join(map(str,args))) )

    def log ( self, *args ):
        """ logging to file """
        with open( "walker%d.log" % self.walkerid, "a" ) as f:
            f.write ( "[regressor:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def train ( self, model, Z ):
        """ train y_label with x_data """
        x_data = self.convert ( model )
        y_pred = self.torchmodel(x_data)
        y_label = torch.Tensor ( [Z] )
        loss = self.criterion ( y_pred, y_label )
        self.pprint ( "training. predicted %s, target %s, loss %s" % ( float(y_pred), float(y_label), float(loss) ) )
        self.adam.zero_grad()
        loss.backward()
        self.adam.step()

    def save ( self ):
        torch.save ( self.torchmodel, 'model.ckpt' )

    def load ( self ):
        if os.path.exists ( "model.ckpt" ):
            self.torchmodel = torch.load ( "model.ckpt" )

    def predict ( self, model ):
        x_data = self.convert ( model )
        return self.torchmodel.forward ( x_data )

if __name__ == "__main__":
    helper = RegressionHelper ()
    print ( helper.countDegreesOfFreedom ( "template_many.slha" ) )
    regressor = Regressor ( helper.freeParameters( "template_many.slha" ) ) 
