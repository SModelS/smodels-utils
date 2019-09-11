#!/usr/bin/env python3

""" The pytorch-based regressor for Z. So we can walk along its gradient. """

import os, time, sys, gzip, time
import numpy as np
import torch
import torch.nn.functional as F
from pympler.asizeof import asizeof
from model import Model, rthresholds

class RegressionHelper:
    def __init__(self):
        pass

    def device ( self ):
        # return torch.device("cpu")
        return torch.device('cuda:0' if torch.cuda.is_available() else 'cpu' )

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

    def trainOffline ( self ):
        trainer = Regressor( torchmodel = "test.ckpt" )
        #with gzip.open("training.gz","rb") as f:
        #    lines = f.readlines()
        with open("training.pcl","rb") as f:
            import pickle
            lines=[]
            try:
                while True:
                    line = pickle.load ( f )
                    lines.append ( line )
            except EOFError:
                pass
        for epoch in range(20000):
            losses=[]
            print ( "Epoch %d" % epoch )
            modelsbatch,Zbatch=[],[]
            dt=0.
            m=Model(0 )
            # for i,line in enumerate(lines):
            for i,d in enumerate(lines):
                # d = eval(line)
                m.masses = d["masses"]
                m.ssmultipliers = d["ssmultipliers"]
                m.decays = d["decays"]
                modelsbatch.append ( m )
                Zbatch.append ( d["Z"] )
                if len(modelsbatch)>=200:
                    t0=time.time()
                    trainer.batchTrain ( modelsbatch, Zbatch )
                    t1=time.time()-t0
                    dt += t1
                    modelsbatch,Zbatch=[],[]
                    losses.append ( trainer.loss )
                if i > 0 and i % 10000  == 0:
                    print ( "training %d, loss=%.5f. training took %.1fs." % (i, trainer.loss, dt ) )
                    dt = 0.
                if i > 0 and i % 100000 == 0:
                    trainer.save( name="test.ckpt" )
            print ( "End of epoch %d: losses=%.4f+-%.4f" % ( epoch, np.mean(losses),np.std(losses) ) )
            with open("regress.log","at") as f:
                f.write ( "[%s] End of epoch %d: losses=%.5f+-%.5f\n" % ( time.asctime(), epoch, np.mean(losses),np.std(losses) ) )


class PyTorchModel(torch.nn.Module):
    def __init__(self, variables = None ):
        super(PyTorchModel, self).__init__()
        self.variables = variables
        if type(variables) == type(None):
            helper = RegressionHelper()
            self.variables = helper.freeParameters( "template_many.slha" )
        self.walkerid = 0
        dim = self.inputDimension()
        self.pprint ( "input dimension is %d" % dim )
        dim2 = int ( dim/2 )
        dim4 = int ( dim/4 )
        dim8 = int ( dim/8 )
        dim16= int ( dim/16 )
        dim32= int ( dim/32 )
        dim64= int ( dim/64 )
        # self.linear1 = torch.nn.Linear( dim, dim16 )
        self.linear1 = torch.nn.Linear( dim, dim2 )
        # self.bn = torch.nn.LayerNorm( dim2 )
        self.bn = torch.nn.BatchNorm1d( dim2 )
        self.linear2 = torch.nn.Linear( dim2, dim4 )
        self.linear3 = torch.nn.Linear( dim4, dim8 )
        self.act = torch.nn.ELU()
        self.linear4 = torch.nn.Linear( dim8, dim16 )
        self.linear5 = torch.nn.Linear( dim16,dim32 )
        self.linear6 = torch.nn.Linear( dim32,dim64 )
        self.linear7 = torch.nn.Linear( dim64, 1 )
        self.dropout = torch.nn.Dropout ( .1 )
        self.last_ypred = None

    def pprint ( self, *args ):
        """ logging """
        print ( "[torchmodel:%d] %s" % (self.walkerid, " ".join(map(str,args))) )

    def inputDimension(self):
        """ returns the dimensionality of the input """
        return len ( self.variables ) 

    def forward(self, x):
        # print ( "forward", x.shape )
        out1 = self.linear1 ( x )
        # print ( "out1", out1.shape )
        bn1 = self.bn ( out1 )
        # print ( "bn1", bn1.shape )
        act1 = self.act ( out1 )
        out2 = self.linear2 ( act1 )
        act2 = self.act ( out2 )
        out3 = self.linear3 ( act2 )
        act3 = self.act ( out3 )
        out4 = self.linear4 ( act3 )
        act4 = self.act ( out4 )
        out5 = self.linear5 ( act4 )
        act5 = self.act ( out5 )
        out6 = self.linear6 ( act5 )
        act6 = self.act ( out6 )
        out7 = self.linear7 ( act6 )
        out8 = self.dropout ( out7 )
        y_pred = torch.sigmoid( out7 )
        self.last_ypred = y_pred.data.tolist()
        return y_pred

