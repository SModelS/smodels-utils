#!/usr/bin/env python3

""" The pytorch-based regressor for Z. So we can walk along its gradient. """

import os, time, sys, gzip, time, copy, random, math, subprocess
import numpy as np
import torch
import torch.nn.functional as F
from pympler.asizeof import asizeof
from model import Model, rthresholds

class PyTorchModel(torch.nn.Module):
    def __init__(self, variables = None ):
        super(PyTorchModel, self).__init__()
        self.variables = variables
        self.nmasses = 0
        self.ndecays = 0
        for k in variables:
            if "M" in k:
                self.nmasses+=1
            if "D" in k:
                self.ndecays+=1
        if type(variables) == type(None):
            helper = RegressionHelper()
            self.variables = helper.freeParameters( "template_many.slha" )
            self.nmasses = helper.nmasses ## store how many masses we have
            self.ndecays = helper.ndecays ## store how many branchings we have
        self.walkerid = 0
        dim = self.inputDimension()
        self.pprint ( "input dimension is %d (%d masses, %d decays)" % ( dim, self.nmasses, self.ndecays ) )
        dim2 = int ( 2*dim )
        dim4 = int ( 4*dim )
        dim8 = int ( dim )
        dim16= int ( dim/2 )
        dim32= int ( dim/4 )
        dim64= int ( dim/8 )
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
        self.dropout1 = torch.nn.Dropout ( .01 )
        self.dropout2 = torch.nn.Dropout ( .1 )
        self.dropout3 = torch.nn.Dropout ( .1 )
        self.dropout4 = torch.nn.Dropout ( .1 )
        self.dropout5 = torch.nn.Dropout ( .1 )
        self.dropout6 = torch.nn.Dropout ( .1 )
        self.dropout7 = torch.nn.Dropout ( .1 )
        # self.relu = torch.nn.ReLU()
        # self.last_ypred = None
        torch.nn.init.xavier_uniform_(self.linear1.weight)
        torch.nn.init.xavier_uniform_(self.linear2.weight)
        torch.nn.init.xavier_uniform_(self.linear3.weight)
        torch.nn.init.xavier_uniform_(self.linear4.weight)
        torch.nn.init.xavier_uniform_(self.linear5.weight)
        torch.nn.init.xavier_uniform_(self.linear6.weight)
        torch.nn.init.xavier_uniform_(self.linear7.weight)

    def my_load_state_dict ( self, dct ):
        """ my own routine for loading state dicts. 
        Dunno why, but this fixes the state dict loading issue.
        """
        self.pprint ( "now loading state dict with %d entries" % len(dct) )
        self.load_state_dict ( dct )
        self.pprint ( "done loading dct" )
        return

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
        # y_pred = torch.nn.Sigmoid() ( do7 ) 
        y_pred = self.act ( do7 ) ## 5, so we can learn Zs up to ~ 5 easily
        # return y_pred / ( 1. + y_pred )
        return y_pred


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
        self.nmasses = 0 ## count the number of masses
        self.ndecays = 0 ## count the number of branchings
        for line in lines:
            p = line.find("#")
            if p>-1:
                line = line[:p]
            line = line.strip()
            #if not "M1" in line and not "M2" in line:
            #    continue ## for now no decays
            if not "D1" in line and not "M1" in line and not "D2" in line and \
                   not "M2" in line:
                continue
            tokens = line.split(" ")
            for i in tokens:
                if i.startswith("D"):
                    t.append ( i )
                    self.ndecays += 1
                if i.startswith("M"):
                    self.nmasses += 1
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
        M=Model(0, keep_meta = False )
        models = []
        for i,d in enumerate(lines):
            m = copy.deepcopy(M)
            m.masses = d["masses"]
            m.ssmultipliers = d["ssmultipliers"]
            m.decays = d["decays"]
            models.append ( ( trainer.convert ( m, tolist=True ), d["Z"] ) )

        for epoch in range(20000):
            errs=[]
            if epoch % 10 == 0:
                trainer.clearScores()
            # print ( "Epoch %d" % epoch )
            dt,tT=0.,0.
            indices = list(range(len(models)))
            random.shuffle ( indices ) ## random indices
            batchsize = 1000
            nbatches = int(math.ceil(len(models)/batchsize))
            writeScores = False
            if epoch % 10 == 0:
                writeScores = True
            for mbatch in range(nbatches):
                beg = mbatch*batchsize
                end = (mbatch+1)*batchsize
                modelsbatch = [ models[x][0] for x in indices[beg:end] ]
                Zbatch = [ [ models[x][1] ] for x in indices[beg:end] ]
                t0=time.time()
                tt=trainer.batchTrain ( modelsbatch, Zbatch, epoch, writeScores )
                tT+=tt
                dt+=time.time()-t0
                errs.append ( np.sqrt(trainer.loss) )
            if epoch % 5 == 0:
                print ( "End of epoch %d: stderr=%.4f+-%.4f (%.1fs/%.1fs)" % ( epoch, np.mean(errs),np.std(errs), dt, tT ) )
            if writeScores:
                trainer.save( name=modelfile )
                with open("regress.log","at") as f:
                    f.write ( "[%s] End of epoch %d: errs=%.5f+-%.5f\n" % ( time.asctime(), epoch, np.mean(errs),np.std(errs) ) )

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
        translate = { "debug": 10, "info": 20, "warning": 30, "error": 40 }
        if verbosity in translate.keys():
            self.verbosity = translate[verbosity]
        self.training = 0
        self.dump_training = dump_training
        self.is_trained = is_trained
        self.device = device
        self.clearScores()
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
            self.adam = torch.optim.Adam( self.torchmodel.parameters(), lr=0.003,
                                          weight_decay = .005  )
        self.walkerid = walkerid

    def plusDeltaM ( self, theorymodel, rate= 1. ):
        """ move the theorymodel parameters in the direction
            of the gradient. """
        grad = self.grad.tolist()
        # print ( "grad", grad )
        for k,v in theorymodel.masses.items():
            if not "M%d" % k in self.torchmodel.variables:
                print ( "error, dont know what to do with M%d" % k )
                sys.exit(-5)
            idx = self.torchmodel.variables.index( "M%d" % k)
            # print ( "idx", idx, "grad=", len(grad), len(grad[0]) )
            t = grad[0][idx] 
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
            if v > 3000.: 
                v = 3000. ## set masses to 3000 max
            ret[idx]= v
            # ret[idx]= np.log(v+1e-5) / 10. # a bit of a normalization
        for k,v in theorymodel.ssmultipliers.items():
            if not "SS%d" % k in self.torchmodel.variables:
                print ( "error, dont know what to do with M%d" % k )
                sys.exit(-22)
            idx = self.torchmodel.variables.index( "SS%d" % k)
            ret[idx]= v
        if True:
            for pid,decays in theorymodel.decays.items():
                for dpid,dbr in decays.items():
                    if not "D%d_%d" % ( pid, dpid ) in self.torchmodel.variables:
                        print ( "error dont know what to do with D%d_%d" % ( pid, dpid ) )
                        sys.exit(-55)
                    idx = self.torchmodel.variables.index( "D%d_%d" % (pid,dpid) )
                    ret[idx]= dbr
        for c,i in enumerate(ret):
            if i==None:
                ## FIXME make sure it only happens when irrelevant
                ret[c]=0.
        # self.pprint ( "returning a tensor for %s, to %s" % ( ret[:3], self.device ) )
        if tolist:
            return ret
        tmp = torch.Tensor([ ret ] )
        #print ( "conversion", tmp )
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

    def clearScores ( self ):
        """ remove old scores file """
        if os.path.exists ( "scores.csv" ):
            cmd = "mv scores.csv oldscores.csv"
            subprocess.getoutput ( cmd )

    def writeScores ( self, pred, truth, epoch ):
        """ write out predicted versus true Z values,
        for debugging """
        with open("scores.csv","at") as f:
            for p,t in zip(pred,truth):
                f.write("%d,%.2f,%.2f\n" % ( epoch, p, t ) )

    def batchTrain ( self, models, Zs, epoch = 0, writeScores = False ):
        """ train y_label with x_data for a minibatch of models 
        :param writeScores: write out the predicted and true Z values,
                            for debugging
        """
        self.training += 1
        t0 = time.time()
        x_data = torch.Tensor ( models ).to ( self.device )
        y_pred = self.torchmodel(x_data).to ( self.device )
        y_label = torch.Tensor ( Zs ).to(self.device)
        t1 = time.time()
        if self.verbosity < 15:
            import random
            i = random.choice(range(len(Zs)))
            Zpred = float(y_pred[i])
            Zsi = Zs[i]
            d = abs(Zpred - Zsi)
            print ( "[regressor] i:%2d, Z_pred:%.2f Z_true:%.2f d:%.2f" % ( i, Zpred, Zsi, d ) )
        #t0 = time.time()
        loss = self.criterion ( y_pred, y_label )
        self.adam.zero_grad()
        loss.backward()
        self.adam.step()
        #t1 = time.time()
        if writeScores:
            self.writeScores ( y_pred, y_label, epoch )
        self.loss = float( loss.data )
        # self.log ( "training. predicted %s, target %s, loss %.3f (%d)" % ( y_pred, y_label, self.loss, writeScores ) )
        tm = t1 - t0
        # self.grad = x_data.grad ## store the gradient!
        return tm

    def dumpTrainingData ( self, model ):
        """ dump the model with the compute Z, so we can train offline on it. """
        D = model.dict()
        # D["Z"] = self.torchmodel.last_ypred
        D["Z"] = model.Z
        D["rmax"] = model.rmax
        if model.rmax > rthresholds[0]: ## put it to zero
            D["Z"]=0.
        line = "%s\n" % D
        with gzip.open("training_%d.gz" % self.walkerid,"ab") as f:
            f.write ( line.encode() )

    def save ( self, name = "model.ckpt" ):
        if self.verbosity < 15:
            print ( "saving model", name )
        torch.save ( self.torchmodel.state_dict(), name )

    def load ( self, name = "model.ckpt" ):
        if os.path.exists ( name ):
            self.pprint ( "attempting to load model %s" % name )
            self.torchmodel = PyTorchModel()
            try:
                sd = torch.load ( name, map_location = self.device )
                self.torchmodel.my_load_state_dict ( sd )
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
    argparser.add_argument ( '-C', '--checkfile',
            help='choose where to get model from for checking [hiscore.pcl]', 
            type=str, default="hiscore.pcl" )
    argparser.add_argument ( '-c', '--check',
            help='simply check the model, dont train (you may use -f to choose where to get model from)', action='store_true' )
    args = argparser.parse_args()
    
    helper = RegressionHelper ()
    if args.check:
        import pickle
        print ( "checking the torch model" )
        regressor = Regressor ( torchmodel = args.modelfile )
        picklefile = args.checkfile
        print ( "fetching model from %s" % picklefile )
        with open( picklefile,"rb") as f:
            models = pickle.load ( f )
            trimmed = pickle.load ( f )
        model = trimmed[0]
        use="trimmed"
        if model == None:
            use="untrimmed"
            model = models[0]
        print ( "Taking %s model %.2f" % ( use, model.Z ) )
        predictedZ = regressor.predict ( model )
        print ( " `- predicted value: %.2f" % predictedZ )
        sys.exit()
        
    helper.trainOffline( args.picklefile, args.modelfile, args.verbosity )
