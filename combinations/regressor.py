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

    def trainOffline ( self, trainingfile, modelfile, verbosity ):
        trainer = Regressor( torchmodel = modelfile, verbosity=verbosity )
        with open( trainingfile, "rb" ) as f:
            import pickle
            lines=[]
            try:
                while True:
                    line = pickle.load ( f )
                    lines.append ( line )
            except EOFError:
                pass
        m=Model(0 )
        for epoch in range(20000):
            losses=[]
            # print ( "Epoch %d" % epoch )
            modelsbatch,Zbatch=[],[]
            dt=0.
            for i,d in enumerate(lines):
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
                if i > 0 and i % 20000  == 0:
                    print ( "training %d, loss=%.5f. training took %.1fs." % (i, trainer.loss, dt ) )
                    dt = 0.
                if i > 0 and i % 200000 == 0:
                    trainer.save( name="temp.ckpt" )
            trainer.save( name=modelfile )
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
        self.linear1 = torch.nn.Linear( dim, dim2 )
        self.bn1 = torch.nn.BatchNorm1d( dim2 )
        self.linear2 = torch.nn.Linear( dim2, dim4 )
        self.bn2 = torch.nn.BatchNorm1d( dim4 )
        self.linear3 = torch.nn.Linear( dim4, dim8 )
        self.bn3 = torch.nn.BatchNorm1d( dim8 )
        self.act = torch.nn.LeakyReLU(.1)
        self.linear4 = torch.nn.Linear( dim8, dim16 )
        self.bn4 = torch.nn.BatchNorm1d( dim16 )
        self.linear5 = torch.nn.Linear( dim16,dim32 )
        self.bn5 = torch.nn.BatchNorm1d( dim32 )
        self.linear6 = torch.nn.Linear( dim32,dim64 )
        self.bn6 = torch.nn.BatchNorm1d( dim64 )
        self.linear7 = torch.nn.Linear( dim64, 1 )
        self.dropout1 = torch.nn.Dropout ( .5 )
        self.dropout2 = torch.nn.Dropout ( .2 )
        self.dropout3 = torch.nn.Dropout ( .2 )
        self.dropout4 = torch.nn.Dropout ( .2 )
        self.dropout5 = torch.nn.Dropout ( .2 )
        self.dropout6 = torch.nn.Dropout ( .2 )
        self.dropout7 = torch.nn.Dropout ( .2 )
        self.relu = torch.nn.ReLU()
        self.last_ypred = None
        torch.nn.init.xavier_uniform_(self.linear1.weight)
        torch.nn.init.xavier_uniform_(self.linear2.weight)
        torch.nn.init.xavier_uniform_(self.linear3.weight)
        torch.nn.init.xavier_uniform_(self.linear4.weight)
        torch.nn.init.xavier_uniform_(self.linear5.weight)
        torch.nn.init.xavier_uniform_(self.linear6.weight)
        torch.nn.init.xavier_uniform_(self.linear7.weight)

    def pprint ( self, *args ):
        """ logging """
        print ( "[torchmodel:%d] %s" % (self.walkerid, " ".join(map(str,args))) )

    def inputDimension(self):
        """ returns the dimensionality of the input """
        return len ( self.variables ) 

    def forward(self, x):
        out1 = self.linear1 ( x )
        do1 = self.dropout1 ( out1 )
        act1 = self.act ( do1 )
        bn1 = self.bn1 ( act1 )
        out2 = self.linear2 ( bn1 )
        do2 = self.dropout2 ( out2 )
        act2 = self.act ( do2 )
        bn2 = self.bn2 ( act2 )
        out3 = self.linear3 ( bn2 )
        do3  = self.dropout3 ( out3 )
        act3 = self.act ( do3 )
        bn3 = self.bn3 ( act3 )
        out4 = self.linear4 ( bn3 )
        do4  = self.dropout4 ( out4 )
        act4 = self.act ( do4 )
        bn4  = self.bn4 ( act4 )
        out5 = self.linear5 ( bn4 )
        do5  = self.dropout5 ( out5 )
        act5 = self.act ( do5 )
        bn5  = self.bn5 ( act5 )
        out6 = self.linear6 ( bn5 )
        do6  = self.dropout6 ( out6 )
        act6 = self.act ( do6 )
        bn6  = self.bn6 ( act6 )
        out7 = self.linear7 ( bn6 )
        do7  = self.dropout7 ( out7 )
        y_pred = self.act ( do7 ) ## no negative numbers
        # self.last_ypred = y_pred.data.tolist()
        return y_pred

class Regressor:
    """ this is our nice regressor """
    def __init__ ( self, variables=None, walkerid=0, torchmodel=None, 
                   device=None, dump_training = True,
                   is_trained = False, verbosity = "info" ):
        """
        :param dump_training: if True, regularly dump training data
        :param is_trained: if True, then we have a trained model, and can perform
                           gradient ascent
        """
        helper = RegressionHelper ()
        self.walkerid = walkerid
        self.verbosity = verbosity
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
            t = 10. * grad[0][idx] # the inverse of the normalization
            # t = 10. * grad[0][idx] * ( v + 1e-5 ) # the inverse of the normalization
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
        y_label = torch.Tensor ( [ [ Z ] ] ).to ( self.device )
        # y_label = torch.Tensor ( [ [ Z / ( Z + 1. ) ] ] ).to ( self.device )
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
            tmp.append ( [ Z ] )
            # tmp.append ( [ Z / ( 1. + Z ) ] )
        y_label = torch.Tensor ( tmp ).to(self.device)
        if self.verbosity in [ "debug" ]:
            import random
            i = random.choice(range(len(Zs)))
            Zpred = float(y_pred[i])
            Zsi = Zs[i]
            d = abs(Zpred - Zsi)
            print ( "[regressor] i:%2d, Z_pred:%.2f Z_true:%.2f d:%.2f" % ( i, Zpred, Zsi, d ) )
        # print ( "y_pred", y_pred.shape, self.unfold ( y_pred[0][0] ) )
        # print ( "y_label", y_label.shape, y_label[0][0] )
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
        ret = self.torchmodel.forward ( x_data )
        return ret[0]

if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser(
            description='regressor, used for training when called from command line ' )
    argparser.add_argument ( '-f', '--picklefile',
            help='specify pickle file with training data [training.pcl]',
            type=str, default="training.pcl" )
    argparser.add_argument ( '-m', '--modelfile',
            help='specify model file to train [test.ckpt]',
            type=str, default="test.ckpt" )
    argparser.add_argument ( '-v', '--verbosity',
            help='verbosity -- debug,info,warn,error [info]',
            type=str, default="info" )
    args = argparser.parse_args()
    
    helper = RegressionHelper ()
    helper.trainOffline( args.picklefile, args.modelfile, args.verbosity )
    #print ( helper.countDegreesOfFreedom ( "template_many.slha" ) )
    #regressor = Regressor ( helper.freeParameters( "template_many.slha" ) ) 
