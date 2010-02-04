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
from util import *

################################################################################
# Neural Network
################################################################################
class NeuralNet:
    def __init__(self, layers_list):
        # layers list - number of nodes in each layer
        self.layers_list = layers_list
        self.num_layers = len(layers_list)

        # initialize the weight arrays according to the layers_list
        self.weights = []
        self.momentum = []
        for i in range(self.num_layers - 1):

            array1 = randMat(layers_list[i], layers_list[i+1])
            self.weights.append(array1)

            array2 = zeroMat(layers_list[i], layers_list[i+1])
            self.momentum.append(array2)

    def getOut(self, a):
        '''
        # takes the input vector a and turns it into a (1 x n) matrix
        a = [a]

        # then dot a...
        self.outputs = []
        for weight_array in self.weights:
            #  ...with our weight arrays
            a = dotMats(a, weight_array)

            # run it through our activation func
            a = sigMat(a)

            # append each output vector to a list
            self.outputs.append(a[0])

        # and outputs the final vector
        return a[0]
        '''

        lay = self.layers_list
        self.outputs = [a]

        for layer in range(len(lay) - 1):
            a = []
            for j in range(lay[layer + 1]):
                sum = 0.0
                for i in range(lay[layer]):
                    sum += self.outputs[layer][i] * self.weights[layer][i][j]
                a.append(sigmoid(sum))
            self.outputs.append(a)

        return a

    def getActionIndex(self):
        # look at the final output vector
        o = self.outputs[-1]

        # find the highest values in the vector
        max = 0
        possible = []
        for i in range(len(o)):
            if o[i] > max:
                max = o[i]
                possible = [i]
                continue
            if o[i] == max:
                possible.append(i)

        # pick a random one from the list
        random.shuffle(possible)
        return possible[0]

    def train(self, input, target, rate = 1):


        # get output of our neural network
        output = self.getOut(input)
        '''
        # back-propogate deltas for each output vector
        err = subVectors(target, output)
        deltas = mulMats(sigPrimeMat([self.outputs[-1]]), [err])

        n = range(-self.num_layers + 2, 0)
        n.reverse()
        for i in n:
            # calculate deltas
            w = self.weights[i]
            d = transMat([deltas[i]])
            wdT = transMat(dotMats(w, d))
            delta = mulMats(sigPrimeMat([self.outputs[i - 1]]), wdT)
            deltas = delta + deltas

            # update weights
            T = transMat([self.outputs[i - 1]])
            D = [deltas[i]]
            change = dotMats(T, D)
            W = self.weights[i]
            self.weights[i] = addMats(addMats(W, scaleMat(rate, change)),
                                      scaleMat(rate, self.momentum[i]))
            self.momentum[i] = change
        '''
        ################### REMOVE

        # calculate error terms for output
        output_deltas = [0.0] * self.layers_list[-1]
        for k in range(self.layers_list[-1]):
            error = target[k]-self.outputs[-1][k]
            output_deltas[k] = sigPrime(self.outputs[-1][k]) * error

        # calculate error terms for hidden
        hidden_deltas = [0.0] * self.layers_list[-2]
        for j in range(self.layers_list[-2]):
            error = 0.0
            for k in range(self.layers_list[-1]):
                error = error + output_deltas[k]*self.weights[-1][j][k]
            hidden_deltas[j] = sigPrime(self.outputs[-2][j]) * error

        N = .5
        M = .1
        # update output weights
        for j in range(self.layers_list[-2]):
            for k in range(self.layers_list[-1]):
                change = output_deltas[k]*self.outputs[-2][j]
                self.weights[-1][j][k] = self.weights[-1][j][k] + N*change + M*self.momentum[-1][j][k]
                self.momentum[-1][j][k] = change
                #print N*change, M*self.co[j][k]

        # update input weights
        for i in range(self.layers_list[0]):
            for j in range(self.layers_list[1]):
                change = hidden_deltas[j]*self.outputs[0][i]
                self.weights[0][i][j] = self.weights[0][i][j] + N*change + M*self.momentum[0][i][j]
                self.momentum[0][i][j] = change

        ################### REMOVE

        '''

        # back-propogate deltas for each output vector
        error = subVectors(target, output)
        delta = [0.0] * self.layers_list[-1]
        for k in range(self.layers_list[-1]):
            delta[k] = sigPrime(self.outputs[-1][k]) * error[k]
        deltas = [delta]

        n = range(-self.num_layers + 3, 0)
        n.reverse()
        for i in n:
            delta = [0.0] * self.layers_list[i]
            for j in range(self.layers_list[i-1]):
                error = 0.0
                for k in range(self.layers_list[i]):
                    error += deltas[i][k]*self.weights[i][j][k]
                delta[j] = sigPrime(self.outputs[i-1][j]) * error
            deltas = [delta] + deltas

            # update output weights
            for j in range(self.layers_list[i-1]):
                for k in range(self.layers_list[1]):
                    change = deltas[i-1][k] * self.outputs[i-1][j]
                    self.weights[i][j][k] = self.weights[i][j][k] + N*change + M*self.momentum[i][j][k]
                    self.momentum[i][j][k] = change
        '''

        #error = 0
        #for i in err:
        #    error += .5 * (i) ** 2
        #return error

################################################################################
# example
################################################################################
def main():

    layers = [2,2,1]
    nn = NeuralNet(layers)
    for i in range(10000):
        nn.train([0,1], [1], 1)
        nn.train([1,1], [0], 1)
        nn.train([1,0], [1], 1)
        nn.train([0,0], [0], 1)

    print nn.getOut([0,1])
    print nn.getOut([1,1])
    print nn.getOut([1,0])
    print nn.getOut([0,0])


if __name__ == '__main__':
    main()