class Regressor:
    """ this is our nice regressor """
    def __init__ ( self, variables=None, walkerid=0, torchmodel=None, 
                   device=None, dump_training = True,
                   is_trained = False ):
        """
        :param dump_training: if True, regularly dump training data
        :param is_trained: if True, then we have a trained model, and can perform
                           gradient ascent
        """
        helper = RegressionHelper ()
        self.walkerid = walkerid
        self.training = 0
        self.dump_training = dump_training
        self.is_trained = is_trained
        self.device = device
        if device == None:
            self.device = helper.device()
        if variables == None:
            variables = helper.freeParameters( "template_many.slha" )
        self.torchmodel = torchmodel
       # if torchmodel == None:
       #     self.torchmodel = PyTorchModel( variables ).to ( self.device )
        if type(torchmodel)==str:
            self.torchmodel = PyTorchModel( variables ).to ( self.device )
            self.load ( torchmodel )
        #else:
        #    self.load() ## if a model exists we load it
        if self.torchmodel != None:
            self.torchmodel.eval()
            self.criterion = torch.nn.MSELoss(reduction="mean").to(self.device)
        # self.adam = torch.optim.SGD(self.torchmodel.parameters(), lr=0.01 )
            self.adam = torch.optim.Adam(self.torchmodel.parameters(), lr=0.001 )
        self.walkerid = walkerid

    def plusDeltaM ( self, theorymodel, rate= 1. ):
        """ move the theorymodel parameters in the direction
            of the gradient. """
        grad = self.grad.tolist()
        for k,v in theorymodel.masses.items():
            if not "M%d" % k in self.torchmodel.variables:
                print ( "error, dont know what to do with M%d" % k )
                sys.exit(-5)
            idx = self.torchmodel.variables.index( "M%d" % k)
            # print ( "idx", idx, "grad=", len(grad), len(grad[0]) )
            t = 10. * grad[0][idx] * ( v + 1e-5 ) # the inverse of the normalization
            theorymodel.masses[k]+= t * rate
        for k,v in theorymodel.ssmultipliers.items():
            if not "SS%d" % k in self.torchmodel.variables:
                print ( "error, dont know what to do with M%d" % k )
                sys.exit(-3)
            idx = self.torchmodel.variables.index( "SS%d" % k)
            t = grad[0][idx]
            theorymodel.ssmultipliers[k]+= t * rate
        for pid,decays in theorymodel.decays.items():
            for dpid,dbr in decays.items():
                if not "D%d_%d" % ( pid, dpid ) in self.torchmodel.variables:
                    print ( "error dont know what to do with D%d_%d" % ( pid, dpid ) )
                    sys.exit(-7)
                idx = self.torchmodel.variables.index( "D%d_%d" % (pid,dpid) )
                t=grad[0][idx]
                theorymodel.decays[pid][dpid]+=t*rate
        return theorymodel

    def convert ( self, theorymodel, tolist=False ):
        """ convert a theory model to x_data 
        :param tolist: if true, return as list, not as tensor
        """
        ret = [ None ]* len(self.torchmodel.variables)
        for k,v in theorymodel.masses.items():
            if not "M%d" % k in self.torchmodel.variables:
                print ( "error, dont know what to do with M%d" % k )
                sys.exit(-9)
            idx = self.torchmodel.variables.index( "M%d" % k)
            #if type(v) not in [ float, int ]:
            #    self.pprint ( "in convert: dealing with %s: %s" % (type(v),v) )
            #    sys.exit(-100)
            ret[idx]= np.log(v+1e-5) / 10. # a bit of a normalization
        for k,v in theorymodel.ssmultipliers.items():
            if not "SS%d" % k in self.torchmodel.variables:
                print ( "error, dont know what to do with M%d" % k )
                sys.exit(-22)
            idx = self.torchmodel.variables.index( "SS%d" % k)
            ret[idx]=v
        for pid,decays in theorymodel.decays.items():
            for dpid,dbr in decays.items():
                if not "D%d_%d" % ( pid, dpid ) in self.torchmodel.variables:
                    print ( "error dont know what to do with D%d_%d" % ( pid, dpid ) )
                    sys.exit(-55)
                idx = self.torchmodel.variables.index( "D%d_%d" % (pid,dpid) )
                ret[idx]=dbr
        for c,i in enumerate(ret):
            if i==None:
                ## FIXME make sure it only happens when irrelevant
                ret[c]=0.
        # self.pprint ( "returning a tensor for %s, to %s" % ( ret[:3], self.device ) )
        if tolist:
            return ret
        tmp = torch.Tensor([ ret ] )
        return tmp.to(self.device)

    def pprint ( self, *args ):
        """ logging """
        print ( "[regressor:%d] %s" % (self.walkerid, " ".join(map(str,args))) )

    def log ( self, *args ):
        """ logging to file """
        with open( "regression%d.log" % self.walkerid, "a" ) as f:
            f.write ( "[regressor:%d - %s] %s\n" % ( self.walkerid, time.strftime("%H:%M:%S"), " ".join(map(str,args)) ) )

    def train ( self, model, Z, rmax=None ):
        """ train y_label with x_data """
        self.training += 1
        x_data = self.convert ( model )
        x_data.requires_grad = True ## needs this to have dZ/dx in the end
        y_pred = self.torchmodel(x_data).to(self.device)
        #y_pred = y_pred.to(self.device)
        # y_label = torch.Tensor ( [np.log10(1.+Z),np.log10(1+rmax)] )#.to ( self.device )
        y_label = torch.Tensor ( [ [ Z / ( Z + 1. ) ] ] ).to ( self.device )
        loss = self.criterion ( y_pred, y_label )
        # self.pprint ( "With x=%s y_pred=%s, label=%s, loss=%s" % ( x_data[:5], y_pred, y_label, loss.data ) ) 
        self.loss = float( loss.data )
        self.log ( "training. predicted %s, target %s, loss %.3f" % ( y_pred, y_label, float(loss) ) )
        self.adam.zero_grad()
        loss.backward()
        self.adam.step()
        # print ( "[regressor] storing grad %s" % type(x_data.grad) )
        self.grad = x_data.grad ## store the gradient!

    def batchTrain ( self, models, Zs, rmax=None ):
        """ train y_label with x_data for a minibatch of models """
        self.training += 1
        tmp = []
        for model in models:
            tmp.append ( self.convert ( model, tolist=True ) )
        x_data = torch.Tensor ( tmp ).to ( self.device )
        x_data.requires_grad = True ## needs this to have dZ/dx in the end
        y_pred = self.torchmodel(x_data).to ( self.device )
        tmp = []
        for Z in Zs:
            if type(Z) in [ list, tuple ] and len(Z)==1:
                Z=Z[0]
            tmp.append ( [ Z / ( 1. + Z ) ] )
        y_label = torch.Tensor ( tmp ).to(self.device)
        # y_label = torch.Tensor ( [np.log10(1.+Z),1./(1+rmax)] )#.to ( self.device )
        loss = self.criterion ( y_pred, y_label )
        # self.pprint ( "With x=%s y_pred=%s, label=%s, loss=%s" % ( x_data[:5], y_pred, y_label, loss.data ) ) 
        self.loss = float( loss.data )
        self.log ( "training. predicted %s, target %s, loss %.3f" % ( y_pred, y_label, float(loss) ) )
        self.adam.zero_grad()
        loss.backward()
        self.adam.step()
        self.grad = x_data.grad ## store the gradient!

    def dumpTrainingData ( self, model ):
        """ dump the model with the compute Z, so we can train offline on it. """
        D = model.dict()
        # D["Z"] = self.torchmodel.last_ypred
        D["Z"] = model.Z
        if model.rmax > rthresholds[0]: ## put it to zero
            D["Z"]=0.
        line = "%s\n" % D
        with gzip.open("training_%d.gz" % self.walkerid,"ab") as f:
            f.write ( line.encode() )

    def save ( self, name = "model.ckpt" ):
        print ( "saving model", name )
        torch.save ( self.torchmodel.state_dict(), name )

    def load ( self, name = "model.ckpt" ):
        if os.path.exists ( name ):
            self.pprint ( "attempting to load model %s" % name )
            self.torchmodel = PyTorchModel()
            try:
                self.torchmodel.load_state_dict ( torch.load ( name, map_location = self.device ) )
                self.torchmodel.to ( self.device )
                self.torchmodel.eval()
            except Exception as e:
                self.pprint ( "couldnt load %s: %s. Will ignore it." % ( name, e ) )

    def predict ( self, model ):
        x_data = self.convert ( model )
        # print ( "x_data", x_data.shape )
        ret = self.torchmodel.forward ( x_data )
        # print ( "[predict] input=", x_data.shape, "ret=", ret )
        # self.grad = x_data.grad ## store the gradient!
        return - ret[0]/(ret[0]-1.)

if __name__ == "__main__":
    helper = RegressionHelper ()
    helper.trainOffline()
    #print ( helper.countDegreesOfFreedom ( "template_many.slha" ) )
    #regressor = Regressor ( helper.freeParameters( "template_many.slha" ) ) 
