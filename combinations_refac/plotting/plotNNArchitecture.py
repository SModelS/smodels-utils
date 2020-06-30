#!/usr/bin/env python3

## https://github.com/waleedka/hiddenlayer/blob/master/demos/pytorch_graph.ipynb

import torch.onnx
import torch
from regressor import PyTorchModel, RegressionHelper
from torchsummary import summary

helper=RegressionHelper()
variables = helper.freeParameters( "template_many.slha" )
model = PyTorchModel( variables ) # .to ( "cuda:0" )
print ( "len",len(variables) )

# summary ( model, input_size = ( len(variables), ) )
# dummy_input = torch.Variable(torch.randn( len(variables)))
dummy_input = torch.Tensor( [0.]*len(variables) )
# torch.onnx.export ( model, dummy_input, "model.onnx" )
import hiddenlayer as hl
hl_graph = hl.build_graph( model, dummy_input )
hl_graph.save ( "NN" )
print ( hl_graph )
import IPython
IPython.embed()

