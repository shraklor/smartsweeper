#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       neural_network.py
#
#       Copyright 2010 Nolan Baker <hendersonhasselbalch@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import random, os, math
from numpy import *
import numpy.random as nrand

################################################################################
# Useful Vector Functions
################################################################################
def sigmoid(x):
    return 1.0 / (1 + math.exp(-x))
sigmoid = vectorize(sigmoid, otypes=[float])

def sigPrime(x):
    # in terms of the output of the sigmoid function
    # otherwise would be sig(x) - sig^2(x)
    return x - x ** 2
sigPrime = vectorize(sigPrime, otypes=[float])

def oneMinus(x):
    return 1 - x
oneMinus = vectorize(oneMinus, otypes=[float])

def sub(x,y):
    return x - y
sub = vectorize(sub, otypes=[float])

################################################################################
# Neural Network
################################################################################
class NeuralNet:
    def __init__(self, i, h, o):
        self.w_ih = mat(nrand.uniform(-1,1,(i,h)))
        self.w_ho = mat(nrand.uniform(-1,1,(h,o)))
        self.m_ih = mat(zeros((i,h)))
        self.m_ho = mat(zeros((h,o)))

    def getOut(self, i):
        self.h = sigmoid(mat(i) * self.w_ih)
        return sigmoid(self.h * self.w_ho).tolist()[0]

    def train(self, i, t, a = .1, b = .01):

        # get output of our neural network
        out = mat(self.getOut(i))

        # calc deltas
        d_o = mat(asarray(out) * asarray(oneMinus(out)) *
                  asarray(sub(mat(t), out)))
        d_h = mat(asarray(self.h) * asarray(oneMinus(self.h)) *
                  asarray(d_o * self.w_ho.T))

        # update weights
        c_ih = mat(i).T * d_h
        self.w_ih = add(add(self.w_ih, a * c_ih), b * self.m_ih)
        self.m_ih = c_ih
        c_ho = self.h.T * d_o
        self.w_ho = add(add(self.w_ho, a * c_ho), b * self.m_ho)
        self.m_ho = c_ho

################################################################################
# example
################################################################################
def main():

    nn = NeuralNet(2,10,1)
    examples = [([0,1], [1]),
                ([1,1], [0]),
                ([1,0], [1]),
                ([0,0], [0])]

    for i in range(10000):
        print i
        x = random.randint(0,4)
        nn.train(examples[x][0], examples[x][1], 3)

    print nn.getOut([0,1])
    print nn.getOut([1,1])
    print nn.getOut([1,0])
    print nn.getOut([0,0])

if __name__ == '__main__':
    main()
