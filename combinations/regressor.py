#!/usr/bin/env python3

""" The pytorch-based regressor for Z. So we can walk along its gradient. """

import numpy as np
import torch
import torch.nn.functional as F

class RegressionHelper:
    def __init__(self):
        pass
    def countDegreesOfFreedom ( self, slhafile ):
        with open(slhafile,"r") as f:
            lines=f.readlines()
        for line in lines
            

class Model(torch.nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.linear = torch.nn.Linear(20, 1)

    def forward(self, x):
        y_pred = F.sigmoid(self.linear(x))
        return y_pred

class Regressor:
    """ this is our nice regressor """
    def __init__ ( self ):
        self.model = Model()
        self.criterion = torch.nn.L2Loss(size_average=True)
        self.adam = torch.optim.Adam(model_adam.parameters(), lr=0.001)

    def train ( self, x_data, y_label ):
        """ train y_label with x_data """
        y_pred = self.model(x_data)
        loss = self.criterion ( y_ped, y_label )
        self.adam.zero_grad()
        loss.backward()
        self.adam.step()

    def predict ( self, x_data ):
        return self.model.forward ( x_data )

if __name__ == "__main__":
    helper = RegressionHelper ()
    print ( helper.countDegreesOfFreedom ( "template_many.slha" ) )
    # regressor = Regressor()
